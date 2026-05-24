# SC-016 Wallet Confidence Scan — 2026-05-24 10:51 UTC

**Wallets scored:** 409
**Qualified (conf ≥ 55.0):** 7
**Green badges:** 0
**Black flags:** 4

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
| 1 | 🟡 YELLOW | thread-extract-2 | 65.3 | category_specialist:weather | 300 | 495 | 72% (68%) | +4.8% | 2.5h | `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11` |
| 2 | 🟡 YELLOW | holder:RITB123 | 65.2 | category_specialist:crypto | 300 | 454 | 60% (56%) | +1.6% | 1.5h | `0x724db3c436dcc7b26fbe1ae0c0d6af538b588dea` |
| 3 | 🟡 YELLOW | lb-profit-1d:arlanta | 56.9 | category_specialist:sports | 300 | 15 | 93% (75%) | +5.7% | 7.8h | `0x1136368d7f6728e94ed14c532ab95a932f710c2e` |
| 4 | 🟡 YELLOW | holder:Mike123455 | 56.6 | longshot_fader | 300 | 93 | 8% (4%) | -3.0% | 2032.4h | `0xeee9d0cedb2b8d59069d76d9f39bf58c383df66f` |
| 5 | 🔴 RED | holder:aimforthebushe | 56.5 | longshot_fader | 32 | 0 | 0% (0%) | -0.3% | 587.3h | `0xbc26352dac6b2cc9274dae39f73269192caa15f9` |
| 6 | 🔴 RED | holder:PoloBoloYolo | 56.3 | category_specialist:weather | 300 | 0 | 0% (0%) | -0.1% | 27.9h | `0x1ef09f92e5217e1b757b37ace873f915cb76e2d1` |
| 7 | 🔴 RED | holder:P-J | 55.3 | general_trader | 300 | 1 | 0% (0%) | +0.1% | 1160.5h | `0xd498f2d1ae092dfc39088343f6d4e9219c7780ae` |
| 8 | 🔴 RED | holder:hongmyungbo | 54.5 | longshot_fader | 7 | 0 | 0% (0%) | -0.3% | 347.1h | `0x5dceeeec594b80f465d1be87712a0d6b6885ecd7` |
| 9 | 🟡 YELLOW | holder:DickTurbin | 53.8 | longshot_fader | 300 | 462 | 29% (25%) | -1.0% | 69.3h | `0xb6bed94e75c333dae24eb9c80b3fef47ef3cfcfe` |
| 10 | 🟡 YELLOW | holder:DavidShekel | 53.5 | longshot_fader | 300 | 416 | 20% (16%) | -0.1% | 13.0h | `0x54525ee78bd513b0bf75f94e560158f6fc35d448` |
| 11 | 🟡 YELLOW | holder:iDARKenjoyer | 53.4 | general_trader | 300 | 49 | 65% (54%) | -0.3% | 8.9h | `0xf68a281980f8c13828e84e147e3822381d6e5b1b` |
| 12 | 🟡 YELLOW | holder:Poivre | 52.8 | longshot_fader | 300 | 21 | 24% (12%) | +3.5% | 360.7h | `0x714f682e577a6892ee921290fd6ad213d11266d5` |
| 13 | 🟡 YELLOW | holder:Protrad | 52.7 | longshot_fader | 300 | 78 | 8% (4%) | -0.1% | 29.6h | `0x409f5d76319a96a05d20ed9715bfa00f725e543a` |
| 14 | 🟡 YELLOW | holder:MRF | 52.7 | longshot_fader | 300 | 410 | 15% (12%) | -12.4% | 60.3h | `0x16cbe223607a6513ae76d1e3751c78e4eabc2704` |
| 15 | 🔴 RED | holder:rillsoapsters | 52.6 | category_specialist:crypto | 23 | 1 | 100% (27%) | -2.0% | 91.6h | `0x458fe51fbe51697b2f2945e93b4c0c9e6fd93036` |
| 16 | 🔴 RED | holder:PMTraderAdam | 52.5 | general_trader | 300 | 4 | 75% (36%) | +0.1% | 91.0h | `0x154794795d978c5890b3f69264311f0bd966d066` |
| 17 | 🔴 RED | holder:0x05e17Fb524aa | 52.3 | category_specialist:sports | 300 | 172 | 0% (0%) | -45.0% | 246.8h | `0x05e17fb524aa6896de92dec88db2f0e4dd5285a2` |
| 18 | 🟡 YELLOW | holder:cigarettes | 52.2 | longshot_fader | 300 | 205 | 33% (28%) | +1.4% | 0.5h | `0xd218e474776403a330142299f7796e8ba32eb5c9` |
| 19 | 🔴 RED | holder:lessthanmore | 51.8 | longshot_fader | 300 | 0 | 0% (0%) | -0.2% | 1190.8h | `0x1fdc383a2e0297171a7013e554d5b0cc52b040aa` |
| 20 | 🔴 RED | holder:c0O0OLI0O03 | 51.7 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 2.6h | `0xfedc381bf3fb5d20433bb4a0216b15dbbc5c6398` |
| 21 | 🔴 RED | holder:blue-musketeer | 51.6 | longshot_fader | 300 | 0 | 0% (0%) | -0.1% | 789.6h | `0xb26d7a12b543f69c2aa283b557a600215c16b98d` |
| 22 | 🔴 RED | holder:Romkos7 | 51.4 | general_trader | 300 | 1 | 100% (27%) | -0.0% | 153.3h | `0xa39c488ea8269609aea27f5f8486044d839908bc` |
| 23 | 🟡 YELLOW | holder:rainbowlilies | 51.3 | longshot_fader | 300 | 133 | 15% (11%) | -1.0% | 6.6h | `0x21064fd320bfd5a86f8c92a94d3209edf4154dea` |
| 24 | 🔴 RED | holder:awaiting-lifec | 51.1 | favorite_collector | 300 | 0 | 0% (0%) | -0.9% | 151.1h | `0x4d32e23ab079511ab2de13d58211a99b23d39dfc` |
| 25 | 🔴 RED | ImJustKen | 51.0 | longshot_fader | 300 | 304 | 17% (14%) | -3.9% | 219.2h | `0x9d84ce0306f8551e02efef1680475fc0f1dc1344` |
| 26 | 🔴 RED | holder:mombil | 51.0 | general_trader | 300 | 30 | 57% (42%) | +2.9% | 14.7h | `0x68c24bf4a8ad4d79a6fe4b8eec6f93a02dfd1711` |
| 27 | 🔴 RED | holder:yiyezhiqiu110 | 51.0 | longshot_fader | 3 | 0 | 0% (0%) | -0.1% | 19.4h | `0x267eee7e20027ea3e3ce5386998929d17ee5f2e8` |
| 28 | 🔴 RED | holder:sheepthecards | 50.7 | longshot_fader | 300 | 1 | 0% (0%) | -2.3% | 1348.6h | `0x6cfcf9047deec0d169005df2fcd1bfededfa661e` |
| 29 | 🔴 RED | holder:WorldFest | 50.7 | longshot_collector | 300 | 1 | 100% (27%) | +0.0% | 589.4h | `0xd568130f9f6498b04f985a157aed36d90ebbba70` |
| 30 | 🔴 RED | holder:0x72bbEF3D5247 | 50.6 | category_specialist:crypto | 300 | 341 | 1% (0%) | -13.4% | 30.0h | `0x72bbef3d52476fdb7cf041bbeaabed927e83281b` |
| 31 | 🔴 RED | holder:0xcdlambjrrt0l | 50.5 | category_specialist:politics | 300 | 0 | 0% (0%) | -1.7% | 68.3h | `0x52c2143f69dd3dcd249f688623c64ab5f7900556` |
| 32 | 🔴 RED | lb-profit-1d:surfandturf | 50.4 | category_specialist:sports | 300 | 1 | 100% (27%) | +0.0% | 4.1h | `0x9f2fe025f84839ca81dd8e0338892605702d2ca8` |
| 33 | 🔴 RED | holder:pupop | 50.4 | longshot_fader | 33 | 0 | 0% (0%) | -0.9% | 1630.8h | `0x3d814aa94bc1229bcead270e9512c703b00977b0` |
| 34 | 🔴 RED | holder:0xf3C4ee5Eb5b1 | 50.3 | general_trader | 300 | 447 | 6% (5%) | -26.2% | 275.4h | `0xf3c4ee5eb5b1e1cd70f697cc1f18db7e94b40216` |
| 35 | 🔴 RED | holder:Nicksypoo | 50.2 | general_trader | 300 | 347 | 0% (0%) | -50.8% | 8.2h | `0xcbb5623096b78505a26524e642c5c9066e585ed9` |
| 36 | 🔴 RED | holder:freemuney | 50.1 | longshot_fader | 15 | 0 | 0% (0%) | -0.6% | 1007.9h | `0x1a162eb4dfb533d503dcc0fa09776f6e1b204335` |
| 37 | 🔴 RED | holder:PrimePenguin | 50.0 | longshot_fader | 300 | 458 | 6% (4%) | -13.2% | 71.5h | `0x933ca00f565ba7130180e58fce4f965cc33ba8c6` |
| 38 | 🔴 RED | holder:scapri | 49.9 | longshot_fader | 294 | 0 | 0% (0%) | -0.3% | 2300.2h | `0x9e25f9cd6d4fd6996135e68ff55acb28bca657c7` |
| 39 | 🔴 RED | holder:0x372999C3F35f | 49.9 | general_trader | 62 | 5 | 0% (0%) | -28.7% | 375.0h | `0x372999c3f35fc853143a1c967a193f12e0dd37b3` |
| 40 | 🔴 RED | holder:Xyu | 49.9 | general_trader | 300 | 0 | 0% (0%) | -1.4% | 213.2h | `0xba3ce1a0a3cd1ab1f98981f3ce7350017de22e4e` |
| 41 | 🟡 YELLOW | holder:petanimal | 49.9 | longshot_fader | 300 | 106 | 10% (6%) | -2.8% | 19.1h | `0xfd691577dc6a9d21e9611b93ef9177d36738a2e1` |
| 42 | 🔴 RED | lb-profit-1d:anoin123 | 49.7 | longshot_fader | 300 | 141 | 14% (9%) | -7.9% | 9.2h | `0x96489abcb9f583d6835c8ef95ffc923d05a86825` |
| 43 | 🔴 RED | holder:lecroissant | 49.7 | longshot_fader | 300 | 0 | 0% (0%) | -0.8% | 276.7h | `0x1f7ffa3efbbe5d075d7c3eefe98dce9d8f05f514` |
| 44 | 🔴 RED | holder:billsmurfiks | 49.7 | favorite_collector | 17 | 0 | 0% (0%) | -0.2% | 21.8h | `0x52d316df580ee729b88aa9e41416550680a13509` |
| 45 | 🔴 RED | holder:0x4549f2B1ddc4 | 49.6 | longshot_fader | 300 | 447 | 1% (0%) | -14.3% | 1852.8h | `0x4549f2b1ddc416da61d33447e0272ba95a810450` |
| 46 | 🔴 RED | holder:SunlineTicker | 49.6 | category_specialist:sports | 300 | 494 | 1% (1%) | -42.2% | 2.9h | `0x4df332e27f9ee3224f52ce30e3ce15c1075e788f` |
| 47 | 🔴 RED | holder:0xA712F13C08AD | 49.5 | longshot_fader | 10 | 0 | 0% (0%) | -0.3% | 2221.4h | `0xa712f13c08ada1fabd654b477292c55069147f18` |
| 48 | 🔴 RED | holder:chikipikinss | 49.5 | favorite_collector | 9 | 3 | 100% (53%) | -0.6% | 19.4h | `0xea81727c212edf992eaae489f9f1c84b20e51171` |
| 49 | 🔴 RED | holder:0xc4eaee3c | 49.5 | general_trader | 202 | 0 | 0% (0%) | -18.2% | 191.0h | `0xc4eaee3cdd1e20a75209250dc8c67a6d180262c5` |
| 50 | 🔴 RED | holder:Nk9 | 49.2 | longshot_fader | 300 | 2 | 0% (0%) | -1.0% | 357.5h | `0x410338a0360417802c93d2e8f1c490f0fcc5a4e7` |
| 51 | 🔴 RED | holder:Ecofarmer | 49.2 | general_trader | 300 | 0 | 0% (0%) | -3.8% | 49.8h | `0xfaa55858f098040003978c3615a086cdd0cd7cc9` |
| 52 | 🔴 RED | holder:benbrugger4484 | 49.1 | favorite_collector | 29 | 0 | 0% (0%) | -0.7% | 96.8h | `0x1bfc98668c2494f11deeb924668a69d2490b0c7f` |
| 53 | 🔴 RED | holder:Hazardrip | 49.1 | general_trader | 300 | 76 | 3% (1%) | -17.3% | 406.6h | `0x32b61f77818ee062a1cf0ad4312752879e1a2f9f` |
| 54 | 🔴 RED | holder:0x3069d3c1cf86 | 49.0 | general_trader | 300 | 2 | 0% (0%) | -11.9% | 117.3h | `0x3069d3c1cf8663728fd3deb63e9592977c5f83cd` |
| 55 | 🔴 RED | holder:nzmvfmogzy | 49.0 | favorite_collector | 207 | 0 | 0% (0%) | -0.4% | 288.7h | `0x37cc4b4f791891a18181b820936a5231a7b3e83a` |
| 56 | 🔴 RED | holder:Count.Gusto | 48.9 | longshot_fader | 96 | 0 | 0% (0%) | -0.2% | 1009.9h | `0x866465ff16468c0a0bea259b75cfc575700edd88` |
| 57 | 🔴 RED | holder:0xaf610A793ec2 | 48.9 | general_trader | 244 | 52 | 0% (0%) | -30.5% | 863.1h | `0xaf610a793ec2d68e929f8073ac4ea51a7ca64d44` |
| 58 | 🔴 RED | holder:0xwhaleshark | 48.8 | longshot_fader | 300 | 4 | 0% (0%) | +0.0% | 12.4h | `0x2179ab15324f5436f1a83c8092b8cc3dad79bedb` |
| 59 | 🔴 RED | Poligarch | 48.7 | category_specialist:weather | 300 | 365 | 55% (51%) | +1.2% | 0.7h | `0xb40e89677d59665d5188541ad860450a6e2a7cc9` |
| 60 | 🔴 RED | holder:peter239784 | 48.7 | longshot_fader | 300 | 74 | 10% (5%) | -15.3% | 80.4h | `0x7d58986f00b3c00e9b24d02f8e35381ca154cfcc` |
| 61 | 🔴 RED | holder:cryptoincome | 48.7 | favorite_collector | 300 | 5 | 100% (65%) | -1.7% | 436.7h | `0xe60f07a844bd18448eb3b23818f94bec1589f4b4` |
| 62 | 🔴 RED | thread-extract-1 | 48.6 | longshot_fader | 300 | 42 | 0% (0%) | -26.4% | 6.0h | `0x8c80d213c0cbad777d06ee3f58f6ca4bc03102c3` |
| 63 | 🔴 RED | holder:fwed33 | 48.6 | general_trader | 300 | 451 | 0% (0%) | -34.0% | 9.4h | `0x14619de097b1fbe058d6d36282662c20958a30a1` |
| 64 | 🔴 RED | holder:Martiini | 48.5 | category_specialist:crypto | 300 | 343 | 43% (39%) | -7.4% | 3357.6h | `0x3b6fd06a595d71c70afb3f44414be1c11304340b` |
| 65 | 🔴 RED | holder:Ronaldo2100 | 48.5 | longshot_fader | 300 | 163 | 1% (0%) | -21.5% | 430.0h | `0x71ca04d689bc38c5e4dcda8a4d743f279c5a3501` |
| 66 | 🔴 RED | holder:BeN | 48.4 | longshot_fader | 300 | 321 | 8% (6%) | -8.2% | 435.6h | `0x668d85d791049bf0100e557a72c7ed4dc97297d2` |
| 67 | 🔴 RED | holder:LiquidatedDege | 48.3 | general_trader | 300 | 465 | 0% (0%) | -27.8% | 85.9h | `0xc7e53ac4a7c76d6df8b794de2e7d0794265d2d3a` |
| 68 | 🔴 RED | holder:John3501 | 48.3 | longshot_fader | 300 | 91 | 1% (0%) | -5.4% | 320.6h | `0x08628ebc448f97450825e14ed3a79f45e5a6c7aa` |
| 69 | 🔴 RED | holder:zc1time | 48.2 | category_specialist:crypto | 300 | 117 | 7% (4%) | -14.6% | 1232.1h | `0x0ef62d386dcbcfe432ef732ee6efbe4a5696b8e3` |
| 70 | ⚫ BLACK | holder:ydexzsnskh | 48.2 | insider_suspected | 169 | 1 | 100% (27%) | -0.8% | 780.0h | `0x5b9d9a69972a0e0a4469e86c4e27029883468f2d` |
| 71 | 🔴 RED | lb-profit-1d:strike123 | 48.1 | general_trader | 300 | 128 | 3% (1%) | -41.4% | 7.4h | `0xf284ad6d607f777f34bc643cea587c33a886b9f9` |
| 72 | 🔴 RED | holder:SamuraiBlue | 48.1 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 1757.7h | `0xf2916e7366f2caf579b12bc6e3e7d145d0ad2cf2` |
| 73 | 🔴 RED | holder:Rrrrffff | 48.1 | longshot_fader | 1 | 0 | 0% (0%) | +0.0% | 972.4h | `0x81ef8cb9f75921beda5a0a6cd3c5c508ac6347f7` |
| 74 | 🔴 RED | holder:patrickreiss | 48.1 | category_specialist:politics | 79 | 0 | 0% (0%) | -4.0% | 318.9h | `0xcd3c9ec99edd66005879d26ecc37e72bc761a801` |
| 75 | 🔴 RED | holder:uponlyvibes | 48.1 | category_specialist:sports | 9 | 0 | 0% (0%) | +0.0% | 2449.4h | `0x99abd14fb1b179b1c5647a5762156b7ceeb77bd2` |
| 76 | 🔴 RED | lb-volume-7d:0xd8dA6BF26964 | 48.0 | general_trader | 300 | 37 | 32% (21%) | -0.7% | 0.7h | `0x8a98109fb0f1d87d9bfcb4486ba3587b95c51b92` |
| 77 | 🔴 RED | holder:0x6C9eFDdac30f | 48.0 | longshot_fader | 3 | 0 | 0% (0%) | -0.1% | 842.2h | `0x6c9efddac30fcb2c2f0934e1db3828937894e3e6` |
| 78 | 🔴 RED | holder:elPolloLoco | 48.0 | longshot_fader | 300 | 485 | 7% (6%) | -17.1% | 190.1h | `0xa2f1fecf1cc7db65a46588f764b6691533052d22` |
| 79 | 🔴 RED | holder:awawa124 | 48.0 | longshot_fader | 115 | 0 | 0% (0%) | -0.1% | 3073.1h | `0x7bcc3fa6be58607526c236301afc6b8b9921dae0` |
| 80 | 🔴 RED | holder:bau7 | 47.9 | longshot_fader | 300 | 0 | 0% (0%) | -4.0% | 42.2h | `0xf9a23d70c3429c582dce8737fc7d818f9044a79a` |
| 81 | 🔴 RED | holder:Basic123 | 47.9 | longshot_fader | 218 | 0 | 0% (0%) | -0.1% | 792.4h | `0x21ff4c3391d81c10a21eb6fe74ab262a5aae3b60` |
| 82 | 🔴 RED | holder:0x879d999541ea | 47.9 | category_specialist:weather | 300 | 92 | 0% (0%) | -13.3% | 4.6h | `0x879d999541ea4b50b7c237092cfc2b5f8a1fb501` |
| 83 | 🔴 RED | holder:Sean821 | 47.9 | longshot_fader | 1 | 0 | 0% (0%) | -0.1% | 100.1h | `0x4ac2767e50cc9f79a1a1fb162efa9e833d6a45c3` |
| 84 | 🔴 RED | holder:theprofit67 | 47.9 | longshot_fader | 2 | 0 | 0% (0%) | -0.1% | 337.0h | `0xd4753215d8e02c100854cbd368e367015cdcd3c0` |
| 85 | 🔴 RED | holder:kardamonchik88 | 47.9 | favorite_collector | 21 | 0 | 0% (0%) | -0.1% | 95.9h | `0x3d0b07845badccb0c8956e69c9a12994d8a6550e` |
| 86 | 🔴 RED | holder:BabyGroot | 47.8 | longshot_collector | 300 | 34 | 59% (45%) | -0.2% | 3.4h | `0xbefa95c276ee8ef6ff3ef43d1c1c454f52bc300d` |
| 87 | 🔴 RED | holder:0xa2dCcd83971D | 47.8 | longshot_fader | 300 | 0 | 0% (0%) | -0.6% | 433.4h | `0xa2dccd83971d56fb4e7ce45c491a968b29a249f9` |
| 88 | 🔴 RED | holder:Maanimo | 47.8 | category_specialist:sports | 300 | 442 | 0% (0%) | -46.7% | 10.5h | `0xe962dfbaed113be79c38e122e67a431231a9663a` |
| 89 | 🔴 RED | lb-volume-7d:asjabaasj | 47.7 | longshot_fader | 300 | 0 | 0% (0%) | +0.0% | 1.1h | `0xa7a8c1fd4bfff08ea30214efa7efaf75d7c6580c` |
| 90 | 🔴 RED | holder:memik | 47.7 | general_trader | 71 | 0 | 0% (0%) | -3.8% | 1216.5h | `0xef3f187deb8fc603d17fe524cfc4a06b84c69560` |
| 91 | 🔴 RED | holder:0x8EDEC839A0B2 | 47.7 | longshot_fader | 1 | 0 | 0% (0%) | -0.2% | 1184.0h | `0x8edec839a0b2848bd651d74c9cde13604c615ab8` |
| 92 | 🔴 RED | holder:0x859D08C50098 | 47.7 | general_trader | 300 | 385 | 0% (0%) | -39.7% | 157.9h | `0x859d08c500981d447a1168f510fd5df9c0663cec` |
| 93 | 🔴 RED | holder:huzpdpgpas | 47.7 | favorite_collector | 257 | 0 | 0% (0%) | -0.1% | 54.0h | `0xf3f7a7ea7d1cd7b8a2d1be66123efe2473dfecb3` |
| 94 | 🔴 RED | holder:redvinny | 47.6 | general_trader | 300 | 238 | 0% (0%) | -69.0% | 2.1h | `0x56c9fbdeccf198f1f5ad95ace39b24f5f7fb0d9e` |
| 95 | 🔴 RED | holder:wodnsdl | 47.6 | longshot_fader | 48 | 0 | 0% (0%) | -0.3% | 386.8h | `0x2a1a96973257559ec00ed7374e20c427dfefc549` |
| 96 | 🔴 RED | holder:touzhu | 47.6 | longshot_fader | 262 | 0 | 0% (0%) | -0.4% | 2448.5h | `0x2afc9bcbbfce9470181ee7a3dfc1f68dbd1eecd9` |
| 97 | 🔴 RED | holder:aff3 | 47.6 | longshot_fader | 300 | 0 | 0% (0%) | +0.1% | 90.9h | `0xe52c0a1327a12edc7bd54ea6f37ce00a4ca96924` |
| 98 | 🔴 RED | holder:DenzelZW | 47.6 | longshot_fader | 2 | 0 | 0% (0%) | -0.1% | 36.6h | `0x694680bbf6a881a836705098a87045169fa713da` |
| 99 | 🔴 RED | holder:synthwavetradi | 47.6 | longshot_fader | 300 | 14 | 29% (14%) | -0.0% | 42.0h | `0x9629a08c47920ac531e01bfec40182fab629b148` |
| 100 | 🔴 RED | holder:stormwww | 47.5 | longshot_fader | 3 | 0 | 0% (0%) | -0.5% | 1141.0h | `0xed2b092ba85a2f182584348932c53b33e9a22bb9` |
| 101 | 🔴 RED | holder:interstellaar | 47.5 | category_specialist:politics | 300 | 1 | 100% (27%) | -4.0% | 54.0h | `0x2d27e4d20f3b8a2ee3bc861d9b83752f338676d8` |
| 102 | 🔴 RED | holder:junipero | 47.5 | longshot_fader | 300 | 0 | 0% (0%) | -1.7% | 111.7h | `0x79797067582d11012e70acfc5a2e8b332580202f` |
| 103 | 🔴 RED | btc-bot-A | 47.4 | category_specialist:crypto | 300 | 0 | 0% (0%) | -1.9% | 33.9h | `0xf705fa045201391d9632b7f3cde06a5e24453ca7` |
| 104 | 🔴 RED | holder:TimeTraveler | 47.4 | longshot_fader | 300 | 433 | 18% (15%) | -2.3% | 23.2h | `0x51fd8f0358cc9e8a1ee5f87a0c7e3b07ed634272` |
| 105 | 🔴 RED | holder:naiiiiii | 47.4 | longshot_fader | 300 | 138 | 4% (2%) | -3.4% | 2.9h | `0x70d94a4ff67ed919a8480885cf0808afefe7a684` |
| 106 | 🔴 RED | holder:ballena | 47.4 | general_trader | 300 | 0 | 0% (0%) | -14.6% | 1765.5h | `0xcfc51c0a1a5a78845127d9d9dcb1236f700dc7cf` |
| 107 | 🔴 RED | lb-profit-30d:Pestle | 47.3 | longshot_fader | 300 | 22 | 0% (0%) | -0.8% | 213.5h | `0x241f846866c2de4fb67cdb0ca6b963d85e56ef50` |
| 108 | 🔴 RED | holder:Tradejarod | 47.3 | longshot_fader | 38 | 5 | 0% (0%) | -3.7% | 469.6h | `0xa04ef304ef09a770b0c61fd14d17147d3ca55a24` |
| 109 | 🔴 RED | holder:io-cane | 47.2 | longshot_fader | 300 | 0 | 0% (0%) | -0.0% | 44.7h | `0xf16640ce7cb59d7b38ca397652a5d296c6d0fb37` |
| 110 | 🔴 RED | holder:roushie | 47.2 | longshot_fader | 300 | 0 | 0% (0%) | -0.2% | 927.6h | `0x5357cf7202881f02ac8dcd9e19dc27456e8f3a0d` |
| 111 | 🔴 RED | 0xheavy888 | 47.1 | general_trader | 300 | 103 | 18% (12%) | -17.2% | 0.5h | `0xec981ed70ae69c5cbcac08c1ba063e734f6bafcd` |
| 112 | 🔴 RED | lb-profit-30d:0x2a2C53bD278c | 47.0 | general_trader | 300 | 454 | 7% (6%) | -28.3% | 83.2h | `0x2a2c53bd278c04da9962fcf96490e17f3dfb9bc1` |
| 113 | 🔴 RED | holder:ug88923 | 47.0 | longshot_fader | 45 | 0 | 0% (0%) | -0.3% | 264.3h | `0x4ae7d4b245aa765793d1d06c42ea5cbcc46a68d2` |
| 114 | 🔴 RED | holder:0xcaEad14f3588 | 47.0 | longshot_fader | 69 | 0 | 0% (0%) | -0.8% | 1053.8h | `0xcaead14f35888c5abfa093b62810af66a3e792cb` |
| 115 | 🔴 RED | holder:0x10cE6837F579 | 47.0 | longshot_fader | 18 | 0 | 0% (0%) | -0.3% | 175.9h | `0x10ce6837f5798eda77a5a17979dc540b7f24fe1f` |
| 116 | 🔴 RED | holder:jpmpower | 47.0 | longshot_fader | 300 | 0 | 0% (0%) | -0.1% | 260.6h | `0x31aea02baa8907646bc69e3787807b8898a44b60` |
| 117 | 🔴 RED | lb-profit-7d:0x2c335066FE58 | 46.9 | midprice_market_maker | 300 | 187 | 5% (3%) | -40.2% | 4.9h | `0x2c335066fe58fe9237c3d3dc7b275c2a034a0563` |
| 118 | 🔴 RED | holder:Etanol | 46.9 | longshot_fader | 300 | 0 | 0% (0%) | -2.8% | 160.3h | `0xd399ba186f89721f79e0a72bfa6c9babd2e13f46` |
| 119 | 🔴 RED | holder:Dernrt | 46.9 | longshot_fader | 92 | 0 | 0% (0%) | -0.2% | 1114.3h | `0xd5e64977e3e6e800e60f10a2821abac395821f0e` |
| 120 | 🔴 RED | holder:Anne666 | 46.9 | longshot_collector | 300 | 26 | 85% (70%) | +0.1% | 7.6h | `0x08730443345e11c078c5b2597ce3c0f06af609e8` |
| 121 | 🔴 RED | holder:wolfipohn | 46.8 | longshot_fader | 65 | 0 | 0% (0%) | -4.2% | 2333.2h | `0x4a241edd284adcd479678babc3a196c87a7898a7` |
| 122 | 🔴 RED | holder:juanporco | 46.8 | longshot_collector | 300 | 2 | 100% (42%) | -2.5% | 1585.3h | `0xce845c6892bcc6d256ab419e7803e5ff2e969e2b` |
| 123 | 🔴 RED | holder:Turtle892 | 46.8 | longshot_fader | 300 | 44 | 0% (0%) | -7.4% | 381.0h | `0xe574b4bf69386301fa2759bc4c39c0fc6f83832a` |
| 124 | 🔴 RED | holder:khalikof | 46.8 | longshot_fader | 300 | 0 | 0% (0%) | -0.3% | 671.3h | `0x3c32adc2fca14ae5afc36081f16262bc516d15bf` |
| 125 | 🔴 RED | holder:omoi0i0 | 46.7 | category_specialist:sports | 300 | 484 | 2% (1%) | -25.9% | 45.6h | `0xb3cfe7615d64db8dfa743a1b1a2b976911460ebd` |
| 126 | 🔴 RED | lb-profit-1d:Countryside | 46.6 | category_specialist:sports | 300 | 459 | 0% (0%) | -37.5% | 1.4h | `0xbddf61af533ff524d27154e589d2d7a81510c684` |
| 127 | 🔴 RED | lb-volume-7d:therighteousdo | 46.6 | midprice_market_maker | 300 | 143 | 6% (3%) | -46.9% | 0.0h | `0x3fd9a838ded6eb832baab3ccbcb5e934e3871ef0` |
| 128 | 🔴 RED | holder:nayoup | 46.6 | longshot_fader | 132 | 0 | 0% (0%) | -0.5% | 2693.6h | `0x735fc56d49eb06246caa34c0f367c9e889620e5b` |
| 129 | 🔴 RED | holder:0x052dc9B0E70d | 46.6 | longshot_fader | 21 | 2 | 0% (0%) | -1.4% | 9.3h | `0x052dc9b0e70d75691a7e37d561331d323571b892` |
| 130 | 🔴 RED | holder:degen22 | 46.6 | longshot_fader | 17 | 3 | 0% (0%) | -1.7% | 3912.4h | `0x09ed04911cd66d1954a8cf747d2f9a856c8276ca` |
| 131 | 🔴 RED | holder:SammySledge | 46.4 | category_specialist:sports | 300 | 372 | 0% (0%) | -44.0% | 7.7h | `0xafbacaeeda63f31202759eff7f8126e49adfe61b` |
| 132 | 🔴 RED | holder:SweetChariot | 46.4 | favorite_collector | 300 | 3 | 100% (53%) | -2.8% | 60.9h | `0x562bc8068347268d9a69b8dd464d00eed0f9dc09` |
| 133 | 🔴 RED | holder:Thethiagoshow | 46.3 | general_trader | 300 | 42 | 5% (2%) | -41.1% | 22.9h | `0x319fae12252753985892dd2b949ad124eb77500b` |
| 134 | 🔴 RED | holder:TheReturnOfDar | 46.3 | general_trader | 300 | 104 | 9% (5%) | -16.9% | 38.5h | `0x3a8aa345d5db7ec5138298c8c4f4540259be7699` |
| 135 | 🔴 RED | holder:0xdFaa6c5baf68 | 46.3 | longshot_fader | 94 | 15 | 7% (2%) | -0.4% | 1571.4h | `0xdfaa6c5baf681d131e1f900b21a3d57656be05e8` |
| 136 | 🔴 RED | holder:StudyPredictio | 46.3 | general_trader | 300 | 115 | 6% (3%) | -14.1% | 9.5h | `0x33bcb6e9bd44be709122b2940c55e34f1a7e37dc` |
| 137 | 🔴 RED | holder:honreserektus | 46.3 | favorite_collector | 19 | 0 | 0% (0%) | -1.1% | 56.1h | `0xc69bc7a6994e3388bc8a89231564fc7370ec1134` |
| 138 | 🔴 RED | holder:0x740159EcEd2A | 46.2 | longshot_fader | 40 | 0 | 0% (0%) | -0.4% | 139.5h | `0x740159eced2aaf9edcb7fac8a0b31d18c0f847a5` |
| 139 | 🔴 RED | holder:KamAlla | 46.1 | longshot_fader | 300 | 0 | 0% (0%) | -0.1% | 176.6h | `0x362ea6c4dbafffe5df6a3cc6f8f4029547238983` |
| 140 | 🔴 RED | holder:0xb1b30231 | 46.0 | longshot_collector | 300 | 3 | 100% (53%) | -0.5% | 248.1h | `0xb1b3023167b5ced7538225e98e19da557616a386` |
| 141 | 🔴 RED | holder:IB1191 | 46.0 | longshot_fader | 8 | 0 | 0% (0%) | -4.0% | 3113.4h | `0x039bbd2c8bbb4397552009a5690571b81a1b86f7` |
| 142 | 🔴 RED | holder:helloeveryone | 46.0 | general_trader | 300 | 17 | 41% (24%) | -4.2% | 28.8h | `0xc9e3208526a3554342652c26bec1ba2c230993f2` |
| 143 | 🔴 RED | holder:Q96s3kwozynxpa | 45.9 | category_specialist:politics | 300 | 2 | 0% (0%) | +0.3% | 3.2h | `0x2663daca3cecf3767ca1c3b126002a8578a8ed1f` |
| 144 | 🔴 RED | holder:0xc6174a742B29 | 45.9 | general_trader | 300 | 0 | 0% (0%) | -2.3% | 1430.0h | `0xc6174a742b2926f00e683828019cef708ff9cd8e` |
| 145 | 🔴 RED | holder:rivermarkets | 45.9 | longshot_fader | 300 | 191 | 8% (5%) | -14.6% | 151.5h | `0x1223987eb4bf8564a932f43e3cec9f28b5ced424` |
| 146 | 🔴 RED | holder:ddalkkak | 45.9 | longshot_fader | 300 | 94 | 2% (1%) | -11.2% | 724.2h | `0x16bd7cc71f6da1e77d1d8255677abc75b9bae288` |
| 147 | 🔴 RED | holder:Tw1n999 | 45.8 | longshot_fader | 300 | 199 | 10% (7%) | -4.7% | 10.8h | `0xcbba64cddd05171925ffd05d8f8abd38c83fdbff` |
| 148 | 🔴 RED | holder:knmrobert | 45.8 | category_specialist:weather | 300 | 50 | 0% (0%) | -14.4% | 7.3h | `0x7c1c3a3e97c81f9235fc24c2811c7218ff5a0b5f` |
| 149 | 🔴 RED | lb-profit-7d:swisstony | 45.7 | hft_uncopyable | 300 | 308 | 72% (68%) | -0.0% | 0.3h | `0x204f72f35326db932158cba6adff0b9a1da95e14` |
| 150 | 🔴 RED | holder:DapperChapper | 45.6 | longshot_fader | 300 | 2 | 0% (0%) | -0.3% | 11.9h | `0xf8ccb567e89c3240359217ebd0b5b5fe7fce5a82` |
| 151 | 🔴 RED | holder:majorL | 45.5 | longshot_fader | 300 | 157 | 1% (0%) | -19.3% | 245.3h | `0xd5386df17edb2b5dd8e11076ebf35e06858f317c` |
| 152 | 🔴 RED | holder:gloriafoster | 45.4 | category_specialist:sports | 300 | 186 | 2% (1%) | -23.4% | 0.8h | `0x5d189e816b4149be00977c1a3c8840374aec4972` |
| 153 | 🔴 RED | holder:2026gogogo | 45.4 | category_specialist:crypto | 300 | 175 | 0% (0%) | -34.8% | 200.2h | `0x87ecc34aa4c597190f61859603ddb6be14ea0777` |
| 154 | 🔴 RED | holder:minnisj | 45.4 | general_trader | 300 | 3 | 33% (8%) | -17.5% | 268.8h | `0x0c9eb97737c40b4dab9c3fe08ad5f7198233352a` |
| 155 | 🔴 RED | lb-profit-1d:FullPicks1 | 45.2 | category_specialist:sports | 259 | 1 | 100% (27%) | +0.0% | 0.0h | `0x9b1e0334569aa1768a07705a859686aad58e82c9` |
| 156 | 🔴 RED | lb-volume-7d:Dafu0715 | 45.2 | favorite_collector | 300 | 0 | 0% (0%) | -5.3% | 32.2h | `0x93511d72d294f1478739bc38f578bf0306fd9e4d` |
| 157 | 🔴 RED | holder:foodenjoyer | 45.2 | general_trader | 300 | 4 | 0% (0%) | -3.3% | 183.2h | `0x7b02b2bac2a30ed5e40b7094e734f4c3dc2a4991` |
| 158 | 🔴 RED | holder:Kolba | 45.1 | longshot_fader | 24 | 0 | 0% (0%) | -1.2% | 3808.3h | `0xb805a4ff8a382798c5fa5d717290df41927251fb` |
| 159 | 🔴 RED | holder:FranckM | 45.1 | longshot_fader | 203 | 5 | 0% (0%) | -22.6% | 1794.0h | `0x632c0a4ecb15df0a370e106f147bace74c0b00a4` |
| 160 | 🔴 RED | holder:btctohigh | 45.1 | favorite_collector | 45 | 0 | 0% (0%) | -8.0% | 822.4h | `0xee44112c72e9e9bae6fa4135de67956e38e31f54` |
| 161 | 🔴 RED | lb-profit-30d:RN1 | 45.0 | general_trader | 300 | 490 | 21% (18%) | -16.4% | 0.6h | `0x2005d16a84ceefa912d4e380cd32e7ff827875ea` |
| 162 | 🔴 RED | holder:Belgaron | 45.0 | favorite_collector | 300 | 12 | 75% (51%) | -0.5% | 153.5h | `0x6c104a31c105ab2573a42e0f178f961e4496df5c` |
| 163 | 🔴 RED | holder:Zaratustra | 44.9 | general_trader | 300 | 3 | 100% (53%) | -5.5% | 46.6h | `0x7818687f1c2cda416877ab68d18d2c9c25f9d185` |
| 164 | 🔴 RED | holder:butterbrot | 44.9 | longshot_collector | 300 | 2 | 100% (42%) | -1.1% | 49.1h | `0x70ad3c12fa92a97e1c387ab594e645d940a3f1df` |
| 165 | 🔴 RED | holder:kuxs | 44.9 | longshot_fader | 300 | 1 | 0% (0%) | -12.3% | 1770.4h | `0x4f7bdee22a435493dd4c06cca077a75fe9eb03e0` |
| 166 | 🔴 RED | holder:Blaskinho | 44.8 | longshot_fader | 300 | 0 | 0% (0%) | -3.3% | 16.0h | `0xd458d05a966ca3e6f6acdbf2a87c3e03f71bb521` |
| 167 | 🔴 RED | holder:nx693 | 44.8 | longshot_fader | 300 | 0 | 0% (0%) | -2.5% | 3528.7h | `0x2f14a4b3a260a8a0db488175c317d474d9f6b2fa` |
| 168 | 🔴 RED | holder:Gucky-Gu45 | 44.8 | longshot_fader | 300 | 262 | 14% (11%) | -1.5% | 4.1h | `0xe613b515bd46b1585a8b137a4d291d9b80bd540e` |
| 169 | 🔴 RED | holder:0x92423247 | 44.8 | longshot_fader | 74 | 0 | 0% (0%) | -2.0% | 1109.7h | `0x9242324787a68ce1cb7ccdd848a88eb8e74f7065` |
| 170 | 🔴 RED | YatSen | 44.7 | general_trader | 300 | 60 | 3% (1%) | -32.1% | 434.1h | `0x5bffcf561bcae83af680ad600cb99f1184d6ffbe` |
| 171 | 🔴 RED | lb-profit-1d:Sassy-Bucket | 44.7 | category_specialist:sports | 300 | 51 | 4% (1%) | -50.8% | 1.5h | `0x4bff30af91642dc7d2b19a8664378fe55c45fc26` |
| 172 | 🔴 RED | holder:nvvn | 44.7 | longshot_fader | 300 | 2 | 0% (0%) | -2.1% | 14.9h | `0xd355b7dc3d83658eeb6701dc88ec80522278f69c` |
| 173 | 🔴 RED | holder:elkmonkey | 44.6 | category_specialist:sports | 300 | 0 | 0% (0%) | +0.6% | 624.8h | `0xead152b855effa6b5b5837f53b24c0756830c76a` |
| 174 | 🔴 RED | holder:KoloMuani | 44.6 | general_trader | 300 | 0 | 0% (0%) | -4.7% | 182.2h | `0xd396dd666a021f1d62121a407c7449ee7e084991` |
| 175 | 🔴 RED | holder:musicmang | 44.5 | general_trader | 57 | 3 | 0% (0%) | -22.4% | 1906.1h | `0xdd9cb05e6709a57441ad04e59cd1e88690062a50` |
| 176 | 🔴 RED | holder:50-Pence | 44.4 | longshot_fader | 300 | 132 | 5% (3%) | -8.6% | 0.0h | `0x9478e0b0db650ac66ca3a2c9f6ed68ebca4863f5` |
| 177 | 🔴 RED | holder:lovedudley | 44.3 | longshot_fader | 300 | 2 | 0% (0%) | -0.8% | 6.7h | `0xfe9455e2cad5257b26547af62cbbfd75c8968a3d` |
| 178 | 🔴 RED | holder:staticllama | 44.3 | longshot_fader | 153 | 43 | 0% (0%) | -19.1% | 912.2h | `0x519794a3d72e8f18790b3089ac1e75cd74a40ce6` |
| 179 | 🔴 RED | holder:parkyun205 | 44.2 | category_specialist:sports | 300 | 66 | 0% (0%) | -43.3% | 24.6h | `0xa3922eaac3633b419f1d30831511275d0a941415` |
| 180 | 🔴 RED | lb-profit-7d:LaBradfordSmit | 44.1 | category_specialist:sports | 300 | 496 | 1% (1%) | -46.7% | 5.0h | `0x9495425feeb0c250accb89275c97587011b19a27` |
| 181 | 🔴 RED | lb-profit-7d:SemyonMarmelad | 44.1 | midprice_market_maker | 300 | 497 | 0% (0%) | -44.2% | 1.2h | `0x37e4728b3c4607fb2b3b205386bb1d1fb1a8c991` |
| 182 | 🔴 RED | holder:repsol | 44.0 | favorite_collector | 300 | 69 | 3% (1%) | -18.3% | 34.4h | `0x71afaf5a5992739e51fa11caadd52109091ac057` |
| 183 | 🔴 RED | holder:BroukPytlik | 44.0 | longshot_fader | 300 | 52 | 14% (8%) | -5.5% | 36.2h | `0x2936e1ec71c0ce15369908d3a83ec39481ca7be9` |
| 184 | 🔴 RED | holder:melchior1248 | 44.0 | longshot_fader | 300 | 249 | 16% (12%) | -1.4% | 0.2h | `0x36901eb0f21519cc9055662a6d2483e96da1e16f` |
| 185 | 🔴 RED | holder:NoobCapt | 44.0 | general_trader | 300 | 2 | 50% (12%) | -19.1% | 179.0h | `0xee30e5174dae1fd602ff1f06cc398bf67a1f9297` |
| 186 | 🔴 RED | holder:jingxingyhh | 43.9 | general_trader | 300 | 0 | 0% (0%) | -4.9% | 784.1h | `0x1bbed6ce05e6c1eba4ae94a223a47ab591bf776d` |
| 187 | 🔴 RED | holder:mingerr | 43.8 | general_trader | 300 | 1 | 0% (0%) | -22.1% | 260.8h | `0x233687fe4fbb772c2619c0f82a810d780d469e65` |
| 188 | ⚫ BLACK | holder:edenmoon | 43.8 | insider_suspected | 300 | 1 | 100% (27%) | -3.3% | 90.8h | `0x3d1ecf16942939b3603c2539a406514a40b504d0` |
| 189 | 🔴 RED | holder:Yelowyolo | 43.7 | category_specialist:politics | 300 | 23 | 52% (36%) | -0.2% | 5.8h | `0x8a815b830d6ecfb203abd27334ef8d621e2558b0` |
| 190 | 🔴 RED | holder:0x115A63c20827 | 43.7 | longshot_collector | 300 | 1 | 100% (27%) | -1.6% | 406.9h | `0x115a63c208278a576150176880f48f064c94e4a6` |
| 191 | 🔴 RED | holder:BruceZhao | 43.7 | favorite_collector | 36 | 2 | 0% (0%) | -19.6% | 2510.7h | `0xf73677e8ec74c0526bfd46c5770e6cfbd4f2c6e0` |
| 192 | 🔴 RED | holder:Stalker4 | 43.6 | longshot_fader | 274 | 0 | 0% (0%) | -0.3% | 264.6h | `0x3078921ae15f218a40660ecbecce8d7eac27ad0a` |
| 193 | 🔴 RED | holder:balldontlieee | 43.6 | general_trader | 300 | 14 | 71% (49%) | -4.8% | 71.2h | `0x966cd85371117d811aab6e6f2b98377433659b1a` |
| 194 | 🔴 RED | holder:wdp8819 | 43.4 | longshot_fader | 300 | 0 | 0% (0%) | -6.0% | 975.7h | `0xdece29298a4974b457272894a7663e89d81f4cd8` |
| 195 | 🔴 RED | holder:AppleTime67 | 43.4 | category_specialist:sports | 300 | 0 | 0% (0%) | -5.0% | 8.1h | `0xacb206b460a17382a734de8d931cc176307eb989` |
| 196 | 🔴 RED | holder:0x90Bf2dbB1ab3 | 43.3 | general_trader | 300 | 25 | 0% (0%) | -26.2% | 126.5h | `0x90bf2dbb1ab3b3c1bdd76d73848afcb19b5799eb` |
| 197 | 🔴 RED | holder:0xa5ef39c3 | 43.2 | unknown | 0 | 448 | 91% (88%) | +0.0% | 0.0h | `0xa5ef39c3d3e10d0b270233af41cac69796b12966` |
| 198 | 🔴 RED | holder:Yang-H | 43.2 | favorite_collector | 130 | 0 | 0% (0%) | -7.7% | 394.7h | `0x796134216a4928b0b90a44e2ecfa4a14585c1b1c` |
| 199 | 🔴 RED | holder:annuity972 | 43.1 | general_trader | 45 | 1 | 0% (0%) | -18.3% | 218.5h | `0x35f0f7dc346142f3084c9e6ccda2de8994ed000f` |
| 200 | 🔴 RED | lb-profit-7d:Mosley1 | 43.0 | category_specialist:sports | 300 | 51 | 0% (0%) | -42.7% | 17.1h | `0x5bec79df9add70a3892041ab1a5516b60f53b215` |
| 201 | 🔴 RED | holder:0x0DBDfBB4A708 | 43.0 | longshot_fader | 300 | 0 | 0% (0%) | -0.2% | 51.8h | `0x0dbdfbb4a708a51dc0c7c3b4a51ce702d41f2caa` |
| 202 | 🔴 RED | holder:alihanyer | 43.0 | general_trader | 300 | 5 | 0% (0%) | -6.3% | 43.1h | `0x1615086ace48440b0bc0da28a9dfc3d6e8208f2b` |
| 203 | 🔴 RED | holder:0xb8df15967183 | 43.0 | longshot_fader | 17 | 1 | 0% (0%) | -4.7% | 954.3h | `0xb8df159671834d9e8113f7905e93c7f0bfa04c92` |
| 204 | 🔴 RED | holder:rivaltwistino | 43.0 | longshot_fader | 3 | 2 | 0% (0%) | -4.4% | 565.9h | `0x6539e7ea8b9169bc56b719f058e151173195434a` |
| 205 | 🔴 RED | holder:0x7Ac67A1555c3 | 43.0 | longshot_fader | 289 | 1 | 0% (0%) | -4.2% | 214.8h | `0x7ac67a1555c361a47eafac1a138cc82c20ab92ca` |
| 206 | 🔴 RED | holder:jt7 | 42.9 | category_specialist:sports | 300 | 144 | 0% (0%) | -41.9% | 3.0h | `0x25cc572fae8d022da57a888597561908fd669297` |
| 207 | 🔴 RED | lb-profit-1d:EB99999 | 42.8 | general_trader | 300 | 1 | 0% (0%) | -26.8% | 143.2h | `0x5d0f03cf1243a3e21262d6cf844795afd9fff0ad` |
| 208 | 🔴 RED | holder:Kura1101 | 42.8 | longshot_fader | 24 | 1 | 0% (0%) | -13.4% | 718.3h | `0x599f72c605635944bbfafc4511aebd05ebe94ce3` |
| 209 | 🔴 RED | holder:FC3988 | 42.8 | general_trader | 300 | 3 | 67% (25%) | -12.4% | 32.7h | `0xdfda01f4b92cd096c6d04eed6eb2b069fd584fe6` |
| 210 | 🔴 RED | lb-volume-7d:ArmageddonRewa | 42.7 | general_trader | 300 | 55 | 26% (17%) | -5.2% | 1.8h | `0xc8ab97a9089a9ff7e6ef0688e6e591a066946418` |
| 211 | 🔴 RED | holder:0xDCD00E0eDE97 | 42.7 | longshot_fader | 15 | 2 | 0% (0%) | -7.6% | 1941.2h | `0xdcd00e0ede9719fd856f8d8a9a0e19a9a91453e5` |
| 212 | 🔴 RED | holder:tsihkodiives | 42.6 | longshot_fader | 300 | 358 | 4% (2%) | -8.3% | 43.4h | `0x6db983ff1cbc85249e64e6ccd101aaa613ba4ab5` |
| 213 | 🔴 RED | holder:RaphCrypto | 42.6 | longshot_collector | 300 | 20 | 40% (24%) | -1.3% | 90.5h | `0x187365dee1866e49c87fba10734375615d5d37b6` |
| 214 | 🔴 RED | holder:Likpa | 42.6 | longshot_fader | 145 | 36 | 0% (0%) | -29.2% | 231.9h | `0xaaa7529e2a4faf294e6a7cbfe2a26e17b722e4ad` |
| 215 | 🔴 RED | lb-profit-1d:0x53757615de1c | 42.5 | longshot_fader | 300 | 203 | 21% (17%) | -6.6% | 6.6h | `0x53757615de1c42b83f893b79d4241a009dc2aeea` |
| 216 | 🔴 RED | holder:tomorrownow | 42.5 | favorite_collector | 300 | 5 | 60% (27%) | -2.7% | 482.7h | `0x88fc342c7f7ad4ff9f1659c48e5bd03af19d900e` |
| 217 | 🔴 RED | holder:JustCrazy | 42.5 | longshot_fader | 300 | 104 | 10% (6%) | -2.5% | 0.5h | `0xc21ea96be762bb55041529af6e386e7c53b80215` |
| 218 | 🔴 RED | holder:avocato | 42.5 | general_trader | 300 | 2 | 0% (0%) | -13.7% | 360.0h | `0x088e9e9e70240212a1bae73269598fb0fc96bc56` |
| 219 | 🔴 RED | holder:funplayer- | 42.5 | general_trader | 300 | 28 | 7% (2%) | -9.0% | 92.5h | `0x373a949d617e60cbb25ca6df3f68018d573bf4c1` |
| 220 | 🔴 RED | holder:0x91EbA8C0D2F5 | 42.4 | longshot_fader | 300 | 24 | 0% (0%) | -9.7% | 5.6h | `0x91eba8c0d2f530bed0e19bb263377d4e82a8da31` |
| 221 | 🔴 RED | holder:alwaysfade | 42.4 | category_specialist:sports | 300 | 34 | 0% (0%) | -42.0% | 19.0h | `0xe5b70fd855af9258d9463992e4f1ed7987905ee3` |
| 222 | 🔴 RED | holder:ijkjijkj | 42.4 | favorite_collector | 38 | 2 | 0% (0%) | -32.4% | 1946.9h | `0xc4d45681cbec788c20ab549b11f1a9c30edca57a` |
| 223 | 🔴 RED | holder:GoldenAlpha168 | 42.3 | midprice_market_maker | 300 | 66 | 2% (0%) | -48.3% | 2.0h | `0x9ba8d25a054044bb66d0ca4e250a16dbfb64cdb3` |
| 224 | 🔴 RED | lb-profit-1d:bossoskil1 | 42.2 | category_specialist:sports | 300 | 397 | 0% (0%) | -41.8% | 0.0h | `0xa5ea13a81d2b7e8e424b182bdc1db08e756bd96a` |
| 225 | 🔴 RED | lb-profit-1d:BBPK | 42.2 | midprice_market_maker | 300 | 139 | 1% (0%) | -46.8% | 0.0h | `0xee0d153c17fe82b8866b484753b56a700ab457ab` |
| 226 | 🔴 RED | lb-volume-7d:0xe9076a87c5ed | 42.1 | longshot_fader | 300 | 88 | 28% (21%) | -2.6% | 0.1h | `0xe9076a87c5ed90ef16e6fe6529c943baeca0cff6` |
| 227 | 🔴 RED | lb-volume-7d:mooseborzoi | 42.1 | general_trader | 300 | 130 | 46% (39%) | -2.5% | 1.0h | `0x84cfffc3f16dcc353094de30d4a45226eccd2f63` |
| 228 | 🔴 RED | holder:thebug44 | 42.1 | category_specialist:sports | 300 | 1 | 100% (27%) | -11.6% | 621.5h | `0xde7cdcab3e0c5b0e8315da358e80c7d80a12c933` |
| 229 | 🔴 RED | holder:Masacrador | 42.1 | longshot_fader | 19 | 0 | 0% (0%) | -15.5% | 1230.1h | `0x4213826f1da5fbced01c5518e96daa079c67b8ca` |
| 230 | 🔴 RED | holder:bookaka | 42.0 | general_trader | 300 | 3 | 67% (25%) | -23.4% | 766.9h | `0x17115903b4ddc47c0b5997724749f09169f678ec` |
| 231 | 🔴 RED | holder:0x9F2E04C7795C | 42.0 | longshot_fader | 300 | 10 | 0% (0%) | -4.4% | 2542.6h | `0x9f2e04c7795c87631a26bb304d79217f873a9061` |
| 232 | 🔴 RED | holder:1Q84 | 41.9 | longshot_fader | 300 | 5 | 0% (0%) | -9.1% | 362.8h | `0x4c677b8da16c8308fbc15f6191a5369faee71075` |
| 233 | 🔴 RED | holder:PDJ88 | 41.8 | category_specialist:sports | 300 | 20 | 0% (0%) | -31.5% | 142.8h | `0x0e1d01759cfa75782134472a7af5963da9d50c53` |
| 234 | 🔴 RED | holder:0xB10bf118b2A3 | 41.8 | hft_uncopyable | 300 | 296 | 1% (1%) | -32.9% | 0.4h | `0xb10bf118b2a3c1cff0379a4134a82eb6d51e0b04` |
| 235 | 🔴 RED | holder:carmenqueasy | 41.8 | longshot_fader | 300 | 2 | 0% (0%) | -11.9% | 862.9h | `0x932051bfc39f59e72340634a430049982df7f7d7` |
| 236 | 🔴 RED | holder:Terry241129 | 41.8 | longshot_fader | 300 | 34 | 6% (2%) | -13.2% | 261.7h | `0x40416ec8233566b9e25cca160bba214b1cab6f52` |
| 237 | 🔴 RED | holder:0x71e11e0f | 41.8 | general_trader | 300 | 67 | 6% (3%) | -14.2% | 34.0h | `0x71e11e0fc20a2adf27026fbf8674b38f8ff945f0` |
| 238 | 🔴 RED | holder:12edhuwadf | 41.8 | general_trader | 75 | 0 | 0% (0%) | -5.8% | 2109.9h | `0x1db044f4c39182852f5e0300751036fe02458c60` |
| 239 | 🔴 RED | holder:test124566 | 41.7 | category_specialist:sports | 300 | 93 | 4% (2%) | -38.7% | 0.0h | `0x16b1f68da281f346fa9ff7a46e9d55826abe968a` |
| 240 | 🔴 RED | holder:happylifeman | 41.7 | general_trader | 43 | 0 | 0% (0%) | -5.8% | 198.4h | `0xf19191b814d9ee30bc8c325850c6b254464079bb` |
| 241 | 🔴 RED | holder:0xe09F33DB14f1 | 41.6 | longshot_fader | 20 | 2 | 0% (0%) | -11.9% | 150.6h | `0xe09f33db14f14e1bc1a6577b48d54a6cd9183561` |
| 242 | 🔴 RED | holder:OhneScharf | 41.5 | general_trader | 300 | 30 | 0% (0%) | -40.7% | 422.5h | `0xd2770343da54f1a2ed7305dbf83eeefa4a8b73fe` |
| 243 | 🔴 RED | holder:Melqui | 41.4 | favorite_collector | 300 | 3 | 67% (25%) | -1.7% | 78.3h | `0x3e0a8847c74b98a0d865e24ae399604ddf67b9cc` |
| 244 | 🔴 RED | holder:docdog | 41.4 | general_trader | 300 | 3 | 0% (0%) | -31.6% | 972.2h | `0xf575a0ab9d64291df311845820d97b4f69bfb53a` |
| 245 | 🔴 RED | holder:Tenebrus7 | 41.3 | general_trader | 300 | 176 | 20% (16%) | -13.9% | 4.5h | `0xa8c63f775ddbbe66b56614191747def3021444e8` |
| 246 | 🔴 RED | holder:justdoit0 | 41.3 | general_trader | 82 | 1 | 0% (0%) | -40.5% | 714.3h | `0xe9de6cbbda8a7ef721aef9f998c0be4d680e215b` |
| 247 | 🔴 RED | holder:qqq89 | 41.2 | category_specialist:sports | 300 | 43 | 0% (0%) | -25.1% | 13.3h | `0x575a227b3d9369b06a4aeffb3ab820b407f3bba6` |
| 248 | 🔴 RED | holder:Gl4d | 41.2 | general_trader | 300 | 55 | 9% (4%) | -17.1% | 16.7h | `0x1e3a86ef98030e7e0519e127d8178e9b45389e14` |
| 249 | 🔴 RED | holder:fritzphantom12 | 41.2 | longshot_fader | 300 | 2 | 0% (0%) | -31.5% | 134.8h | `0x88e50e592d50d07bbf9738015f6f05a3ce8a66b2` |
| 250 | 🔴 RED | holder:Doppelpack | 41.2 | favorite_collector | 300 | 6 | 0% (0%) | -7.3% | 732.0h | `0xf2562bd76f9debf1aa51659f9aa40c3c60119728` |
| 251 | 🔴 RED | holder:P1kaso | 41.2 | general_trader | 300 | 46 | 15% (8%) | -24.5% | 422.1h | `0x4aefed77846f1b884bcbfb9e63acb351c2be9337` |
| 252 | 🔴 RED | holder:definiteeel | 41.1 | longshot_fader | 300 | 0 | 0% (0%) | -0.3% | 0.0h | `0x7d7da331d36fecd10b1ef8fea24898c0d8d23e9c` |
| 253 | 🔴 RED | holder:0x3bb4C822D035 | 41.0 | longshot_fader | 300 | 24 | 4% (1%) | -4.2% | 70.5h | `0x3bb4c822d035392c4579b117410697ec6e1ef4c6` |
| 254 | 🔴 RED | holder:Annica-opencla | 41.0 | general_trader | 300 | 487 | 1% (0%) | -30.4% | 0.6h | `0x6bb5f2b0fbe2430328ee7b21369f9c0aa7bca518` |
| 255 | 🔴 RED | holder:0x10B30364936B | 41.0 | general_trader | 300 | 0 | 0% (0%) | -14.1% | 976.9h | `0x10b30364936b03d26b3fd01a63d1f991454b40d4` |
| 256 | 🔴 RED | holder:CornelJxJ | 40.9 | longshot_fader | 97 | 2 | 0% (0%) | -15.0% | 749.5h | `0xc395b6a171dbf0958e1f76af0e5e235aa391c64b` |
| 257 | 🔴 RED | holder:EABIUAERUNGDD | 40.9 | general_trader | 300 | 24 | 4% (1%) | -31.3% | 134.2h | `0x3ec30fc6e9eba32c557dd8f6188b815faee70cf1` |
| 258 | 🔴 RED | holder:nugget-cinder | 40.9 | longshot_fader | 300 | 2 | 0% (0%) | -7.2% | 73.6h | `0x792243f8fbaeec4a6e60aa518088535807a5ef61` |
| 259 | 🔴 RED | holder:0xA916bFFd830C | 40.8 | longshot_fader | 87 | 5 | 20% (5%) | -23.6% | 2017.5h | `0xa916bffd830cba9530dc6fdcd2cdc8a691491022` |
| 260 | 🔴 RED | holder:gorovi | 40.8 | favorite_collector | 300 | 23 | 4% (1%) | -48.3% | 225.6h | `0x1de92e091804c709f5e06bf1d132f946e673831d` |
| 261 | ⚫ BLACK | holder:volokolasik333 | 40.8 | insider_suspected | 10 | 1 | 100% (27%) | -6.5% | 19.9h | `0x756868aadfb4c6c1e56691a6fb8112286adddaf0` |
| 262 | 🔴 RED | holder:alwayslatetoth | 40.7 | longshot_fader | 300 | 2 | 0% (0%) | -4.3% | 27.0h | `0xb687f00464e33934f5d591f224e71c3559ecaee5` |
| 263 | 🔴 RED | holder:Jdhdhduu | 40.7 | category_specialist:sports | 300 | 3 | 0% (0%) | -15.8% | 240.2h | `0xdd92232bcdfbbac04132b3cbacbf32c2e5b16b2a` |
| 264 | 🔴 RED | holder:ybabyshow | 40.7 | general_trader | 300 | 34 | 0% (0%) | -48.5% | 753.0h | `0x1fc2afeeef93802db725f3546230465f454f5dbb` |
| 265 | 🔴 RED | holder:300PS | 40.6 | general_trader | 300 | 3 | 67% (25%) | -6.0% | 2.5h | `0x8f41129e43ebfbfe6075d0804f3b2bb763b3260e` |
| 266 | 🔴 RED | holder:mikelmoreno | 40.6 | longshot_fader | 300 | 0 | 0% (0%) | -8.9% | 599.4h | `0x8101b9dedd1af262b2cb0a64f278d65695bbe7be` |
| 267 | 🔴 RED | holder:gzezaeazeaze | 40.5 | longshot_fader | 300 | 1 | 0% (0%) | -23.8% | 17.3h | `0x5a57a93b8d6b6500117fb24fba6dec922af59299` |
| 268 | 🔴 RED | holder:icanseeitall | 40.5 | general_trader | 300 | 20 | 5% (1%) | -40.6% | 48.0h | `0xbce543209b599a2384ea78f30c4968474fcd02f1` |
| 269 | 🔴 RED | lb-profit-30d:Oddn | 40.4 | longshot_fader | 300 | 33 | 0% (0%) | -2.2% | 471.4h | `0xa53c26443fb636d8ae31ac24f62fc1d5ef8f67a5` |
| 270 | 🔴 RED | holder:OverDueJam | 40.3 | general_trader | 300 | 40 | 8% (3%) | -39.3% | 8.4h | `0x078ea5b2830eaab20c73f11bcca98bd5a4023ebd` |
| 271 | 🔴 RED | holder:dingaaling | 40.3 | favorite_collector | 22 | 1 | 0% (0%) | -21.7% | 1060.8h | `0xa146e43c70bb667d8ea1c08a1c5708b010fe88a4` |
| 272 | 🔴 RED | lb-volume-7d:GoalLineGhost | 40.2 | hft_uncopyable | 300 | 498 | 38% (34%) | -13.9% | 0.0h | `0x0346afae2603313d2bbee96b628536c8cbe352a5` |
| 273 | 🔴 RED | holder:FarmerGambler | 40.2 | longshot_fader | 300 | 0 | 0% (0%) | -0.8% | 0.0h | `0x4fbbf05fd317e2a68733d80e673b7aeffe074cbc` |
| 274 | 🔴 RED | holder:0x81ad90fe | 40.2 | longshot_fader | 300 | 1 | 0% (0%) | -27.0% | 262.1h | `0x81ad90fe856d6e61e73c8a0a3cab131d63f654c9` |
| 275 | 🔴 RED | holder:fantasici | 40.2 | general_trader | 300 | 10 | 0% (0%) | -52.5% | 965.6h | `0x9af768b815cb422bdcb37cd050e67ca286fb02a6` |
| 276 | 🔴 RED | holder:politics | 40.1 | longshot_fader | 14 | 4 | 0% (0%) | -30.5% | 93.5h | `0x917b3de3741bdec895670a718f9869f626f44df4` |
| 277 | 🔴 RED | holder:sssherra | 40.1 | longshot_collector | 300 | 1 | 100% (27%) | -21.5% | 24.2h | `0xee3ecc39c41e8a6b5399b1cd1b03d72f5271ebb5` |
| 278 | 🔴 RED | holder:Zptml | 40.1 | favorite_collector | 187 | 4 | 0% (0%) | -15.5% | 2419.6h | `0xecb98ff2542d9c57ec36aa3ecad3734b9e295a12` |
| 279 | 🔴 RED | holder:Blackred | 40.1 | longshot_fader | 300 | 12 | 0% (0%) | -6.2% | 232.6h | `0xde7ed2253d8da0b623e026b0e5ef55f4ca91396b` |
| 280 | 🔴 RED | holder:StudentMoney | 40.1 | general_trader | 300 | 60 | 2% (0%) | -39.3% | 127.9h | `0xfb5148fc7223630e0967dbfa8cd920d83ab4742d` |
| 281 | 🔴 RED | holder:simiank777 | 40.0 | general_trader | 300 | 4 | 50% (18%) | -1.9% | 154.9h | `0xefa3ba00c7495a9b4b2b46aa0d21a8023e8ed08b` |
| 282 | 🔴 RED | holder:kingxg | 40.0 | general_trader | 35 | 4 | 0% (0%) | -70.7% | 1566.8h | `0x82fad94d62962c894eaf0b8f9fbfa9516b646805` |
| 283 | 🔴 RED | holder:kjsgdhkjsdfh | 40.0 | general_trader | 113 | 5 | 0% (0%) | -56.3% | 432.1h | `0xc24676916e5befa774dc74b7654c8abd9f9b14c6` |
| 284 | ⚫ BLACK | holder:0xa82038eb | 39.9 | insider_suspected | 300 | 1 | 100% (27%) | -9.9% | 427.5h | `0xa82038ebbe638d53466a1d504d65f827402cba10` |
| 285 | 🔴 RED | holder:VesterBot | 39.9 | longshot_fader | 300 | 1 | 0% (0%) | -37.9% | 8.9h | `0xb00ac22c7a7ad5659bf624570a29181b1f08c58c` |
| 286 | 🔴 RED | holder:0x0b4543fa | 39.8 | general_trader | 300 | 0 | 0% (0%) | -10.2% | 1426.2h | `0x0b4543fa7b6b6261b88f4d913c774a205f56db48` |
| 287 | 🔴 RED | holder:HDGB | 39.8 | longshot_fader | 300 | 18 | 0% (0%) | -1.4% | 51.2h | `0x2e3ea056400d81c42e2ce26ef25fda4ec5caabea` |
| 288 | 🔴 RED | holder:Shmuel31 | 39.8 | general_trader | 92 | 8 | 0% (0%) | -37.1% | 689.6h | `0xc112cc01e598b429cb276f7785d62aec2cdf47b0` |
| 289 | 🔴 RED | holder:BafanaBafana | 39.6 | favorite_collector | 300 | 8 | 12% (3%) | -10.4% | 1703.9h | `0xf72cb9e1ffe0e51da6e747555174cf81a7b9eeb7` |
| 290 | 🔴 RED | holder:ZRGyoyo | 39.6 | general_trader | 300 | 3 | 0% (0%) | -40.2% | 677.5h | `0x1d749b198ea0d5136b21fc128fba38bc419c96eb` |
| 291 | 🔴 RED | holder:timeflybird | 39.6 | favorite_collector | 33 | 1 | 0% (0%) | -123.0% | 798.2h | `0x82388fc29564155dceb631c1bbb4c6674321ca37` |
| 292 | 🔴 RED | holder:growthwizard | 39.5 | longshot_fader | 22 | 4 | 0% (0%) | -13.0% | 157.6h | `0xb7213693631d70e6acfc0b867362577473a924f0` |
| 293 | 🔴 RED | holder:xiaohui998 | 39.5 | midprice_market_maker | 300 | 318 | 2% (1%) | -47.6% | 5.3h | `0x72361923300983fc1ba06dc5798e1082917aea53` |
| 294 | 🔴 RED | holder:0x8AFe29281315 | 39.4 | longshot_fader | 8 | 1 | 0% (0%) | -12.6% | 2203.0h | `0x8afe2928131558a60e018c947dded0a72fa05687` |
| 295 | 🔴 RED | holder:long1982 | 39.3 | midprice_market_maker | 300 | 359 | 2% (2%) | -47.9% | 3.7h | `0xfb1388292ea54f8541efdd18c417a51b59075946` |
| 296 | 🔴 RED | holder:gamblito | 39.2 | general_trader | 300 | 5 | 40% (14%) | -6.8% | 65.7h | `0x6452eee1d08be21886bafcc4cc41ef4bb53130a1` |
| 297 | 🔴 RED | holder:jonjon1986 | 39.1 | general_trader | 147 | 0 | 0% (0%) | -13.9% | 1235.6h | `0x343999a9d134cb8c6299138cc4d034472ffb22a1` |
| 298 | 🔴 RED | holder:Wsix | 39.1 | longshot_fader | 300 | 0 | 0% (0%) | -14.9% | 3421.2h | `0x56c5e91f0ff58e9015011a18b61509b68192dbcf` |
| 299 | 🔴 RED | holder:0x931cd2259731 | 39.1 | category_specialist:crypto | 300 | 202 | 0% (0%) | -17.8% | 0.0h | `0x931cd2259731f65ff31faa5233f446b9f50ca002` |
| 300 | 🔴 RED | holder:PapiBowser | 39.1 | category_specialist:sports | 27 | 5 | 0% (0%) | -33.3% | 690.5h | `0x4f3818cc7bca7c79680bb7fd3ac4108b7f3a2e85` |
| 301 | 🔴 RED | holder:bobbydrews | 39.1 | longshot_fader | 2 | 0 | 0% (0%) | -14.9% | 382.4h | `0x321af590ec54737ab8b3e49f6cfcbeee54c2cd4f` |
| 302 | 🔴 RED | holder:0x7D8d5d166816 | 39.1 | longshot_fader | 17 | 5 | 0% (0%) | -28.5% | 1702.0h | `0x7d8d5d16681608623baf323c291f17760bb1c4d6` |
| 303 | 🔴 RED | holder:gooup | 39.1 | general_trader | 168 | 4 | 0% (0%) | -36.2% | 1489.2h | `0x887fa95a8a0a2d54d345f7b01a25abb389344f97` |
| 304 | 🔴 RED | holder:UhhYeahh | 39.1 | longshot_fader | 100 | 13 | 15% (5%) | -22.6% | 3787.9h | `0x8ba0eb4bdab3f00224e144e8c4549db87b2df472` |
| 305 | 🔴 RED | holder:keepbelieving | 39.0 | longshot_fader | 20 | 1 | 0% (0%) | -33.1% | 497.9h | `0x0221e2d951c807a84c49fea10b5435466514ae79` |
| 306 | 🔴 RED | holder:numbernine | 39.0 | general_trader | 300 | 12 | 0% (0%) | -42.1% | 653.2h | `0xe7fd3fb56636dedc7dc481eca4b08d8ab5fb89de` |
| 307 | 🔴 RED | holder:f13x4ng31 | 39.0 | longshot_fader | 109 | 2 | 0% (0%) | -16.7% | 497.7h | `0x534aaf0db224940da10afa31377492ed4c170adb` |
| 308 | 🔴 RED | holder:Honma | 39.0 | longshot_fader | 250 | 4 | 0% (0%) | -11.2% | 535.1h | `0xba0b958b726c1d64829f294bb852fee274847278` |
| 309 | 🔴 RED | holder:0x1EA06EA7143D | 38.9 | category_specialist:sports | 300 | 3 | 0% (0%) | -89.6% | 861.5h | `0x1ea06ea7143d3b8e2431f9cab7011619c269950a` |
| 310 | 🔴 RED | holder:heybabyY | 38.9 | general_trader | 195 | 5 | 0% (0%) | -75.0% | 81.1h | `0x6a3e9d4c9222ae5592e85d650bd68d6b7c363d5b` |
| 311 | 🔴 RED | lb-profit-1d:AML | 38.8 | general_trader | 300 | 2 | 0% (0%) | -34.1% | 725.0h | `0xfd22b8843ae03a33a8a4c5e39ef1e5ff33ebad91` |
| 312 | 🔴 RED | holder:0x8ba27b7c | 38.8 | longshot_fader | 98 | 2 | 0% (0%) | -48.9% | 396.5h | `0x8ba27b7c9de2b6367f986bff5f9c8049204c1650` |
| 313 | 🔴 RED | holder:IBELIEVEBLUEDR | 38.8 | general_trader | 66 | 2 | 0% (0%) | -25.9% | 865.5h | `0xecabafef3798538e242c1be52500f73c42d8e8d4` |
| 314 | 🔴 RED | holder:0xd544F7dc1D20 | 38.8 | category_specialist:sports | 300 | 1 | 0% (0%) | -29.3% | 1763.0h | `0xd544f7dc1d20e5fe38574650dd80b10075111a81` |
| 315 | 🔴 RED | holder:0xfc4fd600 | 38.8 | general_trader | 18 | 1 | 0% (0%) | -104.0% | 2871.4h | `0xfc4fd6009b83ba96df12782802f184feb54c9bb0` |
| 316 | 🔴 RED | holder:madnesslol | 38.8 | category_specialist:sports | 300 | 2 | 0% (0%) | -40.5% | 1630.8h | `0x21af4efeccea267895a04fae557d025291f37186` |
| 317 | 🔴 RED | holder:DedY4il | 38.8 | category_specialist:sports | 31 | 2 | 0% (0%) | -68.3% | 1564.4h | `0x898f5c73e39f2e6659d01fd2e0a86aab0d3a3757` |
| 318 | 🔴 RED | holder:88877 | 38.8 | longshot_fader | 30 | 3 | 0% (0%) | -69.8% | 224.9h | `0x5d972b6f6012a2efaaab2a5a906c4814a3d83ad9` |
| 319 | 🔴 RED | holder:ocur | 38.8 | general_trader | 83 | 1 | 0% (0%) | -121.1% | 1872.7h | `0x6f85a34afc3e8e8d1229d24831d8ee632ab741b1` |
| 320 | 🔴 RED | holder:0x2d44eCac541F | 38.8 | category_specialist:sports | 55 | 2 | 0% (0%) | -62.6% | 1193.9h | `0x2d44ecac541f3c55577eb226f4d99409bb48a304` |
| 321 | 🔴 RED | btc-bot-B | 38.7 | category_specialist:crypto | 300 | 6 | 50% (22%) | -9.4% | 0.0h | `0x1979ae6b7e6534de9c4539d0c205e582ca637c9d` |
| 322 | 🔴 RED | holder:ab2.0 | 38.7 | general_trader | 21 | 1 | 0% (0%) | -47.9% | 563.9h | `0x76c9e892ec3dc2cb7977041cbfdc87596877628f` |
| 323 | 🔴 RED | holder:msm299 | 38.7 | longshot_fader | 300 | 1 | 0% (0%) | -58.1% | 229.0h | `0xa252a7efd9572128117c869fa4f064bed37edbf4` |
| 324 | 🔴 RED | holder:fanmt | 38.7 | longshot_fader | 300 | 4 | 0% (0%) | -3.1% | 94.3h | `0x6bad153a277a5c1892384d8ca28122b3f1704d53` |
| 325 | 🔴 RED | holder:chinamaxi | 38.7 | category_specialist:sports | 7 | 0 | 0% (0%) | -18.1% | 128.5h | `0x63f390d8493c0122bff4e6b0abc0b7b05d17458b` |
| 326 | 🔴 RED | holder:terry | 38.7 | general_trader | 116 | 1 | 0% (0%) | -29.8% | 991.9h | `0x74d0ad6af3f5bd19b790d5997a1914d0190cd8de` |
| 327 | 🔴 RED | holder:pmverygood | 38.7 | favorite_collector | 24 | 1 | 0% (0%) | -121.9% | 582.4h | `0x7f0fa269bb1be419a3e6a6e64b21e302d1b4cb20` |
| 328 | 🔴 RED | holder:0x9bee7488607B | 38.7 | longshot_fader | 56 | 3 | 33% (8%) | -2.9% | 12.6h | `0x9bee7488607b925214ac16ff1cd32210d33c74a6` |
| 329 | 🔴 RED | holder:kafaka | 38.7 | general_trader | 46 | 1 | 0% (0%) | -71.2% | 725.5h | `0xca6387642206994075b0fa089f1d1af2226d6f15` |
| 330 | 🔴 RED | holder:shmuel. | 38.7 | general_trader | 19 | 1 | 0% (0%) | -25.2% | 226.5h | `0xa5834d828304a8cec14d7e807442babec86ab44b` |
| 331 | 🔴 RED | holder:FootballFan98 | 38.6 | general_trader | 300 | 3 | 67% (25%) | -21.6% | 96.4h | `0xc31d0a0d63d760d72a1236d16beaa6a71c854ebe` |
| 332 | 🔴 RED | holder:DumbMoney2222 | 38.6 | category_specialist:sports | 300 | 1 | 0% (0%) | -19.4% | 56.5h | `0xcfcabcd88df9e0bebfc4347a86c4686e7cb78b3a` |
| 333 | 🔴 RED | holder:goodgmgn | 38.6 | general_trader | 19 | 0 | 0% (0%) | -73.2% | 523.1h | `0x7cfd5ec8c3b264d3fcf55783f6cdb279b9dbb94f` |
| 334 | 🔴 RED | holder:garsv | 38.5 | longshot_fader | 300 | 7 | 14% (3%) | -1.9% | 59.5h | `0xd2617031c8b5623ade5b28079d83982abf6bb663` |
| 335 | 🔴 RED | lb-profit-1d:aekghas | 38.4 | general_trader | 300 | 0 | 0% (0%) | -26.2% | 45.9h | `0xb2a3623364c33561d8312e1edb79eb941c798510` |
| 336 | 🔴 RED | holder:huatimus | 38.4 | favorite_collector | 300 | 12 | 33% (16%) | -20.2% | 2461.7h | `0x7a1849ac8a195e3fd479f81c0b3277ab5d0cd1c9` |
| 337 | 🔴 RED | holder:EHA | 38.2 | general_trader | 300 | 22 | 0% (0%) | -33.0% | 178.3h | `0x4bbe47831533d6eca88e2e602ee4e444aa72abc6` |
| 338 | 🔴 RED | holder:Markcoin10 | 38.2 | category_specialist:crypto | 125 | 23 | 4% (1%) | -17.3% | 272.9h | `0x85a2ef42b0030ffba5c015a15f91eb286ab3203c` |
| 339 | 🔴 RED | holder:inchbyinchbyin | 38.1 | general_trader | 300 | 1 | 0% (0%) | -107.5% | 18.6h | `0x47661b3073d6dd0130e61a5c5b6f00b6f8da0286` |
| 340 | 🔴 RED | holder:suohaSJB | 38.0 | longshot_fader | 300 | 4 | 0% (0%) | -20.4% | 63.1h | `0x81bc8f470d0a4281c1246fe2c10bf64088adfcfa` |
| 341 | 🔴 RED | holder:rtjuedr4y | 37.9 | category_specialist:sports | 216 | 30 | 0% (0%) | -60.9% | 1983.9h | `0x376219dc16381643ebfc499531e22dc7297324bf` |
| 342 | 🔴 RED | lb-profit-1d:bcda | 37.8 | category_specialist:sports | 300 | 8 | 62% (35%) | -28.0% | 0.2h | `0xb45a797faa52b0fd8adc56d30382022b7b12192c` |
| 343 | 🔴 RED | holder:PhilHawesLover | 37.8 | favorite_collector | 300 | 13 | 54% (32%) | -2.7% | 42.0h | `0x6b3a549080f043f5ac2433a30e5ce154c7782841` |
| 344 | 🔴 RED | holder:Jessica562 | 37.7 | general_trader | 300 | 3 | 0% (0%) | -25.2% | 98.7h | `0x8dd73d74b1210be2d5e171c9edd58aeebddfdd08` |
| 345 | 🔴 RED | holder:0xe0eE7CB6880b | 37.6 | general_trader | 106 | 2 | 0% (0%) | -22.2% | 7.5h | `0xe0ee7cb6880b02bd192ea12af64cc6134d65b7f8` |
| 346 | 🔴 RED | holder:janglinjack | 37.6 | category_specialist:sports | 300 | 18 | 0% (0%) | -34.1% | 760.9h | `0x9b292d6d18c1f9837af7edfc9b897d8a0fe88373` |
| 347 | 🔴 RED | holder:Haradwaith | 37.4 | longshot_fader | 300 | 41 | 24% (15%) | -3.0% | 0.5h | `0x21ffd2b7a212a6f277ed3eca1a9f8efcbca90d71` |
| 348 | 🔴 RED | holder:333777 | 37.3 | longshot_fader | 300 | 10 | 0% (0%) | -17.7% | 816.2h | `0x02c50d55157cd98a6ee515a380a86472d7038356` |
| 349 | 🔴 RED | holder:extractive-man | 37.3 | longshot_fader | 300 | 7 | 29% (10%) | -0.8% | 440.2h | `0xf9f207b77137caa79c6c4516abdef3133db45cba` |
| 350 | 🔴 RED | holder:Irboz-sama | 37.3 | general_trader | 300 | 23 | 61% (44%) | -8.5% | 282.8h | `0x9b0b60aa0a1df93202f996860342fd5607815e43` |
| 351 | 🔴 RED | holder:demon42 | 37.1 | longshot_fader | 209 | 18 | 6% (1%) | -21.6% | 2503.3h | `0x04c04a3c0bc826074b1272606566dd2db98f4f3d` |
| 352 | 🔴 RED | holder:FrancoMastuant | 37.1 | longshot_fader | 300 | 6 | 0% (0%) | -5.6% | 327.4h | `0x1fa04fe548fed271beb16f3bdd9d119bc2c3cac8` |
| 353 | 🔴 RED | lb-profit-1d:AdrianCronauer | 36.8 | general_trader | 300 | 9 | 56% (30%) | -12.2% | 12.3h | `0xf9c1190aa8184bcbe418e6f5321c53b0bfbc39e2` |
| 354 | 🔴 RED | holder:GoriIIa | 36.7 | longshot_fader | 300 | 1 | 0% (0%) | -25.0% | 110.8h | `0xfffadf38a520cd5a0035ff52d7fceb436a08864b` |
| 355 | 🔴 RED | holder:Woohx | 36.6 | longshot_collector | 300 | 2 | 50% (12%) | -13.1% | 122.5h | `0x60c1f86859f2724effffffd4cae4bb0259190438` |
| 356 | 🔴 RED | holder:ssalu | 36.6 | longshot_fader | 82 | 14 | 0% (0%) | -19.6% | 758.0h | `0xc6325d53416cfe31c8becc1919e3c73b4c456871` |
| 357 | 🔴 RED | lb-profit-30d:ferrariChampio | 36.5 | hft_uncopyable | 300 | 498 | 7% (6%) | -23.7% | 0.5h | `0xfe787d2da716d60e8acff57fb87eb13cd4d10319` |
| 358 | 🔴 RED | holder:Calvin3328 | 36.4 | longshot_fader | 300 | 15 | 0% (0%) | -9.0% | 506.4h | `0x38b09c9d19c75018afc3ff63b60a33f7d2d7dd47` |
| 359 | 🔴 RED | holder:LionYossi | 36.2 | longshot_fader | 63 | 15 | 0% (0%) | -8.5% | 880.9h | `0x8aae3838fbaaf7ee34a0f16754f26a0b2dac319c` |
| 360 | 🔴 RED | holder:pfing | 36.1 | general_trader | 300 | 21 | 0% (0%) | -42.2% | 1344.5h | `0xc5fa48b547b2fccc480e8699fc2b160d0cac5b59` |
| 361 | 🔴 RED | lb-volume-7d:Borntorun | 35.9 | category_specialist:sports | 300 | 2 | 0% (0%) | -67.1% | 0.0h | `0xd959b6925d3d3391a40c1a85dd3d8916ef16daf7` |
| 362 | 🔴 RED | lb-profit-7d:VPenguin | 35.8 | category_specialist:sports | 300 | 1 | 0% (0%) | -47.8% | 0.0h | `0xfbf3d501e88815464642d0e913f15379c3eeb218` |
| 363 | 🔴 RED | lb-profit-30d:JewishNinja | 35.8 | category_specialist:sports | 300 | 1 | 0% (0%) | -61.0% | 0.0h | `0xa380c504a480f591c7dfbf9944fac3994b9b21ff` |
| 364 | 🔴 RED | holder:joejoeno3 | 35.8 | longshot_collector | 300 | 2 | 50% (12%) | -7.9% | 975.1h | `0xfaa77ed88112b488f6e96c9168ddbfd06db18150` |
| 365 | 🔴 RED | holder:0x63a4F883F689 | 35.7 | longshot_fader | 300 | 12 | 8% (2%) | -4.1% | 6.4h | `0x63a4f883f6897df0eaff6318adb18f4b45d40091` |
| 366 | 🔴 RED | holder:1223111 | 35.7 | longshot_fader | 50 | 8 | 12% (3%) | -26.9% | 843.7h | `0xd54faddebed2b523bda7334e72bd84888664ec81` |
| 367 | 🔴 RED | holder:TradingWave | 35.6 | longshot_collector | 300 | 5 | 60% (27%) | -4.5% | 27.8h | `0xf49ce459b52f60b70ce0fe9aa6203e6bf90f9786` |
| 368 | 🔴 RED | holder:Emme1 | 35.6 | longshot_fader | 195 | 17 | 0% (0%) | -35.7% | 387.1h | `0xec570193a382465a94dec36c05a09e9061bde0ac` |
| 369 | 🔴 RED | holder:Asperatus | 35.5 | longshot_fader | 300 | 9 | 0% (0%) | -10.9% | 6.9h | `0x36a7e80b487b26eebce266da0640e33dd4651aea` |
| 370 | 🔴 RED | holder:mails123 | 35.5 | longshot_fader | 185 | 9 | 0% (0%) | -23.8% | 214.0h | `0xc828a4ebaa5dae5cc1e66a028256ed84efc7dbfa` |
| 371 | 🔴 RED | holder:tnl | 35.4 | general_trader | 300 | 34 | 24% (14%) | -10.4% | 27.2h | `0xb619ed5b378053f8309c307d2f7adf9c13665068` |
| 372 | 🔴 RED | holder:alexbrocan35 | 35.4 | general_trader | 300 | 15 | 0% (0%) | -38.7% | 156.3h | `0xb013a7a854ef42e64b471724346ebec0640c6b3a` |
| 373 | 🔴 RED | holder:albipastore15 | 35.4 | longshot_fader | 300 | 9 | 0% (0%) | -11.0% | 307.2h | `0x80f10b49029e33fde02ac9fb183b49c79d681093` |
| 374 | 🔴 RED | holder:ttomime | 35.3 | longshot_fader | 300 | 23 | 17% (8%) | -10.6% | 1984.5h | `0xd702c806ea9b89a4fd1b378e4e7a098305cfdaa9` |
| 375 | 🔴 RED | holder:grwr | 34.7 | category_specialist:crypto | 198 | 20 | 0% (0%) | -47.3% | 1918.5h | `0x3d531cffdf3fed2fc212f72ec6b5864e771e5e62` |
| 376 | 🔴 RED | holder:rembranny | 34.3 | general_trader | 58 | 10 | 0% (0%) | -33.4% | 1248.3h | `0xd567866524a7eb5dafc794b74ece370f19e9e10d` |
| 377 | 🔴 RED | holder:CaughtByRandom | 34.2 | longshot_fader | 137 | 19 | 0% (0%) | -14.6% | 40.6h | `0x67d27256f79f77380537f3fd41306e8353cc6ffb` |
| 378 | 🔴 RED | holder:sportsbettor22 | 34.0 | category_specialist:sports | 300 | 38 | 0% (0%) | -32.7% | 0.2h | `0x20e2d462eb96d6fe2c4c7d3fb99e1df17a93667f` |
| 379 | 🔴 RED | holder:zarboxyl | 33.9 | longshot_fader | 300 | 13 | 0% (0%) | -21.9% | 1842.4h | `0x59c7fd3c203ee9c6d5ee9a05863e80c2598f4ccc` |
| 380 | 🔴 RED | aenews2 | 33.7 | general_trader | 300 | 25 | 24% (13%) | -7.2% | 46.4h | `0x44c1dfe43260c94ed4f1d00de2e1f80fb113ebc1` |
| 381 | 🔴 RED | holder:0x4880b7b4 | 33.4 | hft_uncopyable | 300 | 2 | 0% (0%) | -8.9% | 0.0h | `0x4880b7b4c78526c1b0dceab2fbfd9c8888925626` |
| 382 | 🔴 RED | holder:EricForeman | 33.3 | longshot_fader | 300 | 22 | 0% (0%) | -20.9% | 27.3h | `0x2b3a389d1c5dc3802a2f539813d3f124f14d610a` |
| 383 | 🔴 RED | holder:sbimbg | 32.9 | general_trader | 300 | 44 | 9% (4%) | -23.6% | 1.9h | `0xf5198df69e13937a40d1c76d6f72d9aa067d906b` |
| 384 | 🔴 RED | holder:0x418D51e13d01 | 32.7 | category_specialist:sports | 300 | 6 | 0% (0%) | -56.5% | 55.7h | `0x418d51e13d019913bb027db22ecc723fe1ad88a3` |
| 385 | 🔴 RED | holder:BigOdds | 32.6 | midprice_market_maker | 300 | 9 | 22% (8%) | -28.8% | 0.0h | `0x49f962674be9d996b3cb356b4c2c2204cfee32b0` |
| 386 | 🔴 RED | lb-profit-7d:caicai888888 | 32.5 | midprice_market_maker | 300 | 24 | 0% (0%) | -41.8% | 1.6h | `0x2d7be5170a8026c18709eaea1027c7f12e8ce2ce` |
| 387 | 🔴 RED | holder:0x21a22c9e1d5E | 32.5 | general_trader | 111 | 13 | 8% (2%) | -34.5% | 51.1h | `0x21a22c9e1d5e3f92d680c49afad87f40bc055f83` |
| 388 | 🔴 RED | holder:TradingBear | 32.5 | longshot_fader | 111 | 8 | 0% (0%) | -12.9% | 229.2h | `0xb567608cc44dd0c2a083b3f9eea78e7d973e1575` |
| 389 | 🔴 RED | holder:NitroStock | 32.4 | longshot_fader | 300 | 12 | 8% (2%) | -27.8% | 114.1h | `0x34fe137193b3fbb12e61571d28fc056816d54a5b` |
| 390 | 🔴 RED | holder:plims | 32.2 | general_trader | 28 | 6 | 0% (0%) | -52.6% | 224.3h | `0xc6029e95294f3eb7e52dd3715def991b968aa32b` |
| 391 | 🔴 RED | holder:DavidTrezeguet | 32.1 | general_trader | 300 | 8 | 0% (0%) | -8.8% | 227.6h | `0xc88eb9ab98663254bff489c515f39f23b76bf3e1` |
| 392 | 🔴 RED | holder:GWinBets | 32.1 | longshot_fader | 55 | 9 | 11% (2%) | -15.8% | 4.5h | `0x66337ff6e514edac9fc91b4f435900cb394ef066` |
| 393 | 🔴 RED | lb-volume-7d:downtownfee | 32.0 | midprice_market_maker | 300 | 20 | 5% (1%) | -54.6% | 2.3h | `0xbee54d90051720e27921dc6874f02d646ffca636` |
| 394 | 🔴 RED | holder:alphatips.Chan | 32.0 | general_trader | 300 | 8 | 0% (0%) | -38.0% | 1265.0h | `0x2aa13994496b2c84268afff01687122de4abc691` |
| 395 | 🔴 RED | holder:lonewolfcapita | 31.9 | longshot_fader | 300 | 10 | 0% (0%) | -12.4% | 1226.5h | `0x4110ae59607b55a47d6f13d356e2dc4f90e01586` |
| 396 | 🔴 RED | holder:smacks97 | 31.8 | general_trader | 67 | 7 | 0% (0%) | -45.8% | 2813.7h | `0x55d201e619fdf5fb7191fd4e54402677ae57efda` |
| 397 | 🔴 RED | lb-profit-30d:beachboy4 | 31.7 | category_specialist:politics | 300 | 0 | 0% (0%) | -44.9% | 0.0h | `0xc2e7800b5af46e6093872b177b7a5e7f0563be51` |
| 398 | 🔴 RED | holder:solwizzo-onX | 31.5 | general_trader | 300 | 16 | 6% (1%) | -4.2% | 73.2h | `0xff165cf8eb75ee77933a7544d7cd600ccb2c7511` |
| 399 | 🔴 RED | holder:piratesfan1313 | 31.4 | category_specialist:sports | 300 | 13 | 23% (10%) | -6.7% | 20.9h | `0xf65506e2d5f55279d77bd67d3c80af6882ad7ea4` |
| 400 | 🔴 RED | holder:drew.eth | 31.1 | longshot_fader | 300 | 6 | 0% (0%) | -25.9% | 2670.7h | `0x5b30fdea8850761f614f3f0d6619b05d248029a4` |
| 401 | 🔴 RED | holder:TheEmprah | 31.0 | general_trader | 300 | 17 | 12% (4%) | -35.7% | 2154.4h | `0x4cb5ec560735efca23f76f2dd152b74bc6a9b536` |
| 402 | 🔴 RED | lb-profit-7d:mentionmarket | 29.7 | midprice_market_maker | 300 | 13 | 0% (0%) | -46.1% | 1.8h | `0xc3acf5878a03523d09a3ac859943445d7baeb964` |
| 403 | 🔴 RED | lb-profit-7d:ChloeT1 | 29.0 | hft_uncopyable | 300 | 14 | 0% (0%) | -52.2% | 0.1h | `0x9ac2536ed93f8fe8ce91d9662b03bcbb19ccbe3d` |
| 404 | 🔴 RED | holder:Guest1 | 28.9 | longshot_fader | 27 | 14 | 7% (2%) | -25.0% | 1333.1h | `0xf87444ae4a9b0d66d318eeee262ca29ad3007c71` |
| 405 | 🔴 RED | holder:Outsid3rTradin | 28.6 | general_trader | 300 | 7 | 14% (3%) | -15.4% | 78.1h | `0xf1ef8705e9f63c790c6fffd6329aea7011718cd6` |
| 406 | 🔴 RED | holder:restart77 | 27.5 | longshot_fader | 300 | 12 | 0% (0%) | -31.7% | 17.7h | `0xe40ea00e74059c76c0035c919ef6b99c3e25a94d` |
| 407 | 🔴 RED | lb-volume-7d:username123123 | 26.5 | category_specialist:crypto | 300 | 6 | 33% (12%) | -41.4% | 0.0h | `0xd950a1a89f3e61a7a9efc85a46e440ce58c15e86` |
| 408 | 🔴 RED | holder:videlake | 26.1 | general_trader | 300 | 17 | 12% (4%) | -14.2% | 19.4h | `0x6ae1575206e99751ff60ec5c0adcaad572bc1e7e` |
| 409 | 🔴 RED | holder:mostovaja | 21.3 | category_specialist:sports | 278 | 9 | 11% (2%) | -51.5% | 0.6h | `0x438e1f519cfe1474d19545c09aecf26cb75cc499` |

## Detail — Qualified Wallets

### thread-extract-2  🟡 YELLOW  (65.3/100)

- **Address**: `0x594edb9112f526fa6a80b8f858a6379c8a2c1c11`
- **Edge type**: `category_specialist:weather`
- **Sample**: 495 resolved / 300 total trades
- **PnL**: $+98,425 (realized $+145,238)
- **WinRate**: 71.9% (Wilson LB: 68.5%)
- **ROI**: avg +6.7% / LB +4.8%
- **Max DD**: 23.9%  |  **Top position**: 18% of PnL
- **Hold time**: median 2.5h  |  **Avg entry**: 0.10
- **Price regime**: 88% longshot / 2% mid / 5% favorite
- **Main category**: weather (95% concentration)
- **Sub-scores**: edge=67 sample=100 persist=30 anti-luck=37 risk=61 copy=75 indep=99

**Notes**:
- Edge not yet persistent across split-halves
- PnL concentrated (top position = 18%)

### holder:RITB123  🟡 YELLOW  (65.2/100)

- **Address**: `0x724db3c436dcc7b26fbe1ae0c0d6af538b588dea`
- **Edge type**: `category_specialist:crypto`
- **Sample**: 454 resolved / 300 total trades
- **PnL**: $+98,877 (realized $+204,232)
- **WinRate**: 60.1% (Wilson LB: 56.3%)
- **ROI**: avg +2.7% / LB +1.6%
- **Max DD**: 99.3%  |  **Top position**: 8% of PnL
- **Hold time**: median 1.5h  |  **Avg entry**: 0.15
- **Price regime**: 78% longshot / 8% mid / 2% favorite
- **Main category**: crypto (76% concentration)
- **Sub-scores**: edge=47 sample=100 persist=79 anti-luck=40 risk=40 copy=69 indep=97

**Notes**:
- PnL concentrated (top position = 8%)

### lb-profit-1d:arlanta  🟡 YELLOW  (56.9/100)

- **Address**: `0x1136368d7f6728e94ed14c532ab95a932f710c2e`
- **Edge type**: `category_specialist:sports`
- **Sample**: 15 resolved / 300 total trades
- **PnL**: $+78,847 (realized $+0)
- **WinRate**: 93.3% (Wilson LB: 74.9%)
- **ROI**: avg +15.6% / LB +5.7%
- **Max DD**: 0.8%  |  **Top position**: 58% of PnL
- **Hold time**: median 7.8h  |  **Avg entry**: 0.44
- **Price regime**: 12% longshot / 32% mid / 16% favorite
- **Main category**: sports (72% concentration)
- **Sub-scores**: edge=72 sample=18 persist=31 anti-luck=23 risk=99 copy=88 indep=94

**Notes**:
- Edge not yet persistent across split-halves
- Limited sample (15 resolved)
- PnL concentrated (top position = 58%)

### holder:Mike123455  🟡 YELLOW  (56.6/100)

- **Address**: `0xeee9d0cedb2b8d59069d76d9f39bf58c383df66f`
- **Edge type**: `longshot_fader`
- **Sample**: 93 resolved / 300 total trades
- **PnL**: $-688 (realized $+50)
- **WinRate**: 7.5% (Wilson LB: 4.1%)
- **ROI**: avg -2.0% / LB -3.0%
- **Max DD**: 0.0%  |  **Top position**: 4% of PnL
- **Hold time**: median 2032.4h  |  **Avg entry**: 0.07
- **Price regime**: 91% longshot / 3% mid / 0% favorite
- **Main category**: other (32% concentration)
- **Sub-scores**: edge=22 sample=100 persist=0 anti-luck=47 risk=100 copy=100 indep=90

**Notes**:
- Edge not yet persistent across split-halves
- PnL concentrated (top position = 4%)
- ROI lower bound -3.0% — edge not proven

### holder:aimforthebushe  🔴 RED  (56.5/100)

- **Address**: `0xbc26352dac6b2cc9274dae39f73269192caa15f9`
- **Edge type**: `longshot_fader`
- **Sample**: 0 resolved / 32 total trades
- **PnL**: $-1,769 (realized $-201)
- **WinRate**: 0.0% (Wilson LB: 0.0%)
- **ROI**: avg +0.4% / LB -0.3%
- **Max DD**: 0.0%  |  **Top position**: 36% of PnL
- **Hold time**: median 587.3h  |  **Avg entry**: 0.06
- **Price regime**: 100% longshot / 0% mid / 0% favorite
- **Main category**: other (89% concentration)
- **Sub-scores**: edge=36 sample=5 persist=50 anti-luck=90 risk=100 copy=99 indep=58

**Notes**:
- Insufficient sample: only 0 resolved positions
- ROI lower bound -0.3% — edge not proven

### holder:PoloBoloYolo  🔴 RED  (56.3/100)

- **Address**: `0x1ef09f92e5217e1b757b37ace873f915cb76e2d1`
- **Edge type**: `category_specialist:weather`
- **Sample**: 0 resolved / 300 total trades
- **PnL**: $-223 (realized $+0)
- **WinRate**: 0.0% (Wilson LB: 0.0%)
- **ROI**: avg +0.1% / LB -0.1%
- **Max DD**: 0.0%  |  **Top position**: 101% of PnL
- **Hold time**: median 27.9h  |  **Avg entry**: 0.83
- **Price regime**: 17% longshot / 0% mid / 83% favorite
- **Main category**: weather (83% concentration)
- **Sub-scores**: edge=37 sample=5 persist=50 anti-luck=65 risk=96 copy=95 indep=100

**Notes**:
- Insufficient sample: only 0 resolved positions
- ROI lower bound -0.1% — edge not proven

### holder:P-J  🔴 RED  (55.3/100)

- **Address**: `0xd498f2d1ae092dfc39088343f6d4e9219c7780ae`
- **Edge type**: `general_trader`
- **Sample**: 1 resolved / 300 total trades
- **PnL**: $+1,322 (realized $+1)
- **WinRate**: 0.0% (Wilson LB: 0.0%)
- **ROI**: avg +18.3% / LB +0.1%
- **Max DD**: 0.0%  |  **Top position**: 50% of PnL
- **Hold time**: median 1160.5h  |  **Avg entry**: 0.32
- **Price regime**: 22% longshot / 11% mid / 0% favorite
- **Main category**: other (67% concentration)
- **Sub-scores**: edge=38 sample=5 persist=50 anti-luck=52 risk=97 copy=100 indep=100

**Notes**:
- Insufficient sample: only 1 resolved positions
- ROI lower bound 0.1% — edge not proven

## Next steps

1. Re-run weekly to catch new wallets and detect edge decay on tracked ones
2. For 🟢 wallets, paper-mirror via PolyCop with 10% bankroll cap and monitor 30 days
3. For 🟡 wallets, watch for sample to grow past n=40 then re-evaluate
4. For ⚫ flags, DO NOT copy — insider edges legally toxic and don't persist after disclosure

## Links

- [[scan_smart_follower]] — Real-time entry detection on tracked wallets
- [[strategy_registry]] — Strategy classifications
- [[edge_research_tests]] — Validation framework