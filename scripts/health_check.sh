#!/usr/bin/env bash
# Health check — lance depuis la VM : bash scripts/health_check.sh

GREEN='\033[0;32m'; RED='\033[0;31m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✅ $1${NC}"; }
fail() { echo -e "${RED}❌ $1${NC}"; }
warn() { echo -e "${YELLOW}⚠️  $1${NC}"; }

ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  POLYBOT HEALTH CHECK — $(date -u '+%Y-%m-%d %H:%M UTC')"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Processus ───────────────────────────────────────────
echo ""
echo "[ PROCESSUS ]"

WD=$(pgrep -f "run_wallet_watchdog.py" | wc -l)
PC=$(pgrep -f "polycop_auto.py" | wc -l)

[ "$WD" -eq 1 ] && ok "Watchdog : 1 process" || fail "Watchdog : $WD process(us) (attendu: 1)"
[ "$PC" -eq 1 ] && ok "PolyCop auto : 1 process" || fail "PolyCop auto : $PC process(us) (attendu: 1)"

# ── 2. Services systemd ────────────────────────────────────
echo ""
echo "[ SERVICES SYSTEMD ]"

for svc in polybot-watchdog polybot-polycop; do
  state=$(systemctl is-active "$svc" 2>/dev/null)
  [ "$state" = "active" ] && ok "$svc : active" || fail "$svc : $state"
done

# ── 3. Session Telethon ────────────────────────────────────
echo ""
echo "[ SESSION TELETHON ]"

SESSION="$ROOT/tmp/polycop.session"
if [ -f "$SESSION" ]; then
  age_min=$(( ($(date +%s) - $(date -r "$SESSION" +%s)) / 60 ))
  ok "Session présente (modifiée il y a ${age_min}min)"
else
  fail "Session absente — relancer : python scripts/polycop_auto.py --auth"
fi

# ── 4. Dernière activité watchdog ──────────────────────────
echo ""
echo "[ DERNIÈRE ACTIVITÉ WATCHDOG ]"

LOG="$ROOT/tmp/watchdog.log"
if [ -f "$LOG" ]; then
  last_scan=$(grep "Scan complete" "$LOG" | tail -1)
  last_done=$(grep "Done —" "$LOG" | tail -1)
  next_scan=$(grep "Next scan in" "$LOG" | tail -1)
  [ -n "$last_scan" ] && ok "$last_scan" || warn "Aucun scan terminé encore"
  [ -n "$last_done" ] && echo "   $last_done"
  [ -n "$next_scan" ] && echo "   $next_scan"
else
  warn "Log watchdog absent (normal si premier démarrage)"
fi

# ── 5. Queue ───────────────────────────────────────────────
echo ""
echo "[ QUEUE AUTO-COPY ]"

QUEUE="$ROOT/tmp/polycop_queue.json"
if [ -f "$QUEUE" ]; then
  pending=$(python3 -c "import json; q=json.load(open('$QUEUE')); print(sum(1 for x in q if x.get('status')=='pending'))" 2>/dev/null)
  done=$(python3 -c "import json; q=json.load(open('$QUEUE')); print(sum(1 for x in q if x.get('status')=='done'))" 2>/dev/null)
  failed=$(python3 -c "import json; q=json.load(open('$QUEUE')); print(sum(1 for x in q if x.get('status')=='failed'))" 2>/dev/null)
  ok "Queue : ${pending:-0} en attente | ${done:-0} exécutés | ${failed:-0} échoués"
else
  ok "Queue vide (aucun wallet qualifié pour auto-copy encore)"
fi

# ── 6. Dernière erreur polycop ─────────────────────────────
echo ""
echo "[ DERNIÈRES ERREURS POLYCOP ]"

PC_LOG="$ROOT/tmp/polycop_auto.log"
if [ -f "$PC_LOG" ]; then
  errors=$(grep -i "error\|failed\|timeout" "$PC_LOG" | tail -5)
  if [ -n "$errors" ]; then
    warn "Dernières erreurs :"
    echo "$errors" | while read -r line; do echo "   $line"; done
  else
    ok "Aucune erreur récente"
  fi
else
  warn "Log polycop absent"
fi

# ── Résumé ─────────────────────────────────────────────────
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
total_ok=$(   grep -c "✅" <<< "$(bash "$0" 2>/dev/null)" 2>/dev/null || echo "?")
total_fail=$( grep -c "❌" <<< "$(bash "$0" 2>/dev/null)" 2>/dev/null || echo "?")
echo ""
