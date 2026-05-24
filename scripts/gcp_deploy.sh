#!/bin/bash
# =============================================================================
# GCP Deployment — Polybot Wallet Watchdog + PolyCop Auto-Copy
# e2-micro free tier (~$0/mois en us-central1/us-east1/us-west1)
#
# Usage (depuis ton PC local, une seule fois) :
#   chmod +x scripts/gcp_deploy.sh
#   ./scripts/gcp_deploy.sh
#
# Prérequis :
#   - gcloud CLI installé et authentifié (gcloud auth login)
#   - Un projet GCP actif (gcloud config set project TON_PROJECT_ID)
#   - Le repo pushé sur GitHub
# =============================================================================
set -euo pipefail

# ── Config ────────────────────────────────────────────────────────────────────
VM_NAME="polybot-vm"
ZONE="us-central1-a"
MACHINE_TYPE="e2-micro"
DISK_SIZE="20GB"
REPO_URL=""  # Set via --repo or env GCP_REPO_URL

# Parse args
while [[ $# -gt 0 ]]; do
  case $1 in
    --repo) REPO_URL="$2"; shift 2 ;;
    --vm)   VM_NAME="$2"; shift 2 ;;
    --zone) ZONE="$2"; shift 2 ;;
    *) echo "Unknown arg: $1"; exit 1 ;;
  esac
done

REPO_URL="${REPO_URL:-${GCP_REPO_URL:-}}"
if [[ -z "$REPO_URL" ]]; then
  echo "ERROR: provide --repo https://github.com/TON_COMPTE/polymarket-bot"
  exit 1
fi

echo "============================================================"
echo "  Polybot GCP Deploy"
echo "  VM   : $VM_NAME ($ZONE, $MACHINE_TYPE)"
echo "  Repo : $REPO_URL"
echo "============================================================"

# ── Step 1: Create VM ─────────────────────────────────────────────────────────
echo ""
echo "[1/5] Creating VM $VM_NAME..."
if gcloud compute instances describe "$VM_NAME" --zone="$ZONE" &>/dev/null; then
  echo "  VM already exists — skipping creation"
else
  gcloud compute instances create "$VM_NAME" \
    --machine-type="$MACHINE_TYPE" \
    --zone="$ZONE" \
    --image-family=debian-12 \
    --image-project=debian-cloud \
    --boot-disk-size="$DISK_SIZE" \
    --tags=polybot
  echo "  VM created. Waiting 20s for SSH to be ready..."
  sleep 20
fi

# ── Step 2: Remote setup ──────────────────────────────────────────────────────
echo ""
echo "[2/5] Running remote setup on $VM_NAME..."

gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="bash -s" << 'REMOTE_SETUP'
set -euo pipefail
echo "  Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-pip python3-venv git

echo "  Cloning repo..."
if [ -d "$HOME/polymarket-bot" ]; then
  cd "$HOME/polymarket-bot" && git pull
else
  git clone __REPO_URL__ "$HOME/polymarket-bot"
fi

echo "  Setting up Python venv..."
cd "$HOME/polymarket-bot"
python3 -m venv .venv
source .venv/bin/activate
pip install -q --upgrade pip
pip install -q -e ".[dashboard,automation]"

echo "  Creating tmp/ directory..."
mkdir -p tmp

echo "  Remote setup done."
REMOTE_SETUP

# Replace placeholder with actual repo URL
gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="
  cd \$HOME/polymarket-bot
  if [ ! -d .git ]; then
    git clone $REPO_URL .
  fi
"

# ── Step 3: Copy .env ─────────────────────────────────────────────────────────
echo ""
echo "[3/5] Uploading .env..."
if [ -f ".env" ]; then
  gcloud compute scp .env "$VM_NAME:~/polymarket-bot/.env" --zone="$ZONE"
  echo "  .env uploaded."
else
  echo "  WARNING: No local .env found."
  echo "  You'll need to create it manually on the VM:"
  echo "    gcloud compute ssh $VM_NAME --zone=$ZONE"
  echo "    cp ~/polymarket-bot/.env.example ~/polymarket-bot/.env && nano ~/polymarket-bot/.env"
fi

# ── Step 4: Create systemd services ──────────────────────────────────────────
echo ""
echo "[4/5] Installing systemd services..."

# Get the username on the remote VM
REMOTE_USER=$(gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="echo \$USER")

gcloud compute ssh "$VM_NAME" --zone="$ZONE" --command="bash -s" << SERVICES
set -euo pipefail
REMOTE_USER="$REMOTE_USER"
WORKDIR="/home/$REMOTE_USER/polymarket-bot"
VENV="/home/$REMOTE_USER/polymarket-bot/.venv/bin/python"

# Watchdog service
sudo tee /etc/systemd/system/polybot-watchdog.service > /dev/null << EOF
[Unit]
Description=Polybot Wallet Watchdog (SC-016 detection 24/7)
After=network.target

[Service]
Type=simple
User=$REMOTE_USER
WorkingDirectory=$WORKDIR
EnvironmentFile=$WORKDIR/.env
Environment=PYTHONPATH=$WORKDIR/src
ExecStart=$VENV scripts/run_wallet_watchdog.py
Restart=always
RestartSec=60
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# PolyCop auto-copy service
sudo tee /etc/systemd/system/polybot-polycop.service > /dev/null << EOF
[Unit]
Description=Polybot PolyCop Auto-Copy (Telethon)
After=network.target

[Service]
Type=simple
User=$REMOTE_USER
WorkingDirectory=$WORKDIR
EnvironmentFile=$WORKDIR/.env
Environment=PYTHONPATH=$WORKDIR/src
ExecStart=$VENV scripts/polycop_auto.py
Restart=always
RestartSec=30
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable polybot-watchdog polybot-polycop
echo "  Services installed and enabled."
SERVICES

# ── Step 5: Summary ───────────────────────────────────────────────────────────
echo ""
echo "[5/5] Deploy complete."
echo ""
echo "============================================================"
echo "  NEXT STEPS (run these on the VM via SSH)"
echo "============================================================"
echo ""
echo "  Connect to VM:"
echo "    gcloud compute ssh $VM_NAME --zone=$ZONE"
echo ""
echo "  1. Edit .env if needed:"
echo "       nano ~/polymarket-bot/.env"
echo ""
echo "  2. Telethon auth (interactive, one-time):"
echo "       cd ~/polymarket-bot"
echo "       PYTHONPATH=src .venv/bin/python scripts/polycop_auto.py --auth"
echo ""
echo "  3. Discover PolyCop Save button:"
echo "       PYTHONPATH=src .venv/bin/python scripts/polycop_auto.py --discover"
echo "       # → copy the Save button label into .env: POLYCOP_SAVE_BUTTON=..."
echo ""
echo "  4. Test one watchdog scan:"
echo "       PYTHONPATH=src .venv/bin/python scripts/run_wallet_watchdog.py --once"
echo ""
echo "  5. Start both services:"
echo "       sudo systemctl start polybot-watchdog polybot-polycop"
echo ""
echo "  6. Monitor logs:"
echo "       sudo journalctl -u polybot-watchdog -f"
echo "       sudo journalctl -u polybot-polycop -f"
echo ""
echo "  Mettre à jour le bankroll (ex: après un dépôt) :
    gcloud compute ssh $VM_NAME --zone=$ZONE --command=\
      "sed -i 's/POLYBOT_BANKROLL_USD=.*/POLYBOT_BANKROLL_USD=50/' ~/polymarket-bot/.env && sudo systemctl restart polybot-polycop"

  Update after git push:"
echo "    gcloud compute ssh $VM_NAME --zone=$ZONE --command="
echo "      'cd ~/polymarket-bot && git pull && sudo systemctl restart polybot-watchdog polybot-polycop'"
echo "============================================================"
