Dépose ici les threads Twitter en .txt — ils seront automatiquement traités au prochain scan du watchdog.

Format attendu : texte brut du thread copié-collé.
- Les adresses 0x sont extraites directement
- Les @mentions sont résolues via l'API Polymarket
- Les fichiers traités sont déplacés dans ../processed/

Tu peux aussi traiter manuellement :
    PYTHONPATH=src python scripts/ingest_threads.py
    PYTHONPATH=src python scripts/ingest_threads.py --dry-run
    PYTHONPATH=src python scripts/ingest_threads.py --stats
