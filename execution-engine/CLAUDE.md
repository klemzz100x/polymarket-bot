# Execution Engine

## Mission

Ce module gère :
- l’exécution des ordres,
- la connexion au CLOB,
- le routing,
- la gestion des ordres,
- la synchronisation état local / exchange.

## Priorités absolues

1. Robustesse
2. Déterminisme
3. Gestion du risque
4. Résilience réseau
5. Cohérence état local
6. Performance

## Règles strictes

- Aucun appel LLM dans le moteur live.
- Aucun traitement bloquant.
- Éviter allocations inutiles.
- Architecture event-driven obligatoire.
- Toute erreur critique doit être observable.
- Aucun secret hardcodé.
- Toutes les actions doivent être loggées.

## Architecture

Le moteur doit être :
- modulaire,
- stateless autant que possible,
- reconnectable,
- replayable.

## Logging

Logger :
- orders,
- fills,
- cancels,
- reconnects,
- latency,
- risk events,
- websocket events.

## Sécurité

Le risk engine doit toujours pouvoir :
- bloquer les ordres,
- réduire exposition,
- kill switch le système.