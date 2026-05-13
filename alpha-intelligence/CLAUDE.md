# Alpha Intelligence Layer

## Mission

Tu travailles sur le module `alpha-intelligence` du bot Polymarket.

L’objectif n’est pas de faire du copy trading naïf, mais de construire une couche quantitative capable d’identifier, classifier et analyser les portefeuilles Polymarket historiquement profitables afin d’extraire des patterns exploitables pour le bot HFT / arbitrage / market making.

Ce module doit servir à comprendre :

- quels wallets gagnent durablement,
- comment ils gagnent,
- sur quels types de marchés,
- avec quelle structure d’ordres,
- dans quels régimes de liquidité,
- avec quel profil de risque,
- et quels patterns peuvent être transformés en signaux ou stratégies.

## Principe central

Ne jamais considérer un wallet profitable comme une preuve d’edge.

Un wallet peut être profitable par chance, par prise de risque directionnelle excessive ou par exposition ponctuelle à un événement.

Le but est d’identifier des comportements reproductibles, mesurables et robustes.

Le module doit privilégier les wallets ayant :

- une profitabilité régulière,
- un drawdown maîtrisé,
- une forte activité,
- un volume significatif,
- une exposition directionnelle contrôlée,
- une forte proportion de trades passifs,
- une activité compatible avec du market making, de l’arbitrage ou de la capture de microstructure.

## Architecture cible

Le dossier `alpha-intelligence` doit être organisé ainsi :

```txt
alpha-intelligence/
  wallets/
    profitable_wallets.yaml
    tagged_wallets.yaml
    blacklist_wallets.yaml

  research/
    wallet_clustering.md
    maker_patterns.md
    arbitrage_patterns.md
    liquidity_rewards.md

  pipelines/
    wallet_scanner.ts
    pnl_tracker.ts
    flow_classifier.ts
    reward_detector.ts

  features/
    wallet_features.ts
    microstructure_features.ts

  datasets/
    wallet_snapshots/
    fills/
    orderbooks/

  models/
    wallet_scoring/