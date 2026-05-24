# SC-016 Wallet Confidence Scan — 2026-05-24 10:45 UTC

**Wallets scored:** 382
**Qualified (conf ≥ 60.0):** 2
**Green badges:** 0
**Black flags:** 3

## Methodology

Confidence is a weighted blend of 7 sub-scores computed from **on-chain trade history only**:

- **EDGE_PROOF (25%)** — Wilson lower bound 90% of mean per-trade ROI
- **SAMPLE_SUFFICIENCY (15%)** — Sigmoid penalty for <30 resolved trades
- **PERSISTENCE (15%)** — Split-half stability of ROI
- **ANTI_LUCK (15%)** — Inverse Gini of positive-PnL contributions (penalize jackpot wallets)
- **RISK_TAKEN (10%)** — Max drawdown + position concentration
- **COPYABILITY (10%)** — Median hold time (slow → copyable via PolyCop)
- **INDEPENDENCE (10%)** — v1 placeholder (cross-corr in v2)

Badge thresholds: 🟢 conf≥75 + n≥40 + persist≥50  |  🟡 partial  |  🔴 conf<50 or n<20  |  ⚫ insider pattern

## Ranked Wallets

| # | Badge | Label | Conf | EdgeType | Trd | Rsl | WinRate (LB) | ROI LB% | MedHold | Address |
|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 🟡 YELLOW | thread-extract-2 | 62.4 | category_specialist:weather | 300 | 495 | 72% (68%) | +4.8% | 2.4h | `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11` |
| 2 | 🟡 YELLOW | holder:RITB123 | 62.4 | category_specialist:crypto | 300 | 454 | 60% (56%) | +1.6% | 1.4h | `0x724db3c436dcc7b26fbe1ae0c0d6af538b588dea` |
| 3 | 🔴 RED | holder:aimforthebushe | 57.6 | longshot_fader | 32 | 0 | 0% (0%) | -0.3% | 587.2h | `0xbc26352dac6b2cc9274dae39f73269192caa15f9` |
| 4 | 🔴 RED | holder:freemuney | 55.1 | longshot_fader | 15 | 0 | 0% (0%) | -0.6% | 1007.8h | `0x1a162eb4dfb533d503dcc0fa09776f6e1b204335` |
| 5 | 🔴 RED | holder:Michel de Nost | 55.1 | category_specialist:crypto | 300 | 0 | 0% (0%) | +2.4% | 547.4h | `0x19de30c1bf1152db0b36d5d548d6c9f6f485713e` |
| 6 | 🟡 YELLOW | holder:Mike123455 | 54.5 | longshot_fader | 300 | 93 | 8% (4%) | -3.0% | 2032.3h | `0xeee9d0cedb2b8d59069d76d9f39bf58c383df66f` |
| 7 | 🔴 RED | holder:Count.Gusto | 53.7 | longshot_fader | 96 | 0 | 0% (0%) | -0.2% | 1009.8h | `0x866465ff16468c0a0bea259b75cfc575700edd88` |
| 8 | 🔴 RED | holder:Sangjoo | 53.7 | longshot_fader | 5 | 0 | 0% (0%) | -0.3% | 410.3h | `0xa6c9c7ccc03decaf4c1134a87a0bb4a937760f17` |
| 9 | 🔴 RED | holder:WorldFest | 53.4 | longshot_collector | 300 | 1 | 100% (27%) | +0.0% | 589.3h | `0xd568130f9f6498b04f985a157aed36d90ebbba70` |
| 10 | 🔴 RED | holder:PoloBoloYolo | 53.3 | category_specialist:weather | 300 | 0 | 0% (0%) | -0.1% | 27.8h | `0x1ef09f92e5217e1b757b37ace873f915cb76e2d1` |
| 11 | 🔴 RED | holder:sheepthecards | 52.5 | longshot_fader | 300 | 1 | 0% (0%) | -2.3% | 1348.5h | `0x6cfcf9047deec0d169005df2fcd1bfededfa661e` |
| 12 | 🔴 RED | holder:roushie | 52.2 | longshot_fader | 300 | 0 | 0% (0%) | -0.2% | 927.5h | `0x5357cf7202881f02ac8dcd9e19dc27456e8f3a0d` |
| 13 | 🔴 RED | holder:P-J | 52.1 | general_trader | 300 | 1 | 0% (0%) | -0.0% | 1160.4h | `0xd498f2d1ae092dfc39088343f6d4e9219c7780ae` |
| 14 | 🔴 RED | holder:scapri | 52.0 | longshot_fader | 294 | 0 | 0% (0%) | -0.3% | 2300.1h | `0x9e25f9cd6d4fd6996135e68ff55acb28bca657c7` |
| 15 | 🟡 YELLOW | holder:DickTurbin | 52.0 | longshot_fader | 300 | 462 | 29% (25%) | -1.0% | 69.2h | `0xb6bed94e75c333dae24eb9c80b3fef47ef3cfcfe` |
| 16 | 🟡 YELLOW | holder:MRF | 51.6 | longshot_fader | 300 | 410 | 15% (12%) | -12.4% | 60.2h | `0x16cbe223607a6513ae76d1e3751c78e4eabc2704` |
| 17 | 🔴 RED | holder:hongmyungbo | 51.5 | longshot_fader | 7 | 0 | 0% (0%) | -0.3% | 347.0h | `0x5dceeeec594b80f465d1be87712a0d6b6885ecd7` |
| 18 | 🔴 RED | holder:lecroissant | 51.4 | longshot_fader | 300 | 0 | 0% (0%) | -0.8% | 276.6h | `0x1f7ffa3efbbe5d075d7c3eefe98dce9d8f05f514` |
| 19 | 🟡 YELLOW | holder:iDARKenjoyer | 51.4 | general_trader | 300 | 49 | 65% (54%) | -0.3% | 8.8h | `0xf68a281980f8c13828e84e147e3822381d6e5b1b` |
| 20 | 🟡 YELLOW | holder:DavidShekel | 51.4 | longshot_fader | 300 | 416 | 20% (16%) | -0.1% | 12.9h | `0x54525ee78bd513b0bf75f94e560158f6fc35d448` |
| 21 | 🔴 RED | holder:khalikof | 51.3 | longshot_fader | 300 | 0 | 0% (0%) | -0.3% | 671.2h | `0x3c32adc2fca14ae5afc36081f16262bc516d15bf` |
| 22 | 🔴 RED | holder:Romkos7 | 50.9 | general_trader | 300 | 1 | 100% (27%) | -0.0% | 153.2h | `0xa39c488ea8269609aea27f5f8486044d839908bc` |
| 23 | 🟡 YELLOW | holder:rainbowlilies | 50.8 | longshot_fader | 300 | 133 | 15% (11%) | -1.0% | 6.5h | `0x21064fd320bfd5a86f8c92a94d3209edf4154dea` |
| 24 | 🔴 RED | holder:c0O0OLI0O03 | 50.6 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 2.6h | `0xfedc381bf3fb5d20433bb4a0216b15dbbc5c6398` |
| 25 | 🟡 YELLOW | holder:petanimal | 50.6 | longshot_fader | 300 | 106 | 10% (6%) | -2.8% | 19.1h | `0xfd691577dc6a9d21e9611b93ef9177d36738a2e1` |
| 26 | 🟡 YELLOW | holder:cigarettes | 50.4 | longshot_fader | 300 | 205 | 33% (28%) | +1.4% | 0.4h | `0xd218e474776403a330142299f7796e8ba32eb5c9` |
| 27 | 🔴 RED | holder:asjabaasj | 50.3 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 1.1h | `0xa7a8c1fd4bfff08ea30214efa7efaf75d7c6580c` |
| 28 | 🔴 RED | holder:aff3 | 50.2 | longshot_fader | 300 | 0 | 0% (0%) | +0.1% | 90.8h | `0xe52c0a1327a12edc7bd54ea6f37ce00a4ca96924` |
| 29 | 🔴 RED | holder:PMTraderAdam | 50.2 | general_trader | 300 | 4 | 75% (36%) | -0.1% | 90.9h | `0x154794795d978c5890b3f69264311f0bd966d066` |
| 30 | 🟡 YELLOW | holder:FreeCityIndivi | 50.2 | longshot_collector | 300 | 359 | 52% (48%) | -1.2% | 97.9h | `0x098eddabb2d388f31e79aaf525e49588f22a6fa2` |
| 31 | 🟡 YELLOW | holder:Poivre | 50.1 | longshot_fader | 300 | 21 | 24% (12%) | +3.5% | 360.6h | `0x714f682e577a6892ee921290fd6ad213d11266d5` |
| 32 | 🔴 RED | holder:0x05e17Fb524aa | 49.6 | category_specialist:sports | 300 | 172 | 0% (0%) | -45.0% | 246.8h | `0x05e17fb524aa6896de92dec88db2f0e4dd5285a2` |
| 33 | 🔴 RED | holder:juanporco | 49.3 | longshot_collector | 300 | 2 | 100% (42%) | -2.5% | 1585.2h | `0xce845c6892bcc6d256ab419e7803e5ff2e969e2b` |
| 34 | 🔴 RED | holder:TomTurbo | 49.3 | longshot_fader | 300 | 2 | 0% (0%) | -1.1% | 139.2h | `0x9186257f5881a068874a329efeabd542085a9220` |
| 35 | 🔴 RED | holder:mombil | 49.2 | general_trader | 300 | 30 | 57% (42%) | +2.9% | 14.6h | `0x68c24bf4a8ad4d79a6fe4b8eec6f93a02dfd1711` |
| 36 | 🔴 RED | holder:KamAlla | 48.9 | longshot_fader | 300 | 0 | 0% (0%) | -0.1% | 176.5h | `0x362ea6c4dbafffe5df6a3cc6f8f4029547238983` |
| 37 | 🔴 RED | ImJustKen | 48.7 | longshot_fader | 300 | 304 | 17% (14%) | -3.9% | 219.1h | `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` |
| 38 | 🔴 RED | holder:io-cane | 48.7 | longshot_fader | 300 | 0 | 0% (0%) | -0.0% | 44.6h | `0xf16640ce7cb59d7b38ca397652a5d296c6d0fb37` |
| 39 | 🔴 RED | holder:Dernrt | 48.7 | longshot_fader | 92 | 0 | 0% (0%) | -0.2% | 1114.2h | `0xd5e64977e3e6e800e60f10a2821abac395821f0e` |
| 40 | 🔴 RED | holder:0xA712F13C08AD | 48.7 | longshot_fader | 10 | 0 | 0% (0%) | -0.3% | 2221.3h | `0xa712f13c08ada1fabd654b477292c55069147f18` |
| 41 | 🔴 RED | holder:0xb1b30231 | 48.6 | longshot_collector | 300 | 3 | 100% (53%) | -0.5% | 248.0h | `0xb1b3023167b5ced7538225e98e19da557616a386` |
| 42 | 🔴 RED | holder:0x10cE6837F579 | 48.6 | longshot_fader | 18 | 0 | 0% (0%) | -0.3% | 175.8h | `0x10ce6837f5798eda77a5a17979dc540b7f24fe1f` |
| 43 | 🔴 RED | holder:Stalker4 | 48.6 | longshot_fader | 273 | 0 | 0% (0%) | -0.3% | 264.5h | `0x3078921ae15f218a40660ecbecce8d7eac27ad0a` |
| 44 | 🔴 RED | holder:ug88923 | 48.5 | longshot_fader | 45 | 0 | 0% (0%) | -0.3% | 264.2h | `0x4ae7d4b245aa765793d1d06c42ea5cbcc46a68d2` |
| 45 | 🔴 RED | holder:Iruk4ndji | 48.5 | longshot_fader | 3 | 0 | 0% (0%) | -0.1% | 386.7h | `0x78325269e6ac6e96c84d97f3b8e802d22b10b98b` |
| 46 | 🔴 RED | holder:Basic123 | 48.4 | longshot_fader | 218 | 0 | 0% (0%) | -0.1% | 792.3h | `0x21ff4c3391d81c10a21eb6fe74ab262a5aae3b60` |
| 47 | 🔴 RED | holder:nvvn | 48.3 | longshot_fader | 300 | 2 | 0% (0%) | -2.1% | 15.1h | `0xd355b7dc3d83658eeb6701dc88ec80522278f69c` |
| 48 | 🔴 RED | holder:Turtle892 | 48.3 | longshot_fader | 300 | 44 | 0% (0%) | -7.4% | 380.9h | `0xe574b4bf69386301fa2759bc4c39c0fc6f83832a` |
| 49 | 🔴 RED | holder:0xcdlambjrrt0l | 48.3 | category_specialist:politics | 300 | 0 | 0% (0%) | -1.7% | 68.2h | `0x52c2143f69dd3dcd249f688623c64ab5f7900556` |
| 50 | 🔴 RED | holder:0xaf610A793ec2 | 48.2 | general_trader | 244 | 52 | 0% (0%) | -30.5% | 863.0h | `0xaf610a793ec2d68e929f8073ac4ea51a7ca64d44` |
| 51 | 🔴 RED | lb-profit-1d:anoin123 | 48.1 | longshot_fader | 300 | 141 | 14% (9%) | -7.9% | 9.1h | `0x96489abcb9f583d6835c8ef95ffc923d05a86825` |
| 52 | 🔴 RED | holder:awaiting-lifec | 48.1 | favorite_collector | 300 | 0 | 0% (0%) | -0.9% | 151.0h | `0x4d32e23ab079511ab2de13d58211a99b23d39dfc` |
| 53 | 🔴 RED | holder:yiyezhiqiu110 | 48.0 | longshot_fader | 3 | 0 | 0% (0%) | -0.1% | 19.4h | `0x267eee7e20027ea3e3ce5386998929d17ee5f2e8` |
| 54 | 🔴 RED | holder:jpmpower | 48.0 | longshot_fader | 300 | 0 | 0% (0%) | -0.1% | 260.5h | `0x31aea02baa8907646bc69e3787807b8898a44b60` |
| 55 | 🔴 RED | holder:0x740159EcEd2A | 47.9 | longshot_fader | 40 | 0 | 0% (0%) | -0.4% | 139.4h | `0x740159eced2aaf9edcb7fac8a0b31d18c0f847a5` |
| 56 | 🔴 RED | holder:Pol.1 | 47.9 | category_specialist:politics | 300 | 0 | 0% (0%) | -0.1% | 27.4h | `0xd3a72382f2c459af33a839866b3f2852e4723362` |
| 57 | 🔴 RED | holder:Xyu | 47.8 | general_trader | 300 | 0 | 0% (0%) | -1.4% | 213.1h | `0xba3ce1a0a3cd1ab1f98981f3ce7350017de22e4e` |
| 58 | 🔴 RED | holder:0xa2dCcd83971D | 47.7 | longshot_fader | 300 | 0 | 0% (0%) | -0.6% | 433.3h | `0xa2dccd83971d56fb4e7ce45c491a968b29a249f9` |
| 59 | 🔴 RED | holder:0x72bbEF3D5247 | 47.7 | category_specialist:crypto | 300 | 341 | 1% (0%) | -13.4% | 30.0h | `0x72bbef3d52476fdb7cf041bbeaabed927e83281b` |
| 60 | 🔴 RED | holder:lovedudley | 47.5 | longshot_fader | 300 | 2 | 0% (0%) | -0.8% | 6.7h | `0xfe9455e2cad5257b26547af62cbbfd75c8968a3d` |
| 61 | 🔴 RED | holder:0xf3C4ee5Eb5b1 | 47.5 | general_trader | 300 | 447 | 6% (5%) | -26.2% | 275.3h | `0xf3c4ee5eb5b1e1cd70f697cc1f18db7e94b40216` |
| 62 | 🔴 RED | lb-profit-1d:surfandturf | 47.4 | category_specialist:sports | 300 | 1 | 100% (27%) | +0.0% | 4.1h | `0x9f2fe025f84839ca81dd8e0338892605702d2ca8` |
| 63 | 🔴 RED | holder:Kolba | 47.4 | longshot_fader | 24 | 0 | 0% (0%) | -1.2% | 3808.2h | `0xb805a4ff8a382798c5fa5d717290df41927251fb` |
| 64 | 🔴 RED | holder:Nicksypoo | 47.4 | general_trader | 300 | 347 | 0% (0%) | -50.8% | 8.2h | `0xcbb5623096b78505a26524e642c5c9066e585ed9` |
| 65 | 🔴 RED | holder:PrimePenguin | 47.4 | longshot_fader | 300 | 458 | 6% (4%) | -13.2% | 71.4h | `0x933ca00f565ba7130180e58fce4f965cc33ba8c6` |
| 66 | 🔴 RED | holder:SunlineTicker | 47.0 | category_specialist:sports | 300 | 494 | 1% (1%) | -42.2% | 2.9h | `0x4df332e27f9ee3224f52ce30e3ce15c1075e788f` |
| 67 | 🔴 RED | holder:0x372999C3F35f | 46.9 | general_trader | 62 | 5 | 0% (0%) | -28.7% | 374.9h | `0x372999c3f35fc853143a1c967a193f12e0dd37b3` |
| 68 | 🔴 RED | holder:naiiiiii | 46.8 | longshot_fader | 300 | 138 | 4% (2%) | -3.4% | 2.9h | `0x70d94a4ff67ed919a8480885cf0808afefe7a684` |
| 69 | 🔴 RED | holder:0xwhaleshark | 46.8 | longshot_fader | 300 | 4 | 0% (0%) | +0.0% | 12.3h | `0x2179ab15324f5436f1a83c8092b8cc3dad79bedb` |
| 70 | 🔴 RED | holder:peter239784 | 46.8 | longshot_fader | 300 | 74 | 10% (5%) | -15.3% | 80.4h | `0x7d58986f00b3c00e9b24d02f8e35381ca154cfcc` |
| 71 | 🔴 RED | holder:billsmurfiks | 46.7 | favorite_collector | 17 | 0 | 0% (0%) | -0.2% | 21.7h | `0x52d316df580ee729b88aa9e41416550680a13509` |
| 72 | 🔴 RED | holder:Q96s3kwozynxpa | 46.6 | category_specialist:politics | 300 | 2 | 0% (0%) | +0.3% | 3.3h | `0x2663daca3cecf3767ca1c3b126002a8578a8ed1f` |
| 73 | 🔴 RED | holder:junipero | 46.6 | longshot_fader | 300 | 0 | 0% (0%) | -1.7% | 111.6h | `0x79797067582d11012e70acfc5a2e8b332580202f` |
| 74 | 🔴 RED | holder:Hazardrip | 46.6 | general_trader | 300 | 76 | 3% (1%) | -17.3% | 406.6h | `0x32b61f77818ee062a1cf0ad4312752879e1a2f9f` |
| 75 | 🔴 RED | holder:keasiyo | 46.5 | general_trader | 300 | 64 | 2% (0%) | -26.7% | 620.0h | `0xee67f4f549180f564dd5910b1024b8c6729cef38` |
| 76 | 🔴 RED | holder:Ronaldo2100 | 46.5 | longshot_fader | 300 | 163 | 1% (0%) | -21.5% | 429.9h | `0x71ca04d689bc38c5e4dcda8a4d743f279c5a3501` |
| 77 | 🔴 RED | holder:cryptoincome | 46.5 | favorite_collector | 300 | 5 | 100% (65%) | -1.7% | 436.6h | `0xe60f07a844bd18448eb3b23818f94bec1589f4b4` |
| 78 | 🔴 RED | holder:chikipikinss | 46.5 | favorite_collector | 9 | 3 | 100% (53%) | -0.6% | 19.3h | `0xea81727c212edf992eaae489f9f1c84b20e51171` |
| 79 | 🔴 RED | holder:0xc4eaee3c | 46.5 | general_trader | 202 | 0 | 0% (0%) | -18.2% | 190.9h | `0xc4eaee3cdd1e20a75209250dc8c67a6d180262c5` |
| 80 | 🔴 RED | holder:0xb11ebd1CdD2b | 46.5 | favorite_collector | 102 | 0 | 0% (0%) | -0.1% | 43.0h | `0xb11ebd1cdd2b8091f3e154272f0655b3c8151352` |
| 81 | 🔴 RED | thread-extract-1 | 46.4 | longshot_fader | 300 | 42 | 0% (0%) | -26.4% | 6.0h | `0x8c80d213c0cbad777d06ee3f58f6ca4bc03102c3` |
| 82 | 🔴 RED | holder:BabyGroot | 46.4 | longshot_collector | 300 | 34 | 59% (45%) | -0.2% | 3.4h | `0xbefa95c276ee8ef6ff3ef43d1c1c454f52bc300d` |
| 83 | 🔴 RED | holder:BeN | 46.4 | longshot_fader | 300 | 321 | 8% (6%) | -8.2% | 435.6h | `0x668d85d791049bf0100e557a72c7ed4dc97297d2` |
| 84 | 🔴 RED | lb-volume-7d:0xd8dA6BF26964 | 46.3 | general_trader | 300 | 37 | 32% (21%) | -0.7% | 0.7h | `0x8a98109fb0f1d87d9bfcb4486ba3587b95c51b92` |
| 85 | 🔴 RED | holder:0x0f03ee04 | 46.3 | longshot_fader | 251 | 0 | 0% (0%) | -0.2% | 407.3h | `0x0f03ee04e63f003fd9d4dcce1690f9276f2b38d7` |
| 86 | 🔴 RED | holder:Nk9 | 46.2 | longshot_fader | 300 | 2 | 0% (0%) | -1.0% | 357.4h | `0x410338a0360417802c93d2e8f1c490f0fcc5a4e7` |
| 87 | 🔴 RED | holder:0x3069d3c1cf86 | 46.1 | general_trader | 300 | 2 | 0% (0%) | -11.9% | 117.2h | `0x3069d3c1cf8663728fd3deb63e9592977c5f83cd` |
| 88 | 🔴 RED | Poligarch | 45.9 | category_specialist:weather | 300 | 366 | 56% (51%) | +1.2% | 0.8h | `0xb40e89677d59665d5188541ad860450a6e2a7cc9` |
| 89 | 🔴 RED | holder:DapperChapper | 45.9 | longshot_fader | 300 | 2 | 0% (0%) | -0.3% | 11.9h | `0xf8ccb567e89c3240359217ebd0b5b5fe7fce5a82` |
| 90 | 🔴 RED | holder:John3501 | 45.9 | longshot_fader | 300 | 91 | 1% (0%) | -5.4% | 320.6h | `0x08628ebc448f97450825e14ed3a79f45e5a6c7aa` |
| 91 | 🔴 RED | holder:Ecofarmer | 45.9 | general_trader | 300 | 0 | 0% (0%) | -4.0% | 49.7h | `0xfaa55858f098040003978c3615a086cdd0cd7cc9` |
| 92 | 🔴 RED | holder:fwed33 | 45.8 | general_trader | 300 | 451 | 0% (0%) | -34.0% | 9.4h | `0x14619de097b1fbe058d6d36282662c20958a30a1` |
| 93 | 🔴 RED | holder:ddalkkak | 45.8 | longshot_fader | 300 | 94 | 2% (1%) | -11.2% | 724.1h | `0x16bd7cc71f6da1e77d1d8255677abc75b9bae288` |
| 94 | 🔴 RED | holder:elPolloLoco | 45.7 | longshot_fader | 300 | 485 | 7% (6%) | -17.1% | 190.0h | `0xa2f1fecf1cc7db65a46588f764b6691533052d22` |
| 95 | 🔴 RED | holder:Martiini | 45.7 | category_specialist:crypto | 300 | 343 | 43% (39%) | -7.4% | 3357.5h | `0x3b6fd06a595d71c70afb3f44414be1c11304340b` |
| 96 | 🔴 RED | holder:TimeTraveler | 45.5 | longshot_fader | 300 | 433 | 18% (15%) | -2.3% | 23.1h | `0x51fd8f0358cc9e8a1ee5f87a0c7e3b07ed634272` |
| 97 | 🔴 RED | holder:LiquidatedDege | 45.5 | general_trader | 300 | 465 | 0% (0%) | -27.8% | 85.8h | `0xc7e53ac4a7c76d6df8b794de2e7d0794265d2d3a` |
| 98 | 🔴 RED | holder:0x0DBDfBB4A708 | 45.3 | longshot_fader | 300 | 0 | 0% (0%) | -0.2% | 51.7h | `0x0dbdfbb4a708a51dc0c7c3b4a51ce702d41f2caa` |
| 99 | 🔴 RED | holder:0x57F4274b4E37 | 45.2 | category_specialist:ai_tech | 5 | 0 | 0% (0%) | -1.6% | 66.1h | `0x57f4274b4e3799d1872898398ea61d457f94fce5` |
| 100 | 🔴 RED | btc-bot-A | 45.1 | category_specialist:crypto | 300 | 0 | 0% (0%) | -1.9% | 33.8h | `0xf705fa045201391d9632b7f3cde06a5e24453ca7` |
| 101 | 🔴 RED | holder:SamuraiBlue | 45.1 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 1757.6h | `0xf2916e7366f2caf579b12bc6e3e7d145d0ad2cf2` |
| 102 | 🔴 RED | holder:Rrrrffff | 45.1 | longshot_fader | 1 | 0 | 0% (0%) | +0.0% | 972.3h | `0x81ef8cb9f75921beda5a0a6cd3c5c508ac6347f7` |
| 103 | 🔴 RED | holder:meta.xing | 45.1 | category_specialist:ai_tech | 9 | 0 | 0% (0%) | +0.0% | 1391.4h | `0x56e0b7bb3ca3a41399078420b5d81c711a6912ac` |
| 104 | 🔴 RED | holder:uponlyvibes | 45.1 | category_specialist:sports | 9 | 0 | 0% (0%) | +0.0% | 2449.3h | `0x99abd14fb1b179b1c5647a5762156b7ceeb77bd2` |
| 105 | 🔴 RED | holder:DeFiMonky | 45.0 | longshot_fader | 22 | 0 | 0% (0%) | -0.1% | 905.7h | `0x03431e72f2c3de8a1fb35eeb4c82624e08e1f2dc` |
| 106 | 🔴 RED | holder:Tw1n999 | 45.0 | longshot_fader | 300 | 199 | 10% (7%) | -4.7% | 10.8h | `0xcbba64cddd05171925ffd05d8f8abd38c83fdbff` |
| 107 | 🔴 RED | holder:StudyPredictio | 45.0 | general_trader | 300 | 115 | 6% (3%) | -14.1% | 9.5h | `0x33bcb6e9bd44be709122b2940c55e34f1a7e37dc` |
| 108 | 🔴 RED | holder:Blaskinho | 44.9 | longshot_fader | 300 | 0 | 0% (0%) | -3.3% | 15.9h | `0xd458d05a966ca3e6f6acdbf2a87c3e03f71bb521` |
| 109 | 🔴 RED | holder:0x879d999541ea | 44.9 | category_specialist:weather | 300 | 92 | 0% (0%) | -13.3% | 4.5h | `0x879d999541ea4b50b7c237092cfc2b5f8a1fb501` |
| 110 | 🔴 RED | holder:Maanimo | 44.9 | category_specialist:sports | 300 | 442 | 0% (0%) | -46.7% | 10.5h | `0xe962dfbaed113be79c38e122e67a431231a9663a` |
| 111 | 🔴 RED | holder:kardamonchik88 | 44.9 | favorite_collector | 21 | 0 | 0% (0%) | -0.1% | 95.8h | `0x3d0b07845badccb0c8956e69c9a12994d8a6550e` |
| 112 | 🔴 RED | holder:redvinny | 44.8 | general_trader | 300 | 238 | 0% (0%) | -69.0% | 2.0h | `0x56c9fbdeccf198f1f5ad95ace39b24f5f7fb0d9e` |
| 113 | 🔴 RED | holder:0x859D08C50098 | 44.8 | general_trader | 300 | 385 | 0% (0%) | -39.7% | 157.8h | `0x859d08c500981d447a1168f510fd5df9c0663cec` |
| 114 | 🔴 RED | lb-profit-30d:0x2a2C53bD278c | 44.7 | general_trader | 300 | 454 | 7% (6%) | -28.3% | 83.1h | `0x2a2c53bd278c04da9962fcf96490e17f3dfb9bc1` |
| 115 | 🔴 RED | holder:0x8EDEC839A0B2 | 44.7 | longshot_fader | 1 | 0 | 0% (0%) | -0.2% | 1183.9h | `0x8edec839a0b2848bd651d74c9cde13604c615ab8` |
| 116 | 🔴 RED | holder:huzpdpgpas | 44.7 | favorite_collector | 257 | 0 | 0% (0%) | -0.1% | 53.9h | `0xf3f7a7ea7d1cd7b8a2d1be66123efe2473dfecb3` |
| 117 | 🔴 RED | 0xheavy888 | 44.6 | general_trader | 300 | 103 | 18% (12%) | -17.2% | 0.5h | `0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd` |
| 118 | 🔴 RED | holder:wodnsdl | 44.6 | longshot_fader | 48 | 0 | 0% (0%) | -0.3% | 386.7h | `0x2a1a96973257559ec00ed7374e20c427dfefc549` |
| 119 | 🔴 RED | holder:touzhu | 44.6 | longshot_fader | 262 | 0 | 0% (0%) | -0.4% | 2448.4h | `0x2afc9bcbbfce9470181ee7a3dfc1f68dbd1eecd9` |
| 120 | 🔴 RED | holder:DenzelZW | 44.6 | longshot_fader | 2 | 0 | 0% (0%) | -0.1% | 36.5h | `0x694680bbf6a881a836705098a87045169fa713da` |
| 121 | 🔴 RED | holder:Thethiagoshow | 44.6 | general_trader | 300 | 42 | 5% (2%) | -41.1% | 22.8h | `0x319fae12252753985892dd2b949ad124eb77500b` |
| 122 | 🔴 RED | holder:melchior1248 | 44.6 | longshot_fader | 300 | 249 | 16% (12%) | -1.4% | 0.6h | `0x36901eb0f21519cc9055662a6d2483e96da1e16f` |
| 123 | 🔴 RED | holder:stormwww | 44.5 | longshot_fader | 3 | 0 | 0% (0%) | -0.5% | 1140.9h | `0xed2b092ba85a2f182584348932c53b33e9a22bb9` |
| 124 | 🔴 RED | holder:1Q84 | 44.5 | longshot_fader | 300 | 5 | 0% (0%) | -9.1% | 362.7h | `0x4c677b8da16c8308fbc15f6191a5369faee71075` |
| 125 | 🔴 RED | lb-profit-1d:Countryside | 44.4 | category_specialist:sports | 300 | 459 | 0% (0%) | -37.5% | 1.4h | `0xbddf61af533ff524d27154e589d2d7a81510c684` |
| 126 | 🔴 RED | holder:ballena | 44.4 | general_trader | 300 | 0 | 0% (0%) | -14.6% | 1765.4h | `0xcfc51c0a1a5a78845127d9d9dcb1236f700dc7cf` |
| 127 | 🔴 RED | lb-profit-7d:swisstony | 44.3 | hft_uncopyable | 300 | 306 | 73% (68%) | -0.0% | 0.2h | `0x204f72f35326db932158cba6adff0b9a1da95e14` |
| 128 | 🔴 RED | lb-profit-30d:Pestle | 44.3 | longshot_fader | 300 | 22 | 0% (0%) | -0.8% | 213.4h | `0x241f846866c2de4fb67cdb0ca6b963d85e56ef50` |
| 129 | 🔴 RED | holder:Gucky-Gu45 | 44.3 | longshot_fader | 300 | 262 | 14% (11%) | -1.5% | 4.0h | `0xe613b515bd46b1585a8b137a4d291d9b80bd540e` |
| 130 | 🔴 RED | holder:helloeveryone | 44.3 | general_trader | 300 | 17 | 41% (24%) | -4.2% | 28.7h | `0xc9e3208526a3554342652c26bec1ba2c230993f2` |
| 131 | 🔴 RED | lb-profit-7d:0x2c335066FE58 | 44.2 | midprice_market_maker | 300 | 187 | 5% (3%) | -40.2% | 4.8h | `0x2c335066fe58fe9237c3d3dc7b275c2a034a0563` |
| 132 | 🔴 RED | holder:omoi0i0 | 44.2 | category_specialist:sports | 300 | 484 | 2% (1%) | -25.9% | 45.5h | `0xb3cfe7615d64db8dfa743a1b1a2b976911460ebd` |
| 133 | 🔴 RED | holder:TheReturnOfDar | 44.2 | general_trader | 300 | 104 | 9% (5%) | -16.9% | 38.4h | `0x3a8aa345d5db7ec5138298c8c4f4540259be7699` |
| 134 | 🔴 RED | holder:achoque | 44.1 | favorite_collector | 34 | 0 | 0% (0%) | -0.7% | 192.2h | `0x76c5f743e91a93a50b139783abaecca3d8452cda` |
| 135 | 🔴 RED | holder:Etanol | 44.0 | longshot_fader | 300 | 0 | 0% (0%) | -2.8% | 160.2h | `0xd399ba186f89721f79e0a72bfa6c9babd2e13f46` |
| 136 | 🔴 RED | holder:0xcaEad14f3588 | 44.0 | longshot_fader | 69 | 0 | 0% (0%) | -0.8% | 1053.7h | `0xcaead14f35888c5abfa093b62810af66a3e792cb` |
| 137 | 🔴 RED | holder:Joe-Biden | 44.0 | longshot_fader | 300 | 58 | 0% (0%) | -28.4% | 124.5h | `0x8b5a7da2fdf239b51b9c68a2a1a35bb156d200f2` |
| 138 | 🔴 RED | holder:keepbelieving | 44.0 | longshot_fader | 20 | 1 | 0% (0%) | -33.1% | 497.8h | `0x0221e2d951c807a84c49fea10b5435466514ae79` |
| 139 | 🔴 RED | holder:SweetChariot | 43.8 | favorite_collector | 300 | 3 | 100% (53%) | -2.8% | 60.8h | `0x562bc8068347268d9a69b8dd464d00eed0f9dc09` |
| 140 | 🔴 RED | holder:lyprop | 43.7 | longshot_fader | 300 | 3 | 0% (0%) | -16.7% | 428.6h | `0xdf920cc41d76c0d3f24e5778e53624dd1b426fa0` |
| 141 | 🔴 RED | holder:Thomas-Anderso | 43.6 | longshot_fader | 25 | 0 | 0% (0%) | -2.1% | 867.3h | `0x36bd0412539892373be60df52c3ffa56f6183263` |
| 142 | 🔴 RED | holder:cowcat | 43.6 | longshot_fader | 300 | 383 | 18% (14%) | -9.5% | 33.8h | `0x38e59b36aae31b164200d0cad7c3fe5e0ee795e7` |
| 143 | 🔴 RED | holder:SammySledge | 43.6 | category_specialist:sports | 300 | 372 | 0% (0%) | -44.0% | 7.6h | `0xafbacaeeda63f31202759eff7f8126e49adfe61b` |
| 144 | 🔴 RED | holder:0x115A63c20827 | 43.5 | longshot_collector | 300 | 1 | 100% (27%) | -1.6% | 406.8h | `0x115a63c208278a576150176880f48f064c94e4a6` |
| 145 | 🔴 RED | holder:foodenjoyer | 43.5 | general_trader | 300 | 4 | 0% (0%) | -3.3% | 183.1h | `0x7b02b2bac2a30ed5e40b7094e734f4c3dc2a4991` |
| 146 | 🔴 RED | holder:gloriafoster | 43.4 | category_specialist:sports | 300 | 186 | 2% (1%) | -23.4% | 0.8h | `0x5d189e816b4149be00977c1a3c8840374aec4972` |
| 147 | 🔴 RED | holder:rivermarkets | 43.4 | longshot_fader | 300 | 191 | 8% (5%) | -14.6% | 151.4h | `0x1223987eb4bf8564a932f43e3cec9f28b5ced424` |
| 148 | 🔴 RED | holder:elkmonkey | 43.2 | category_specialist:sports | 300 | 0 | 0% (0%) | +0.6% | 624.7h | `0xead152b855effa6b5b5837f53b24c0756830c76a` |
| 149 | 🔴 RED | holder:knmrobert | 43.2 | category_specialist:weather | 300 | 50 | 0% (0%) | -14.4% | 7.3h | `0x7c1c3a3e97c81f9235fc24c2811c7218ff5a0b5f` |
| 150 | 🔴 RED | holder:KoloMuani | 43.2 | general_trader | 300 | 0 | 0% (0%) | -4.7% | 182.1h | `0xd396dd666a021f1d62121a407c7449ee7e084991` |
| 151 | 🔴 RED | holder:Belgaron | 43.0 | favorite_collector | 300 | 12 | 75% (51%) | -0.5% | 153.4h | `0x6c104a31c105ab2573a42e0f178f961e4496df5c` |
| 152 | 🔴 RED | holder:0xc6174a742B29 | 42.9 | general_trader | 300 | 0 | 0% (0%) | -2.3% | 1430.0h | `0xc6174a742b2926f00e683828019cef708ff9cd8e` |
| 153 | 🔴 RED | holder:carmenqueasy | 42.9 | longshot_fader | 300 | 2 | 0% (0%) | -11.9% | 862.8h | `0x932051bfc39f59e72340634a430049982df7f7d7` |
| 154 | 🔴 RED | holder:musicmang | 42.9 | general_trader | 57 | 3 | 0% (0%) | -22.4% | 1906.0h | `0xdd9cb05e6709a57441ad04e59cd1e88690062a50` |
| 155 | 🔴 RED | holder:jingxingyhh | 42.8 | general_trader | 300 | 0 | 0% (0%) | -4.9% | 784.0h | `0x1bbed6ce05e6c1eba4ae94a223a47ab591bf776d` |
| 156 | 🔴 RED | holder:polyproguy | 42.8 | general_trader | 300 | 89 | 3% (1%) | -47.2% | 83.3h | `0xdcc9d68a4bad9fc8becd27a03ee5b2b4feda4534` |
| 157 | 🔴 RED | holder:xiaohui998 | 42.8 | midprice_market_maker | 300 | 318 | 2% (1%) | -47.6% | 5.3h | `0x72361923300983fc1ba06dc5798e1082917aea53` |
| 158 | 🔴 RED | lb-volume-7d:Dafu0715 | 42.7 | favorite_collector | 300 | 0 | 0% (0%) | -5.3% | 32.1h | `0x93511d72d294f1478739bc38f578bf0306fd9e4d` |
| 159 | 🔴 RED | holder:majorL | 42.6 | longshot_fader | 300 | 155 | 1% (0%) | -19.5% | 245.2h | `0xd5386df17edb2b5dd8e11076ebf35e06858f317c` |
| 160 | 🔴 RED | holder:repsol | 42.6 | favorite_collector | 300 | 69 | 3% (1%) | -18.3% | 34.4h | `0x71afaf5a5992739e51fa11caadd52109091ac057` |
| 161 | 🔴 RED | holder:Zaratustra | 42.6 | general_trader | 300 | 3 | 100% (53%) | -5.5% | 46.5h | `0x7818687f1c2cda416877ab68d18d2c9c25f9d185` |
| 162 | 🔴 RED | holder:long1982 | 42.6 | midprice_market_maker | 300 | 359 | 2% (2%) | -47.9% | 3.7h | `0xfb1388292ea54f8541efdd18c417a51b59075946` |
| 163 | 🔴 RED | lb-profit-30d:RN1 | 42.5 | general_trader | 300 | 490 | 21% (18%) | -16.4% | 0.5h | `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` |
| 164 | 🔴 RED | holder:minnisj | 42.5 | general_trader | 300 | 3 | 33% (8%) | -17.5% | 268.7h | `0x0c9eb97737c40b4dab9c3fe08ad5f7198233352a` |
| 165 | 🔴 RED | holder:2026gogogo | 42.4 | category_specialist:crypto | 300 | 175 | 0% (0%) | -34.8% | 200.1h | `0x87ecc34aa4c597190f61859603ddb6be14ea0777` |
| 166 | 🔴 RED | holder:50-Pence | 42.4 | longshot_fader | 300 | 132 | 5% (3%) | -8.6% | 0.0h | `0x9478e0b0db650ac66ca3a2c9f6ed68ebca4863f5` |
| 167 | 🔴 RED | holder:BroukPytlik | 42.3 | longshot_fader | 300 | 52 | 14% (8%) | -5.5% | 36.1h | `0x2936e1ec71c0ce15369908d3a83ec39481ca7be9` |
| 168 | 🔴 RED | lb-profit-1d:FullPicks1 | 42.2 | category_specialist:sports | 259 | 1 | 100% (27%) | +0.0% | 0.0h | `0x9b1e0334569aa1768a07705a859686aad58e82c9` |
| 169 | 🔴 RED | holder:CornelJxJ | 42.2 | longshot_fader | 97 | 2 | 0% (0%) | -15.0% | 749.4h | `0xc395b6a171dbf0958e1f76af0e5e235aa391c64b` |
| 170 | 🔴 RED | YatSen | 42.1 | general_trader | 300 | 60 | 3% (1%) | -32.1% | 434.0h | `0x5bffcf561bcae83af680ad600cb99f1184d6ffbe` |
| 171 | 🔴 RED | holder:btctohigh | 42.1 | favorite_collector | 45 | 0 | 0% (0%) | -8.0% | 822.3h | `0xee44112c72e9e9bae6fa4135de67956e38e31f54` |
| 172 | 🔴 RED | holder:alihanyer | 42.0 | general_trader | 300 | 5 | 0% (0%) | -6.3% | 43.0h | `0x1615086ace48440b0bc0da28a9dfc3d6e8208f2b` |
| 173 | 🔴 RED | holder:JustCrazy | 42.0 | longshot_fader | 300 | 104 | 10% (6%) | -2.5% | 0.5h | `0xc21ea96be762bb55041529af6e386e7c53b80215` |
| 174 | 🔴 RED | holder:nx693 | 41.8 | longshot_fader | 300 | 0 | 0% (0%) | -2.5% | 3528.6h | `0x2f14a4b3a260a8a0db488175c317d474d9f6b2fa` |
| 175 | 🔴 RED | holder:alwayslatetoth | 41.8 | longshot_fader | 300 | 2 | 0% (0%) | -4.3% | 26.9h | `0xb687f00464e33934f5d591f224e71c3559ecaee5` |
| 176 | 🔴 RED | holder:BruceZhao | 41.8 | favorite_collector | 36 | 2 | 0% (0%) | -19.6% | 2510.6h | `0xf73677e8ec74c0526bfd46c5770e6cfbd4f2c6e0` |
| 177 | 🔴 RED | holder:0x9F2E04C7795C | 41.8 | longshot_fader | 300 | 10 | 0% (0%) | -4.4% | 2542.5h | `0x9f2e04c7795c87631a26bb304d79217f873a9061` |
| 178 | 🔴 RED | lb-profit-7d:Sassy-Bucket | 41.7 | category_specialist:sports | 300 | 51 | 4% (1%) | -50.8% | 1.5h | `0x4bff30af91642dc7d2b19a8664378fe55c45fc26` |
| 179 | 🔴 RED | lb-profit-7d:LaBradfordSmit | 41.6 | category_specialist:sports | 300 | 496 | 1% (1%) | -46.7% | 5.0h | `0x9495425feeb0c250accb89275c97587011b19a27` |
| 180 | 🔴 RED | holder:Kura1101 | 41.6 | longshot_fader | 24 | 1 | 0% (0%) | -13.4% | 718.2h | `0x599f72c605635944bbfafc4511aebd05ebe94ce3` |
| 181 | 🔴 RED | holder:parkyun205 | 41.5 | category_specialist:sports | 300 | 66 | 0% (0%) | -43.3% | 24.6h | `0xa3922eaac3633b419f1d30831511275d0a941415` |
| 182 | 🔴 RED | holder:0x90Bf2dbB1ab3 | 41.5 | general_trader | 300 | 25 | 0% (0%) | -26.2% | 126.4h | `0x90bf2dbb1ab3b3c1bdd76d73848afcb19b5799eb` |
| 183 | 🔴 RED | holder:SemyonMarmelad | 41.4 | midprice_market_maker | 300 | 497 | 0% (0%) | -44.2% | 1.2h | `0x37e4728b3c4607fb2b3b205386bb1d1fb1a8c991` |
| 184 | 🔴 RED | holder:0x10B30364936B | 41.3 | general_trader | 300 | 0 | 0% (0%) | -14.1% | 976.7h | `0x10b30364936b03d26b3fd01a63d1f991454b40d4` |
| 185 | 🔴 RED | lb-profit-1d:EB99999 | 41.2 | general_trader | 300 | 1 | 0% (0%) | -26.9% | 143.1h | `0x5d0f03cf1243a3e21262d6cf844795afd9fff0ad` |
| 186 | 🔴 RED | holder:0xa5ef39c3 | 41.2 | unknown | 0 | 448 | 91% (88%) | +0.0% | 0.0h | `0xa5ef39c3d3e10d0b270233af41cac69796b12966` |
| 187 | 🔴 RED | holder:RoloPy | 41.2 | general_trader | 161 | 54 | 0% (0%) | -24.4% | 20.8h | `0x13558f3c3ea3f6e74e058a529101a4100e859955` |
| 188 | 🔴 RED | holder:balldontlieee | 41.1 | general_trader | 300 | 14 | 71% (49%) | -4.8% | 71.1h | `0x966cd85371117d811aab6e6f2b98377433659b1a` |
| 189 | 🔴 RED | holder:Yelowyolo | 41.0 | category_specialist:politics | 300 | 23 | 52% (36%) | -0.2% | 5.8h | `0x8a815b830d6ecfb203abd27334ef8d621e2558b0` |
| 190 | 🔴 RED | holder:fanmt | 41.0 | longshot_fader | 300 | 4 | 0% (0%) | -3.1% | 94.2h | `0x6bad153a277a5c1892384d8ca28122b3f1704d53` |
| 191 | 🔴 RED | holder:NoobCapt | 41.0 | general_trader | 300 | 2 | 50% (12%) | -19.1% | 178.9h | `0xee30e5174dae1fd602ff1f06cc398bf67a1f9297` |
| 192 | ⚫ BLACK | holder:edenmoon | 40.8 | insider_suspected | 300 | 1 | 100% (27%) | -3.3% | 90.7h | `0x3d1ecf16942939b3603c2539a406514a40b504d0` |
| 193 | 🔴 RED | holder:suohaSJB | 40.8 | longshot_fader | 300 | 4 | 0% (0%) | -20.4% | 63.0h | `0x81bc8f470d0a4281c1246fe2c10bf64088adfcfa` |
| 194 | 🔴 RED | holder:AppleTime67 | 40.8 | category_specialist:sports | 300 | 0 | 0% (0%) | -5.0% | 8.0h | `0xacb206b460a17382a734de8d931cc176307eb989` |
| 195 | 🔴 RED | holder:RaphCrypto | 40.7 | longshot_collector | 300 | 20 | 40% (24%) | -1.5% | 90.4h | `0x187365dee1866e49c87fba10734375615d5d37b6` |
| 196 | 🔴 RED | holder:Samomalo | 40.7 | favorite_collector | 300 | 0 | 0% (0%) | -3.5% | 1553.8h | `0x524506fe322ad3e91bd61ba6d12836affc250d45` |
| 197 | 🔴 RED | lb-volume-7d:ArmageddonRewa | 40.6 | general_trader | 300 | 55 | 26% (17%) | -5.2% | 1.7h | `0xc8ab97a9089a9ff7e6ef0688e6e591a066946418` |
| 198 | 🔴 RED | holder:mooseborzoi | 40.5 | general_trader | 300 | 130 | 46% (39%) | -2.5% | 1.1h | `0x84cfffc3f16dcc353094de30d4a45226eccd2f63` |
| 199 | 🔴 RED | holder:juanse000 | 40.5 | longshot_fader | 4 | 0 | 0% (0%) | -10.9% | 655.3h | `0x3d3a48ca1da92e560db9ff9512e4ae0da8c81126` |
| 200 | 🔴 RED | holder:0xb8df15967183 | 40.4 | longshot_fader | 17 | 1 | 0% (0%) | -4.7% | 954.2h | `0xb8df159671834d9e8113f7905e93c7f0bfa04c92` |
| 201 | 🔴 RED | holder:wdp8819 | 40.4 | longshot_fader | 300 | 0 | 0% (0%) | -6.0% | 975.6h | `0xdece29298a4974b457272894a7663e89d81f4cd8` |
| 202 | 🔴 RED | holder:GoriIIa | 40.3 | longshot_fader | 300 | 1 | 0% (0%) | -25.0% | 110.7h | `0xfffadf38a520cd5a0035ff52d7fceb436a08864b` |
| 203 | 🔴 RED | holder:jt7 | 40.3 | category_specialist:sports | 300 | 144 | 0% (0%) | -41.9% | 3.0h | `0x25cc572fae8d022da57a888597561908fd669297` |
| 204 | 🔴 RED | holder:nohash69 | 40.2 | general_trader | 300 | 51 | 4% (1%) | -42.8% | 19.8h | `0x195d0bfaeaf0af2d68e2d9200d2fd4d2edff2dec` |
| 205 | 🔴 RED | holder:alwaysfade | 40.2 | category_specialist:sports | 300 | 34 | 0% (0%) | -42.0% | 18.9h | `0xe5b70fd855af9258d9463992e4f1ed7987905ee3` |
| 206 | 🔴 RED | holder:Yang-H | 40.2 | favorite_collector | 130 | 0 | 0% (0%) | -7.7% | 394.6h | `0x796134216a4928b0b90a44e2ecfa4a14585c1b1c` |
| 207 | 🔴 RED | lb-profit-1d:0x53757615de1c | 40.1 | longshot_fader | 300 | 203 | 21% (17%) | -6.6% | 6.5h | `0x53757615de1c42b83f893b79d4241a009dc2aeea` |
| 208 | 🔴 RED | lb-profit-7d:Mosley1 | 40.1 | category_specialist:sports | 300 | 51 | 0% (0%) | -42.7% | 17.0h | `0x5bec79df9add70a3892041ab1a5516b60f53b215` |
| 209 | 🔴 RED | holder:tsihkodiives | 40.1 | longshot_fader | 300 | 358 | 4% (2%) | -8.3% | 43.3h | `0x6db983ff1cbc85249e64e6ccd101aaa613ba4ab5` |
| 210 | 🔴 RED | holder:alwayslate1331 | 40.1 | longshot_fader | 39 | 3 | 0% (0%) | -14.5% | 1107.0h | `0x608b16197375d35db426375ccc2704dc6203fbd6` |
| 211 | 🔴 RED | holder:annuity972 | 40.1 | general_trader | 45 | 1 | 0% (0%) | -18.3% | 218.4h | `0x35f0f7dc346142f3084c9e6ccda2de8994ed000f` |
| 212 | 🔴 RED | holder:funplayer- | 40.1 | general_trader | 300 | 28 | 7% (2%) | -9.0% | 92.4h | `0x373a949d617e60cbb25ca6df3f68018d573bf4c1` |
| 213 | 🔴 RED | holder:PDJ88 | 40.0 | category_specialist:sports | 300 | 20 | 0% (0%) | -31.5% | 142.7h | `0x0e1d01759cfa75782134472a7af5963da9d50c53` |
| 214 | 🔴 RED | holder:rivaltwistino | 40.0 | longshot_fader | 3 | 2 | 0% (0%) | -4.4% | 565.8h | `0x6539e7ea8b9169bc56b719f058e151173195434a` |
| 215 | 🔴 RED | holder:0x7Ac67A1555c3 | 40.0 | longshot_fader | 289 | 1 | 0% (0%) | -4.2% | 214.7h | `0x7ac67a1555c361a47eafac1a138cc82c20ab92ca` |
| 216 | 🔴 RED | holder:avocato | 40.0 | general_trader | 300 | 2 | 0% (0%) | -13.7% | 359.9h | `0x088e9e9e70240212a1bae73269598fb0fc96bc56` |
| 217 | 🔴 RED | holder:qwenten | 39.9 | category_specialist:sports | 192 | 31 | 6% (2%) | -39.3% | 118.8h | `0xd4aef53973f29fa1feb3ee36b1b6fe7420d07aa6` |
| 218 | 🔴 RED | holder:politics | 39.8 | longshot_fader | 14 | 4 | 0% (0%) | -30.5% | 93.4h | `0x917b3de3741bdec895670a718f9869f626f44df4` |
| 219 | 🔴 RED | holder:ijkjijkj | 39.8 | favorite_collector | 38 | 2 | 0% (0%) | -32.4% | 1946.8h | `0xc4d45681cbec788c20ab549b11f1a9c30edca57a` |
| 220 | 🔴 RED | holder:0xDCD00E0eDE97 | 39.7 | longshot_fader | 15 | 2 | 0% (0%) | -7.6% | 1941.1h | `0xdcd00e0ede9719fd856f8d8a9a0e19a9a91453e5` |
| 221 | 🔴 RED | holder:FC3988 | 39.7 | general_trader | 300 | 3 | 67% (25%) | -12.4% | 32.6h | `0xdfda01f4b92cd096c6d04eed6eb2b069fd584fe6` |
| 222 | 🔴 RED | holder:0xA916bFFd830C | 39.7 | longshot_fader | 87 | 5 | 20% (5%) | -23.6% | 2017.4h | `0xa916bffd830cba9530dc6fdcd2cdc8a691491022` |
| 223 | 🔴 RED | holder:xianzhongdaddy | 39.7 | general_trader | 8 | 0 | 0% (0%) | -4.6% | 3253.7h | `0x442d978eceddf745f6dbaa242441572ec32772cb` |
| 224 | 🔴 RED | holder:Tenebrus7 | 39.6 | general_trader | 300 | 176 | 20% (15%) | -13.9% | 4.4h | `0xa8c63f775ddbbe66b56614191747def3021444e8` |
| 225 | 🔴 RED | lb-profit-1d:bossoskil1 | 39.5 | category_specialist:sports | 300 | 397 | 0% (0%) | -41.8% | 0.0h | `0xa5ea13a81d2b7e8e424b182bdc1db08e756bd96a` |
| 226 | 🔴 RED | lb-profit-1d:BBPK | 39.5 | midprice_market_maker | 300 | 139 | 1% (0%) | -46.8% | 0.0h | `0xee0d153c17fe82b8866b484753b56a700ab457ab` |
| 227 | 🔴 RED | holder:Melqui | 39.5 | favorite_collector | 300 | 3 | 67% (25%) | -1.6% | 78.2h | `0x3e0a8847c74b98a0d865e24ae399604ddf67b9cc` |
| 228 | 🔴 RED | holder:Zptml | 39.5 | favorite_collector | 187 | 4 | 0% (0%) | -15.5% | 2419.5h | `0xecb98ff2542d9c57ec36aa3ecad3734b9e295a12` |
| 229 | 🔴 RED | holder:test124566 | 39.5 | category_specialist:sports | 300 | 93 | 4% (2%) | -38.7% | 0.0h | `0x16b1f68da281f346fa9ff7a46e9d55826abe968a` |
| 230 | 🔴 RED | holder:0x71e11e0f | 39.5 | general_trader | 300 | 67 | 6% (3%) | -14.2% | 33.9h | `0x71e11e0fc20a2adf27026fbf8674b38f8ff945f0` |
| 231 | 🔴 RED | holder:HDGB | 39.4 | longshot_fader | 300 | 18 | 0% (0%) | -1.4% | 51.1h | `0x2e3ea056400d81c42e2ce26ef25fda4ec5caabea` |
| 232 | 🔴 RED | holder:GoldenAlpha168 | 39.3 | midprice_market_maker | 300 | 66 | 2% (0%) | -48.3% | 2.0h | `0x9ba8d25a054044bb66d0ca4e250a16dbfb64cdb3` |
| 233 | 🔴 RED | lb-volume-7d:GoalLineGhost | 39.2 | hft_uncopyable | 300 | 498 | 37% (34%) | -14.0% | 0.0h | `0x0346afae2603313d2bbee96b628536c8cbe352a5` |
| 234 | 🔴 RED | holder:0xB10bf118b2A3 | 39.2 | hft_uncopyable | 300 | 296 | 1% (1%) | -32.9% | 0.4h | `0xb10bf118b2a3c1cff0379a4134a82eb6d51e0b04` |
| 235 | 🔴 RED | holder:Hyperlong | 39.2 | general_trader | 300 | 6 | 50% (22%) | -2.6% | 123.0h | `0x014c4e7ae2145992861c2d1b124af633a97f820c` |
| 236 | 🔴 RED | holder:biggest18 | 39.1 | general_trader | 13 | 3 | 0% (0%) | -95.4% | 1598.6h | `0x58dc538247468e09efc9dfc361a60e047bc4e95c` |
| 237 | 🔴 RED | holder:Masacrador | 39.1 | longshot_fader | 19 | 0 | 0% (0%) | -15.5% | 1230.0h | `0x4213826f1da5fbced01c5518e96daa079c67b8ca` |
| 238 | 🔴 RED | holder:thebug44 | 39.1 | category_specialist:sports | 300 | 1 | 100% (27%) | -11.6% | 621.4h | `0xde7cdcab3e0c5b0e8315da358e80c7d80a12c933` |
| 239 | 🔴 RED | holder:FrancoMastuant | 39.1 | longshot_fader | 300 | 6 | 0% (0%) | -5.6% | 327.3h | `0x1fa04fe548fed271beb16f3bdd9d119bc2c3cac8` |
| 240 | 🔴 RED | holder:simiank777 | 39.0 | general_trader | 300 | 4 | 50% (18%) | -1.9% | 154.8h | `0xefa3ba00c7495a9b4b2b46aa0d21a8023e8ed08b` |
| 241 | 🔴 RED | holder:qqq89 | 39.0 | category_specialist:sports | 300 | 43 | 0% (0%) | -25.1% | 13.3h | `0x575a227b3d9369b06a4aeffb3ab820b407f3bba6` |
| 242 | 🔴 RED | holder:Woohx | 39.0 | longshot_collector | 300 | 2 | 50% (12%) | -13.1% | 122.4h | `0x60c1f86859f2724effffffd4cae4bb0259190438` |
| 243 | 🔴 RED | holder:bookaka | 39.0 | general_trader | 300 | 3 | 67% (25%) | -23.4% | 766.8h | `0x17115903b4ddc47c0b5997724749f09169f678ec` |
| 244 | 🔴 RED | holder:lasix928 | 39.0 | favorite_collector | 300 | 0 | 0% (0%) | -48.4% | 296.1h | `0x83d4d28475bbcf7422cc468dfca22777feecbce8` |
| 245 | 🔴 RED | holder:Bp8757 | 38.9 | favorite_collector | 92 | 1 | 0% (0%) | -7.9% | 2701.5h | `0xa5cafdc75967fe17f9df2e14f1f909a469e53070` |
| 246 | 🔴 RED | holder:0xe9076a87 | 38.8 | longshot_fader | 300 | 87 | 24% (17%) | -2.7% | 0.0h | `0xe9076a87c5ed90ef16e6fe6529c943baeca0cff6` |
| 247 | 🔴 RED | holder:OhneScharf | 38.7 | general_trader | 300 | 30 | 0% (0%) | -40.7% | 422.4h | `0xd2770343da54f1a2ed7305dbf83eeefa4a8b73fe` |
| 248 | 🔴 RED | holder:icanseeitall | 38.7 | general_trader | 300 | 20 | 5% (1%) | -40.5% | 48.0h | `0xbce543209b599a2384ea78f30c4968474fcd02f1` |
| 249 | 🔴 RED | holder:happylifeman | 38.7 | general_trader | 43 | 0 | 0% (0%) | -5.8% | 198.3h | `0xf19191b814d9ee30bc8c325850c6b254464079bb` |
| 250 | 🔴 RED | holder:300PS | 38.5 | general_trader | 300 | 3 | 67% (25%) | -6.0% | 2.4h | `0x8f41129e43ebfbfe6075d0804f3b2bb763b3260e` |
| 251 | 🔴 RED | holder:peaceworldgo | 38.5 | longshot_fader | 39 | 1 | 0% (0%) | -25.0% | 725.8h | `0x5059b86f8108d323728259104f3d706837243d42` |
| 252 | 🔴 RED | holder:shuishen00 | 38.5 | general_trader | 300 | 17 | 0% (0%) | -29.5% | 957.2h | `0xbc9a9aca9bafb4d9a2b7640f3a4bcb273e07b2ff` |
| 253 | 🔴 RED | holder:steiner | 38.4 | longshot_fader | 300 | 16 | 0% (0%) | -14.7% | 937.9h | `0x2dd15107f0b6b3ff71ab747432e6bb0b76037af0` |
| 254 | 🔴 RED | holder:justdoit0 | 38.4 | general_trader | 82 | 1 | 0% (0%) | -40.5% | 714.2h | `0xe9de6cbbda8a7ef721aef9f998c0be4d680e215b` |
| 255 | 🔴 RED | holder:no-cry-in-casi | 38.3 | general_trader | 300 | 1 | 100% (27%) | -11.0% | 769.1h | `0x8506d66c17dbe55b919d30a2807b6822b60410ea` |
| 256 | 🔴 RED | holder:P1kaso | 38.2 | general_trader | 300 | 46 | 15% (8%) | -24.5% | 422.0h | `0x4aefed77846f1b884bcbfb9e63acb351c2be9337` |
| 257 | 🔴 RED | holder:mikelmoreno | 38.1 | longshot_fader | 300 | 0 | 0% (0%) | -8.9% | 599.3h | `0x8101b9dedd1af262b2cb0a64f278d65695bbe7be` |
| 258 | 🔴 RED | holder:0x81ad90fe | 38.1 | longshot_fader | 300 | 1 | 0% (0%) | -27.0% | 262.0h | `0x81ad90fe856d6e61e73c8a0a3cab131d63f654c9` |
| 259 | 🔴 RED | holder:Blackred | 37.9 | longshot_fader | 300 | 12 | 0% (0%) | -6.2% | 232.5h | `0xde7ed2253d8da0b623e026b0e5ef55f4ca91396b` |
| 260 | 🔴 RED | holder:gorovi | 37.9 | favorite_collector | 300 | 23 | 4% (1%) | -48.3% | 225.5h | `0x1de92e091804c709f5e06bf1d132f946e673831d` |
| 261 | ⚫ BLACK | holder:volokolasik333 | 37.8 | insider_suspected | 10 | 1 | 100% (27%) | -6.5% | 19.8h | `0x756868aadfb4c6c1e56691a6fb8112286adddaf0` |
| 262 | 🔴 RED | holder:Jdhdhduu | 37.7 | category_specialist:sports | 300 | 3 | 0% (0%) | -15.8% | 240.2h | `0xdd92232bcdfbbac04132b3cbacbf32c2e5b16b2a` |
| 263 | 🔴 RED | holder:StudentMoney | 37.7 | general_trader | 300 | 60 | 2% (0%) | -39.3% | 127.8h | `0xfb5148fc7223630e0967dbfa8cd920d83ab4742d` |
| 264 | 🔴 RED | holder:BafanaBafana | 37.6 | favorite_collector | 300 | 8 | 12% (3%) | -10.4% | 1703.8h | `0xf72cb9e1ffe0e51da6e747555174cf81a7b9eeb7` |
| 265 | 🔴 RED | holder:Honma | 37.6 | longshot_fader | 250 | 4 | 0% (0%) | -11.2% | 535.0h | `0xba0b958b726c1d64829f294bb852fee274847278` |
| 266 | 🔴 RED | holder:Morbo | 37.5 | longshot_fader | 171 | 3 | 0% (0%) | -27.0% | 4125.8h | `0x0e5bdeb6c2a57d7cca3b06653a26780f1fb27cfc` |
| 267 | 🔴 RED | holder:OverDueJam | 37.5 | general_trader | 300 | 40 | 8% (3%) | -39.2% | 8.3h | `0x078ea5b2830eaab20c73f11bcca98bd5a4023ebd` |
| 268 | 🔴 RED | holder:dingaaling | 37.3 | favorite_collector | 22 | 1 | 0% (0%) | -21.7% | 1060.7h | `0xa146e43c70bb667d8ea1c08a1c5708b010fe88a4` |
| 269 | 🔴 RED | holder:FarmerGambler | 37.2 | longshot_fader | 300 | 0 | 0% (0%) | -0.8% | 0.0h | `0x4fbbf05fd317e2a68733d80e673b7aeffe074cbc` |
| 270 | 🔴 RED | holder:fantasici | 37.2 | general_trader | 300 | 10 | 0% (0%) | -52.5% | 965.5h | `0x9af768b815cb422bdcb37cd050e67ca286fb02a6` |
| 271 | 🔴 RED | holder:TTdes | 37.2 | category_specialist:sports | 300 | 459 | 2% (1%) | -44.0% | 31.8h | `0x25867077c891354137bbaf7fde12eec6949cc893` |
| 272 | 🔴 RED | holder:sssherra | 37.1 | longshot_collector | 300 | 1 | 100% (27%) | -21.5% | 24.1h | `0xee3ecc39c41e8a6b5399b1cd1b03d72f5271ebb5` |
| 273 | 🔴 RED | holder:kingxg | 37.0 | general_trader | 35 | 4 | 0% (0%) | -70.7% | 1566.7h | `0x82fad94d62962c894eaf0b8f9fbfa9516b646805` |
| 274 | 🔴 RED | holder:kjsgdhkjsdfh | 37.0 | general_trader | 113 | 5 | 0% (0%) | -56.3% | 432.0h | `0xc24676916e5befa774dc74b7654c8abd9f9b14c6` |
| 275 | ⚫ BLACK | holder:0xa82038eb | 36.9 | insider_suspected | 300 | 1 | 100% (27%) | -9.9% | 427.4h | `0xa82038ebbe638d53466a1d504d65f827402cba10` |
| 276 | 🔴 RED | holder:0x63a4F883F689 | 36.9 | longshot_fader | 300 | 12 | 8% (2%) | -4.1% | 6.3h | `0x63a4f883f6897df0eaff6318adb18f4b45d40091` |
| 277 | 🔴 RED | holder:0x0b4543fa | 36.8 | general_trader | 300 | 0 | 0% (0%) | -10.2% | 1426.1h | `0x0b4543fa7b6b6261b88f4d913c774a205f56db48` |
| 278 | 🔴 RED | holder:demon42 | 36.8 | longshot_fader | 209 | 18 | 6% (1%) | -21.6% | 2503.2h | `0x04c04a3c0bc826074b1272606566dd2db98f4f3d` |
| 279 | 🔴 RED | holder:Shmuel31 | 36.8 | general_trader | 92 | 8 | 0% (0%) | -37.1% | 689.5h | `0xc112cc01e598b429cb276f7785d62aec2cdf47b0` |
| 280 | 🔴 RED | holder:numbernine | 36.7 | general_trader | 300 | 12 | 0% (0%) | -42.1% | 653.1h | `0xe7fd3fb56636dedc7dc481eca4b08d8ab5fb89de` |
| 281 | 🔴 RED | holder:StephenCampos | 36.6 | category_specialist:sports | 34 | 1 | 100% (27%) | -11.2% | 337.7h | `0x277e331c25260a1c712e0e8d801687b96feb7a02` |
| 282 | 🔴 RED | holder:ZRGyoyo | 36.6 | general_trader | 300 | 3 | 0% (0%) | -40.2% | 677.4h | `0x1d749b198ea0d5136b21fc128fba38bc419c96eb` |
| 283 | 🔴 RED | holder:Markcoin10 | 36.6 | category_specialist:crypto | 125 | 23 | 4% (1%) | -17.3% | 272.9h | `0x85a2ef42b0030ffba5c015a15f91eb286ab3203c` |
| 284 | 🔴 RED | holder:timeflybird | 36.6 | favorite_collector | 33 | 1 | 0% (0%) | -123.0% | 798.1h | `0x82388fc29564155dceb631c1bbb4c6674321ca37` |
| 285 | 🔴 RED | holder:FootballFan98 | 36.5 | general_trader | 300 | 3 | 67% (25%) | -21.6% | 96.3h | `0xc31d0a0d63d760d72a1236d16beaa6a71c854ebe` |
| 286 | 🔴 RED | holder:Ronaldo2win | 36.5 | longshot_fader | 43 | 3 | 0% (0%) | -31.3% | 373.2h | `0xd8474df65bfc771faa0459ce6e32b83b5b0dae3a` |
| 287 | 🔴 RED | holder:growthwizard | 36.5 | longshot_fader | 22 | 4 | 0% (0%) | -13.0% | 157.5h | `0xb7213693631d70e6acfc0b867362577473a924f0` |
| 288 | 🔴 RED | holder:ssalu | 36.5 | longshot_fader | 82 | 14 | 0% (0%) | -19.6% | 757.9h | `0xc6325d53416cfe31c8becc1919e3c73b4c456871` |
| 289 | 🔴 RED | holder:huatimus | 36.5 | favorite_collector | 300 | 12 | 33% (16%) | -20.2% | 2461.6h | `0x7a1849ac8a195e3fd479f81c0b3277ab5d0cd1c9` |
| 290 | 🔴 RED | holder:Haradwaith | 36.4 | longshot_fader | 300 | 42 | 29% (19%) | -3.0% | 0.4h | `0x21ffd2b7a212a6f277ed3eca1a9f8efcbca90d71` |
| 291 | 🔴 RED | holder:jonjon1986 | 36.1 | general_trader | 147 | 0 | 0% (0%) | -13.9% | 1235.5h | `0x343999a9d134cb8c6299138cc4d034472ffb22a1` |
| 292 | 🔴 RED | holder:0x931cd2259731 | 36.1 | category_specialist:crypto | 300 | 201 | 0% (0%) | -17.8% | 0.0h | `0x931cd2259731f65ff31faa5233f446b9f50ca002` |
| 293 | 🔴 RED | holder:PapiBowser | 36.1 | category_specialist:sports | 27 | 5 | 0% (0%) | -33.3% | 690.5h | `0x4f3818cc7bca7c79680bb7fd3ac4108b7f3a2e85` |
| 294 | 🔴 RED | holder:bobbydrews | 36.1 | longshot_fader | 2 | 0 | 0% (0%) | -14.9% | 382.3h | `0x321af590ec54737ab8b3e49f6cfcbeee54c2cd4f` |
| 295 | 🔴 RED | holder:0x7D8d5d166816 | 36.1 | longshot_fader | 17 | 5 | 0% (0%) | -28.5% | 1701.9h | `0x7d8d5d16681608623baf323c291f17760bb1c4d6` |
| 296 | 🔴 RED | holder:Gamblingmoney | 36.0 | general_trader | 60 | 6 | 0% (0%) | -48.0% | 664.5h | `0x072cf24b0b9f75d2d824e0187be7702a96f4f037` |
| 297 | 🔴 RED | holder:extractive-man | 35.9 | longshot_fader | 300 | 7 | 29% (10%) | -0.8% | 440.2h | `0xf9f207b77137caa79c6c4516abdef3133db45cba` |
| 298 | 🔴 RED | holder:0x1EA06EA7143D | 35.9 | category_specialist:sports | 300 | 3 | 0% (0%) | -89.6% | 861.5h | `0x1ea06ea7143d3b8e2431f9cab7011619c269950a` |
| 299 | 🔴 RED | holder:EHA | 35.9 | general_trader | 300 | 22 | 0% (0%) | -33.0% | 178.2h | `0x4bbe47831533d6eca88e2e602ee4e444aa72abc6` |
| 300 | 🔴 RED | holder:heybabyY | 35.9 | general_trader | 195 | 5 | 0% (0%) | -75.0% | 81.1h | `0x6a3e9d4c9222ae5592e85d650bd68d6b7c363d5b` |
| 301 | 🔴 RED | holder:0x8ba27b7c | 35.8 | longshot_fader | 98 | 2 | 0% (0%) | -48.9% | 396.4h | `0x8ba27b7c9de2b6367f986bff5f9c8049204c1650` |
| 302 | 🔴 RED | holder:IBELIEVEBLUEDR | 35.8 | general_trader | 66 | 2 | 0% (0%) | -25.9% | 865.4h | `0xecabafef3798538e242c1be52500f73c42d8e8d4` |
| 303 | 🔴 RED | holder:0xd544F7dc1D20 | 35.8 | category_specialist:sports | 300 | 1 | 0% (0%) | -29.3% | 1762.9h | `0xd544f7dc1d20e5fe38574650dd80b10075111a81` |
| 304 | 🔴 RED | holder:0xfc4fd600 | 35.8 | general_trader | 18 | 1 | 0% (0%) | -104.0% | 2871.3h | `0xfc4fd6009b83ba96df12782802f184feb54c9bb0` |
| 305 | 🔴 RED | holder:DonaldDump88 | 35.8 | longshot_fader | 300 | 1 | 0% (0%) | -26.3% | 916.1h | `0x5ab676dbd8bb2dfcb7478ee13618b505babe6eec` |
| 306 | 🔴 RED | holder:DedY4il | 35.8 | category_specialist:sports | 31 | 2 | 0% (0%) | -68.3% | 1564.3h | `0x898f5c73e39f2e6659d01fd2e0a86aab0d3a3757` |
| 307 | 🔴 RED | holder:ocur | 35.8 | general_trader | 83 | 1 | 0% (0%) | -121.1% | 1872.6h | `0x6f85a34afc3e8e8d1229d24831d8ee632ab741b1` |
| 308 | 🔴 RED | holder:0x2d44eCac541F | 35.8 | category_specialist:sports | 55 | 2 | 0% (0%) | -62.6% | 1193.9h | `0x2d44ecac541f3c55577eb226f4d99409bb48a304` |
| 309 | 🔴 RED | btc-bot-B | 35.7 | category_specialist:crypto | 300 | 6 | 50% (22%) | -9.4% | 0.0h | `0x1979ae6b7e6534de9c4539d0c205e582ca637c9d` |
| 310 | 🔴 RED | holder:ab2.0 | 35.7 | general_trader | 21 | 1 | 0% (0%) | -47.9% | 563.9h | `0x76c9e892ec3dc2cb7977041cbfdc87596877628f` |
| 311 | 🔴 RED | holder:msm299 | 35.7 | longshot_fader | 300 | 1 | 0% (0%) | -58.1% | 228.9h | `0xa252a7efd9572128117c869fa4f064bed37edbf4` |
| 312 | 🔴 RED | holder:chinamaxi | 35.7 | category_specialist:sports | 7 | 0 | 0% (0%) | -18.1% | 128.4h | `0x63f390d8493c0122bff4e6b0abc0b7b05d17458b` |
| 313 | 🔴 RED | holder:terry | 35.7 | general_trader | 116 | 1 | 0% (0%) | -29.8% | 991.8h | `0x74d0ad6af3f5bd19b790d5997a1914d0190cd8de` |
| 314 | 🔴 RED | holder:joejoeno3 | 35.7 | longshot_collector | 300 | 2 | 50% (12%) | -7.9% | 975.1h | `0xfaa77ed88112b488f6e96c9168ddbfd06db18150` |
| 315 | 🔴 RED | holder:pmverygood | 35.7 | favorite_collector | 24 | 1 | 0% (0%) | -121.9% | 582.3h | `0x7f0fa269bb1be419a3e6a6e64b21e302d1b4cb20` |
| 316 | 🔴 RED | holder:kafaka | 35.7 | general_trader | 46 | 1 | 0% (0%) | -71.2% | 725.5h | `0xca6387642206994075b0fa089f1d1af2226d6f15` |
| 317 | 🔴 RED | holder:bananavomBa717 | 35.7 | favorite_collector | 23 | 1 | 0% (0%) | -62.5% | 718.1h | `0x7e0375241f72317f68a7a6a755cfb8829692770f` |
| 318 | 🔴 RED | holder:shmuel. | 35.7 | general_trader | 19 | 1 | 0% (0%) | -25.2% | 226.4h | `0xa5834d828304a8cec14d7e807442babec86ab44b` |
| 319 | 🔴 RED | holder:DumbMoney2222 | 35.6 | category_specialist:sports | 300 | 1 | 0% (0%) | -19.4% | 56.4h | `0xcfcabcd88df9e0bebfc4347a86c4686e7cb78b3a` |
| 320 | 🔴 RED | holder:0x1cE22666B8fB | 35.6 | general_trader | 300 | 32 | 3% (1%) | -33.2% | 122.1h | `0x1ce22666b8fb017a55db38c731b05d0b24583c96` |
| 321 | 🔴 RED | holder:goodgmgn | 35.6 | general_trader | 19 | 0 | 0% (0%) | -73.2% | 523.0h | `0x7cfd5ec8c3b264d3fcf55783f6cdb279b9dbb94f` |
| 322 | 🔴 RED | holder:footballone | 35.6 | general_trader | 159 | 2 | 0% (0%) | -118.4% | 96.4h | `0x94a969949177150e56579aeec530e606c3a679f6` |
| 323 | 🔴 RED | lb-profit-1d:AdrianCronauer | 35.5 | general_trader | 300 | 9 | 44% (22%) | -12.4% | 12.3h | `0xf9c1190aa8184bcbe418e6f5321c53b0bfbc39e2` |
| 324 | 🔴 RED | holder:333777 | 35.5 | longshot_fader | 300 | 10 | 0% (0%) | -17.7% | 816.1h | `0x02c50d55157cd98a6ee515a380a86472d7038356` |
| 325 | 🔴 RED | holder:PhilHawesLover | 35.5 | favorite_collector | 300 | 13 | 54% (32%) | -2.7% | 42.0h | `0x6b3a549080f043f5ac2433a30e5ce154c7782841` |
| 326 | 🔴 RED | holder:Str3sU | 35.5 | longshot_fader | 300 | 31 | 10% (4%) | -20.7% | 1230.0h | `0xd71a00e4cd4c7caeedaad16b1b16eae72cbd78c9` |
| 327 | 🔴 RED | lb-profit-1d:aekghas | 35.3 | general_trader | 300 | 0 | 0% (0%) | -26.9% | 45.8h | `0xb2a3623364c33561d8312e1edb79eb941c798510` |
| 328 | 🔴 RED | holder:inchbyinchbyin | 35.1 | general_trader | 300 | 1 | 0% (0%) | -107.5% | 18.6h | `0x47661b3073d6dd0130e61a5c5b6f00b6f8da0286` |
| 329 | 🔴 RED | holder:LionYossi | 35.0 | longshot_fader | 63 | 15 | 0% (0%) | -8.5% | 880.8h | `0x8aae3838fbaaf7ee34a0f16754f26a0b2dac319c` |
| 330 | 🔴 RED | holder:Asperatus | 35.0 | longshot_fader | 300 | 9 | 0% (0%) | -10.9% | 6.8h | `0x36a7e80b487b26eebce266da0640e33dd4651aea` |
| 331 | 🔴 RED | holder:Irboz-sama | 35.0 | general_trader | 300 | 23 | 61% (44%) | -8.5% | 282.7h | `0x9b0b60aa0a1df93202f996860342fd5607815e43` |
| 332 | 🔴 RED | lb-profit-7d:bcda | 34.8 | category_specialist:sports | 300 | 8 | 62% (35%) | -28.0% | 0.2h | `0xb45a797faa52b0fd8adc56d30382022b7b12192c` |
| 333 | 🔴 RED | holder:Jessica562 | 34.8 | general_trader | 300 | 3 | 0% (0%) | -25.2% | 98.6h | `0x8dd73d74b1210be2d5e171c9edd58aeebddfdd08` |
| 334 | 🔴 RED | holder:janglinjack | 34.7 | category_specialist:sports | 300 | 18 | 0% (0%) | -34.1% | 760.8h | `0x9b292d6d18c1f9837af7edfc9b897d8a0fe88373` |
| 335 | 🔴 RED | holder:Emme1 | 34.6 | longshot_fader | 195 | 17 | 0% (0%) | -35.7% | 387.0h | `0xec570193a382465a94dec36c05a09e9061bde0ac` |
| 336 | 🔴 RED | holder:0xe0eE7CB6880b | 34.6 | general_trader | 106 | 2 | 0% (0%) | -22.2% | 7.4h | `0xe0ee7cb6880b02bd192ea12af64cc6134d65b7f8` |
| 337 | 🔴 RED | holder:TradingWave | 34.5 | longshot_collector | 300 | 5 | 60% (27%) | -4.5% | 27.7h | `0xf49ce459b52f60b70ce0fe9aa6203e6bf90f9786` |
| 338 | 🔴 RED | holder:Calvin3328 | 34.5 | longshot_fader | 300 | 15 | 0% (0%) | -9.0% | 506.3h | `0x38b09c9d19c75018afc3ff63b60a33f7d2d7dd47` |
| 339 | 🔴 RED | holder:0x54A598106e04 | 34.4 | longshot_fader | 300 | 21 | 5% (1%) | -17.8% | 319.9h | `0x54a598106e0467dacc1a4ced3909582f72aaee3d` |
| 340 | 🔴 RED | holder:mathmarket | 34.4 | general_trader | 300 | 19 | 0% (0%) | -20.9% | 300.2h | `0x3c648e8295c38533e7c3c38c98dc9e4080e0cb26` |
| 341 | 🔴 RED | holder:Booking07 | 34.2 | longshot_fader | 257 | 28 | 0% (0%) | -33.7% | 794.5h | `0xc18bd4097fd387387030ef63542785c455279491` |
| 342 | 🔴 RED | holder:ttomime | 33.9 | longshot_fader | 300 | 23 | 17% (8%) | -10.6% | 1984.5h | `0xd702c806ea9b89a4fd1b378e4e7a098305cfdaa9` |
| 343 | 🔴 RED | holder:takeormake | 33.8 | category_specialist:sports | 300 | 123 | 5% (2%) | -36.0% | 2.6h | `0xa38a455bbdd4b68486548b7e19da99903f4f821d` |
| 344 | 🔴 RED | holder:albipastore15 | 33.8 | longshot_fader | 300 | 9 | 0% (0%) | -11.0% | 307.1h | `0x80f10b49029e33fde02ac9fb183b49c79d681093` |
| 345 | 🔴 RED | lb-volume-7d:ferrariChampio | 33.7 | hft_uncopyable | 300 | 498 | 7% (6%) | -23.7% | 0.4h | `0xfe787d2da716d60e8acff57fb87eb13cd4d10319` |
| 346 | 🔴 RED | holder:pfing | 33.2 | general_trader | 300 | 21 | 0% (0%) | -42.2% | 1344.4h | `0xc5fa48b547b2fccc480e8699fc2b160d0cac5b59` |
| 347 | 🔴 RED | holder:0x0571f37F4d6D | 33.1 | longshot_fader | 54 | 8 | 0% (0%) | -19.7% | 1005.9h | `0x0571f37f4d6d85c7e177179d9c784cb690b178be` |
| 348 | 🔴 RED | holder:sbimbg | 32.9 | general_trader | 300 | 44 | 9% (4%) | -23.6% | 1.8h | `0xf5198df69e13937a40d1c76d6f72d9aa067d906b` |
| 349 | 🔴 RED | lb-profit-7d:VPenguin | 32.8 | category_specialist:sports | 300 | 1 | 0% (0%) | -47.8% | 0.0h | `0xfbf3d501e88815464642d0e913f15379c3eeb218` |
| 350 | 🔴 RED | holder:0xb187803a | 32.8 | longshot_fader | 300 | 6 | 0% (0%) | -13.2% | 245.4h | `0xb187803a4ac9c5a498e470aab82de203f5870ab8` |
| 351 | 🔴 RED | holder:1223111 | 32.7 | longshot_fader | 50 | 8 | 12% (3%) | -26.9% | 843.7h | `0xd54faddebed2b523bda7334e72bd84888664ec81` |
| 352 | 🔴 RED | holder:mails123 | 32.6 | longshot_fader | 185 | 9 | 0% (0%) | -23.8% | 213.9h | `0xc828a4ebaa5dae5cc1e66a028256ed84efc7dbfa` |
| 353 | 🔴 RED | holder:followflow | 32.5 | general_trader | 300 | 14 | 0% (0%) | -42.3% | 120.1h | `0x37f4c111b2a973fb8a9cce94d6ff60048c7249af` |
| 354 | 🔴 RED | holder:alexbrocan35 | 32.4 | general_trader | 300 | 15 | 0% (0%) | -38.7% | 156.2h | `0xb013a7a854ef42e64b471724346ebec0640c6b3a` |
| 355 | 🔴 RED | aenews2 | 31.9 | general_trader | 300 | 25 | 24% (13%) | -7.2% | 46.3h | `0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1` |
| 356 | 🔴 RED | holder:lonewolfcapita | 31.4 | longshot_fader | 300 | 10 | 0% (0%) | -12.4% | 1226.4h | `0x4110ae59607b55a47d6f13d356e2dc4f90e01586` |
| 357 | 🔴 RED | holder:sportsbettor22 | 31.2 | category_specialist:sports | 300 | 38 | 0% (0%) | -32.7% | 0.2h | `0x20e2d462eb96d6fe2c4c7d3fb99e1df17a93667f` |
| 358 | 🔴 RED | holder:CaughtByRandom | 31.2 | longshot_fader | 137 | 19 | 0% (0%) | -14.6% | 40.6h | `0x67d27256f79f77380537f3fd41306e8353cc6ffb` |
| 359 | 🔴 RED | holder:zarboxyl | 30.9 | longshot_fader | 300 | 13 | 0% (0%) | -21.9% | 1842.3h | `0x59c7fd3c203ee9c6d5ee9a05863e80c2598f4ccc` |
| 360 | 🔴 RED | lb-volume-7d:username123123 | 30.6 | category_specialist:crypto | 300 | 6 | 50% (22%) | -43.1% | 0.0h | `0xd950a1a89f3e61a7a9efc85a46e440ce58c15e86` |
| 361 | 🔴 RED | holder:DavidTrezeguet | 30.4 | general_trader | 300 | 8 | 0% (0%) | -8.8% | 227.5h | `0xc88eb9ab98663254bff489c515f39f23b76bf3e1` |
| 362 | 🔴 RED | holder:0x4880b7b4 | 30.4 | hft_uncopyable | 300 | 2 | 0% (0%) | -8.9% | 0.0h | `0x4880b7b4c78526c1b0dceab2fbfd9c8888925626` |
| 363 | 🔴 RED | holder:piratesfan1313 | 30.0 | category_specialist:sports | 300 | 13 | 23% (10%) | -6.7% | 20.9h | `0xf65506e2d5f55279d77bd67d3c80af6882ad7ea4` |
| 364 | 🔴 RED | holder:llh | 30.0 | favorite_collector | 300 | 6 | 0% (0%) | -39.1% | 1160.9h | `0x834965f34911dfda31d5b313b5def15e6348c99d` |
| 365 | 🔴 RED | holder:0x418D51e13d01 | 29.8 | category_specialist:sports | 300 | 6 | 0% (0%) | -56.5% | 55.6h | `0x418d51e13d019913bb027db22ecc723fe1ad88a3` |
| 366 | 🔴 RED | lb-profit-7d:caicai888888 | 29.7 | midprice_market_maker | 300 | 24 | 0% (0%) | -41.8% | 1.5h | `0x2d7be5170a8026c18709eaea1027c7f12e8ce2ce` |
| 367 | 🔴 RED | holder:abura2025 | 29.7 | category_specialist:sports | 300 | 16 | 0% (0%) | -46.0% | 1.4h | `0x8fba2c29715c41dd87e781c23373aa1e0549d08a` |
| 368 | 🔴 RED | holder:strictly4fun | 29.6 | category_specialist:crypto | 106 | 12 | 0% (0%) | -40.0% | 3731.8h | `0x651efec760a52b4c5743e7bd8169a08da8c1567b` |
| 369 | 🔴 RED | holder:solwizzo-onX | 29.4 | general_trader | 300 | 16 | 6% (1%) | -4.2% | 73.1h | `0xff165cf8eb75ee77933a7544d7cd600ccb2c7511` |
| 370 | 🔴 RED | holder:NitroStock | 29.4 | longshot_fader | 300 | 12 | 8% (2%) | -27.8% | 114.1h | `0x34fe137193b3fbb12e61571d28fc056816d54a5b` |
| 371 | 🔴 RED | holder:TheEmprah | 29.3 | general_trader | 300 | 17 | 12% (4%) | -35.7% | 2154.3h | `0x4cb5ec560735efca23f76f2dd152b74bc6a9b536` |
| 372 | 🔴 RED | holder:plims | 29.2 | general_trader | 28 | 6 | 0% (0%) | -52.6% | 224.2h | `0xc6029e95294f3eb7e52dd3715def991b968aa32b` |
| 373 | 🔴 RED | holder:alphatips.Chan | 29.0 | general_trader | 300 | 8 | 0% (0%) | -38.0% | 1264.9h | `0x2aa13994496b2c84268afff01687122de4abc691` |
| 374 | 🔴 RED | holder:firzek | 29.0 | category_specialist:sports | 300 | 27 | 0% (0%) | -55.5% | 0.0h | `0x5782cc3ae4dcf9f7e322cbdc5bde781883758ce5` |
| 375 | 🔴 RED | lb-volume-7d:downtownfee | 28.9 | midprice_market_maker | 300 | 20 | 5% (1%) | -54.6% | 2.2h | `0xbee54d90051720e27921dc6874f02d646ffca636` |
| 376 | 🔴 RED | holder:smacks97 | 28.8 | general_trader | 67 | 7 | 0% (0%) | -45.8% | 2813.6h | `0x55d201e619fdf5fb7191fd4e54402677ae57efda` |
| 377 | 🔴 RED | lb-profit-30d:beachboy4 | 28.7 | category_specialist:politics | 300 | 0 | 0% (0%) | -44.9% | 0.0h | `0xc2e7800b5af46e6093872b177b7a5e7f0563be51` |
| 378 | 🔴 RED | holder:drew.eth | 28.7 | longshot_fader | 300 | 6 | 0% (0%) | -25.9% | 2670.6h | `0x5b30fdea8850761f614f3f0d6619b05d248029a4` |
| 379 | 🔴 RED | holder:Outsid3rTradin | 27.0 | general_trader | 300 | 7 | 14% (3%) | -15.4% | 78.0h | `0xf1ef8705e9f63c790c6fffd6329aea7011718cd6` |
| 380 | 🔴 RED | lb-profit-7d:mentionmarket | 26.8 | midprice_market_maker | 300 | 13 | 0% (0%) | -46.1% | 1.7h | `0xc3acf5878a03523d09a3ac859943445d7baeb964` |
| 381 | 🔴 RED | holder:videlake | 24.2 | general_trader | 300 | 17 | 12% (4%) | -14.1% | 19.3h | `0x6ae1575206e99751ff60ec5c0adcaad572bc1e7e` |
| 382 | 🔴 RED | holder:mostovaja | 18.3 | category_specialist:sports | 278 | 9 | 11% (2%) | -51.5% | 0.6h | `0x438e1f519cfe1474d19545c09aecf26cb75cc499` |

## Detail — Qualified Wallets

### thread-extract-2  🟡 YELLOW  (62.4/100)

- **Address**: `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`
- **Edge type**: `category_specialist:weather`
- **Sample**: 495 resolved / 300 total trades
- **PnL**: $+98,426 (realized $+145,238)
- **WinRate**: 71.9% (Wilson LB: 68.5%)
- **ROI**: avg +6.7% / LB +4.8%
- **Max DD**: 23.9%  |  **Top position**: 18% of PnL
- **Hold time**: median 2.4h  |  **Avg entry**: 0.10
- **Price regime**: 88% longshot / 2% mid / 5% favorite
- **Main category**: weather (95% concentration)
- **Sub-scores**: edge=67 sample=100 persist=30 anti-luck=37 risk=61 copy=75 indep=70

**Notes**:
- Edge not yet persistent across split-halves
- PnL concentrated (top position = 18%)

### holder:RITB123  🟡 YELLOW  (62.4/100)

- **Address**: `0x724db3c436dcc7b26fbe1ae0c0d6af538b588dea`
- **Edge type**: `category_specialist:crypto`
- **Sample**: 454 resolved / 300 total trades
- **PnL**: $+98,879 (realized $+204,232)
- **WinRate**: 60.1% (Wilson LB: 56.3%)
- **ROI**: avg +2.7% / LB +1.6%
- **Max DD**: 99.3%  |  **Top position**: 8% of PnL
- **Hold time**: median 1.4h  |  **Avg entry**: 0.15
- **Price regime**: 78% longshot / 8% mid / 2% favorite
- **Main category**: crypto (76% concentration)
- **Sub-scores**: edge=47 sample=100 persist=79 anti-luck=40 risk=40 copy=68 indep=70

**Notes**:
- PnL concentrated (top position = 8%)

## Next steps

1. Re-run weekly to catch new wallets and detect edge decay on tracked ones
2. For 🟢 wallets, paper-mirror via PolyCop with 10% bankroll cap and monitor 30 days
3. For 🟡 wallets, watch for sample to grow past n=40 then re-evaluate
4. For ⚫ flags, DO NOT copy — insider edges legally toxic and don't persist after disclosure

## Links

- [[scan_smart_follower]] — Real-time entry detection on tracked wallets
- [[strategy_registry]] — Strategy classifications
- [[edge_research_tests]] — Validation framework