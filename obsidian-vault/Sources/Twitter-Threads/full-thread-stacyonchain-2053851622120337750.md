---
type: "twitter-thread"
source: "https://x.com/stacyonchain/status/2053851622120337750?s=20"
author: "stacyonchain"
status_id: "2053851622120337750"
status: "full_content_imported"
primary_family: "smart_money_wallet_tracking"
priority: "high"
relevance: "direct_edge"
tags: ["source/twitter", "polymarket", "research", "full-content"]
---
# Full Thread - stacyonchain - 2053851622120337750

## Source
https://x.com/stacyonchain/status/2053851622120337750?s=20

## Title
500 Smart Money Addresses on Polymarket for Copy Trading: An Analysis of the Best Traders

## Extraction Summary
- Relevance: `direct_edge`
- Primary family: `smart_money_wallet_tracking`
- Priority: `high`
- Families: `smart_money_wallet_tracking`, `news_latency`, `weather_event_discovery`

## Actionable Takeaways
- Rank wallets by out-of-sample hit rate, market category, entry timing, and drawdown, not headline PnL.
- Replay timestamped news events and measure time-to-midpoint-move with simulated execution latency.
- For each weather thread claim, replay forecast update times against market mid-price changes and spread.

## Hypotheses
### smart_money_wallet_tracking
- Thesis: Wallet tracking may identify repeatable market selection patterns, but direct copy trading is dangerous.
- Value type: `research_signal`
- Required data: `wallet trades`, `market metadata`, `entry timestamps`, `exit timestamps`, `PnL attribution`
- First test: Rank wallets by out-of-sample hit rate, market category, entry timing, and drawdown, not headline PnL.
- Risk: Copying delayed fills creates adverse selection; public wallet lists decay quickly.
- Priority: `medium`

### news_latency
- Thesis: News-to-price latency can create short windows where Polymarket reprices slower than credible external feeds.
- Value type: `latency_signal`
- Required data: `news timestamps`, `feed latency`, `orderbooks`, `trades`, `market mapping`
- First test: Replay timestamped news events and measure time-to-midpoint-move with simulated execution latency.
- Risk: Bad source quality, timestamp drift, or already-priced information can erase the edge.
- Priority: `high`

### weather_event_discovery
- Thesis: Weather markets can be found and repriced faster by mapping forecast updates to active Polymarket markets.
- Value type: `market_selection`
- Required data: `market metadata`, `weather API snapshots`, `forecast timestamps`, `orderbooks`, `trades`
- First test: For each weather thread claim, replay forecast update times against market mid-price changes and spread.
- Risk: Forecast source mismatch or ambiguous market wording can create false positives.
- Priority: `high`

## Evidence
- While most participants on Polymarket are trying to predict outcomes based on headlines, emotions, and speculation, a small group of addresses consistently approaches the market with precision and systematically captures the majority of profitable opportunities.
- I collected 500 wallets with the highest PnL, categorized them by trading behavior and market focus, and selected the ones that are genuinely worth tracking for copy trading.
- Below is a curated database of addresses you can use to monitor activity, analyze strategies, and identify patterns used by some of the platform’s most successful traders.

## Caveats
- Do not treat posted PnL, win rate, or screenshots as evidence until reproduced locally.

## Raw Thread
```text
While most participants on Polymarket are trying to predict outcomes based on headlines, emotions, and speculation, a small group of addresses consistently approaches the market with precision and systematically captures the majority of profitable opportunities.
I collected 500 wallets with the highest PnL, categorized them by trading behavior and market focus, and selected the ones that are genuinely worth tracking for copy trading. Below is a curated database of addresses you can use to monitor activity, analyze strategies, and identify patterns used by some of the platform’s most successful traders.
Before anything else: if you want to skip the reading and go straight to what we built - centpro.bot

Everything is there.  Real results. Real mechanics. Real video.
Now the list.
Polymarket Top-500 Wallets
Overall ranks #200–#700 · Last 30 days · Generated May 11, 2026
Sports
restart77 — +$50.7K
llllll…IIlI — +$50.3K
balldo…ieee — +$49.7K
sjhfccha — +$49.6K
KeF666 — +$49.1K
0x5234…6273 — +$48.7K
SolMoe — +$48.5K
strike123 — +$48.3K
frontrunnar — +$48.1K
Feromont — +$47.9K
rustin — +$47.9K
f3arless — +$46.3K
Paracellus — +$46.0K
0x5375…aeea — +$45.7K
.Sisyphus — +$45.4K
UCF-BI…-FAN — +$45.3K
ALWAYS…ROVE — +$44.9K
ic4cream — +$44.8K
sbimbg — +$44.7K
Tirdenchi — +$44.3K
linbeiele — +$44.3K
dudukos — +$43.1K
lovedudley — +$43.0K
meoooow — +$41.8K
0x418D…7961 — +$41.3K
ifpl — +$40.8K
chowfun — +$40.6K
AppleTime67 — +$40.0K
Partyarty91 — +$39.8K
iTitan — +$39.8K
Milo100 — +$39.1K
JWPREG…HLTV — +$38.5K
BookWarrior — +$37.8K
1922 — +$37.4K
Dogeco…aire — +$37.1K
111sf — +$36.9K
pilotbaby — +$36.8K
SDTrading — +$36.6K
middle…cean — +$36.6K
Eulhunter — +$36.5K
gardiner — +$36.5K
hansama31 — +$36.2K
ieuei31 — +$36.1K
rocroi — +$36.0K
YOURSOUL — +$36.0K
sushifish — +$35.9K
StakePilot — +$35.6K
goodman877 — +$35.5K
VeryLucky888 — +$34.6K
Bacc — +$34.6K
Joe-Biden — +$34.0K
KingVon99 — +$34.0K
0x4f2 — +$33.7K
Axis54 — +$33.6K
yupiiiiiiiii — +$33.4K
qsyqsyqsy — +$32.4K
kiviro — +$32.3K
retroa…urce — +$31.7K
473game — +$31.4K
SnGewg…aaa2 — +$31.4K
xxyyxxzz — +$31.2K
baoying8888 — +$31.0K
TJRTrades — +$30.8K
alexubet — +$30.6K
geiyecapixie — +$30.5K
NewTea…sed4 — +$30.5K
fkgggg…uria — +$30.1K
ccn023390 — +$29.9K
HorribleWork — +$29.9K
8a7sh2 — +$29.8K
chidor…ngan — +$29.8K
bambambole — +$29.4K
Nk9 — +$29.1K
gbbgxfb — +$28.8K
ramada…adam — +$28.5K
0x53eCc53E7 — +$28.4K
MaciBe…ng23 — +$28.4K
DOLLAR…NTER — +$27.8K
zhangwen1688 — +$27.6K
Ashley…ffer — +$27.0K
contrarycap — +$27.0K
3musketeers — +$27.0K
Ilovemywife — +$26.9K
gamble…2015 — +$26.9K
Blastoise1 — +$26.8K
steadysteady — +$26.7K
0xf559…7740 — +$26.7K
oieshfn345 — +$26.4K
valnech — +$26.3K
dudebro — +$25.8K
meG342…Czf1 — +$25.6K
menghuan388 — +$25.5K
yhii — +$25.4K
RevNorth — +$25.1K
Sjels — +$25.1K
0xD9E0…05f2 — +$25.0K
4qfrankie — +$24.8K
Lugh-do — +$24.4K
OA1 — +$24.3K
olegio — +$24.3K
kokony — +$24.2K
HowieRatner — +$23.9K
itsallupnow — +$23.9K
oresttetr — +$23.9K
neverr…gain — +$23.8K
long1982 — +$23.7K
qqi6699 — +$23.4K
fenglin5945 — +$23.4K
baws — +$23.4K
0xD3D — +$23.3K
WynnWaldorf — +$23.2K
Linda1972 — +$22.9K
0xff34…694b — +$22.6K
cumulus33 — +$22.5K
minji — +$22.5K
chenmocm — +$22.5K
001000…1100 — +$22.5K
Innova…nEdu — +$22.4K
0x85E8…6093 — +$22.3K
Gh0stTradez — +$22.2K
Kramer — +$22.1K
Gameth…-394 — +$22.0K
C63AMG — +$22.0K
n.magas — +$22.0K
pedroBala — +$22.0K
MartyMcFox — +$21.9K
0x6918…0027 — +$21.9K
LYnetLY — +$21.8K
L31szz…s1sa — +$21.8K
scubacat — +$21.7K
0x5b10…9314 — +$21.7K
0x228B…4872 — +$21.6K
csgod — +$21.5K
oilmoneyw — +$21.5K
Iamnob…body — +$21.5K
0x5986…7056 — +$21.2K
HDGB — +$21.2K
jackenand — +$21.2K
Wldntu…know — +$21.1K
Shori888 — +$20.8K
0x3020…4333 — +$20.6K
0x84d7…2055 — +$20.6K
Aceplus1 — +$20.5K
muusd — +$20.2K
TOWERCAPITAL — +$20.2K
Lester…mond — +$20.0K
BaronO…rone — +$19.8K
yajiSelene — +$19.8K
Zetalias — +$19.7K
0xa697…6031 — +$19.5K
riandro — +$19.3K
0x129e…8314 — +$19.0K
HeyIts…cle0 — +$18.9K
ewelmealt — +$18.9K
xytest — +$18.7K
0x8f91…00e7 — +$18.7K
0x82fF…4403 — +$18.7K
0x6982…4945 — +$18.7K
0xfb51…082d — +$18.6K
kaktus69 — +$18.6K
Juan12345678 — +$18.6K
DCAAA — +$18.6K
bbbbbb…bbbb — +$18.4K
aangelika — +$18.4K
Arturi…lito — +$18.4K
0xhj37…g443 — +$18.3K
agraw — +$18.3K
shoemanhere — +$18.2K
diceking — +$18.1K
0x8cbf…1636 — +$17.9K
fortuneking — +$17.8K
FC3988 — +$17.6K
wolfycoco — +$17.5K
JonDomino — +$17.5K
one8tyfive — +$17.4K
PRIMEboss — +$17.3K
0xE911…6286 — +$17.3K
evoi9 — +$17.2K
11owen — +$17.2K
0xB595…6105 — +$17.2K
Canadi…oose — +$17.2K
foooool — +$17.1K
0x35E9…1110 — +$17.1K
0x0352…3960 — +$17.1K
Blesse…adin — +$17.1K
k-maniac — +$17.1K
white-rabbit — +$16.8K
aurorapp — +$16.7K
254321758 — +$16.7K
2800freebz — +$16.6K
TrapCap — +$16.1K
loitterer — +$16.0K
lucio12z16 — +$15.9K
COLBY451 — +$15.9K
LadyLuckPLZ — +$15.9K
0x021C…0808 — +$15.8K
POKE1 — +$15.8K
Benedictat0r — +$15.7K
humpyninja — +$15.5K
0x9B2B…6689 — +$15.5K
sweetspea — +$15.4K
failstober — +$15.3K
cricketzero — +$15.2K
0xF290…5392 — +$15.1K
midwicket72 — +$15.0K
gilmar…i176 — +$15.0K
stakesroyale — +$14.9K
Obilic — +$14.9K
Kishorwho — +$14.8K
vananal0318 — +$14.8K
Notradecopy — +$14.8K
ViLco — +$14.7K
PrimeO…1987 — +$14.6K
fwed33 — +$14.5K
BEBE1 — +$14.5K
0x9D8a…1847 — +$14.4K
anon.1….123 — +$14.4K
HBAFlover98 — +$14.4K
RazorS…urns — +$14.4K
pateekk — +$14.3K
tmoneeey — +$14.3K
DrPufferfish — +$14.2K
0x5fD5…3931 — +$14.2K
haini — +$14.2K
iwillc…back — +$14.2K
prezzel — +$14.1K
machiavelia — +$14.1K
lebandito — +$14.1K
NiuBot — +$14.0K
Random…eBet — +$14.0K
0xf3ce…a57a — +$14.0K
torta.tech — +$14.0K
trashmon — +$14.0K
Zephyrpo1 — +$14.0K
greek404 — +$13.9K
secretlogic — +$13.9K
0xf668…3123 — +$13.7K
Gooooo…llll — +$13.7K
sdgdhf — +$13.6K
JuiceFarm — +$13.6K
mrgoated — +$13.6K
Sharkb….pro — +$13.6K
mrweed — +$13.6K
0x8a6C…8725 — +$13.5K
Zestwooda — +$13.3K
ohayog…imas — +$13.3K
Stickman22 — +$13.3K
blindsamsam — +$13.2K
Mrazi777 — +$13.2K
yelnata — +$13.2K
0xfC08…5274 — +$13.2K
leegunner — +$13.2K
risktale — +$13.1K
PikaCHU448 — +$13.1K
Dapper…pper — +$13.1K
12monkeys — +$13.1K
Maxcheche — +$13.0K
slimjoe — +$13.0K
Foreca…ion2 — +$13.0K
eoNs- — +$12.9K
0xbFe6…2816 — +$12.9K
888ball — +$12.9K
CruzJude — +$12.8K
Grizzl…Suck — +$12.8K
Politics
i18z — +$50.4K
StasPanda — +$47.9K
66601 — +$46.2K
krimut — +$45.6K
tervero — +$45.1K
nobles…lige — +$45.0K
tourists — +$44.9K
paspor — +$44.6K
Eatpraylove — +$44.0K
metsW — +$42.6K
operat…stle — +$42.1K
0xFc2F…7451 — +$41.9K
I0I0I0 — +$41.5K
azot — +$41.3K
makemo…2025 — +$40.8K
0x3b4e…8965 — +$40.4K
Hisokaaa — +$39.6K
djwcx — +$39.3K
mr.ozi — +$39.2K
marketside — +$38.2K
SaylorMoon — +$37.8K
NyetRisk — +$37.8K
M888 — +$36.9K
BigBoiBettin — +$35.6K
TheRet…Maul — +$35.5K
korda77 — +$34.3K
BobBiswas — +$33.5K
pup1 — +$31.3K
stupid22 — +$31.2K
immanuelcan — +$30.9K
pd.unique — +$30.8K
jocpolitic — +$29.9K
firebat — +$29.6K
bobe2.1 — +$29.4K
881112 — +$29.4K
ChikaBoomPow — +$29.3K
rebotsliaf — +$28.6K
2B9S — +$28.1K
TeamA — +$27.7K
bobe2 — +$27.6K
horiz0n — +$27.2K
WarriorPooh — +$26.7K
hose — +$26.3K
StoneMarble — +$26.2K
xopierhljkh — +$25.9K
FedWillWin — +$25.6K
Ubuntu…ding — +$25.5K
NeH — +$25.2K
Marks1000 — +$25.0K
Flammergod — +$25.0K
trying…here — +$24.6K
george6688 — +$24.3K
odifof — +$24.0K
Lelouc…ndia — +$23.0K
0x60AE…7106 — +$23.0K
0xa2dC…7503 — +$23.0K
Clicker1 — +$22.8K
chungguskhan — +$22.7K
Anjun — +$21.8K
ghfjnfgjkgk — +$21.1K
unknwnfnd — +$21.0K
Warren…fett — +$20.8K
0x3748…9622 — +$20.8K
0xe639…082a — +$19.8K
AishahSofey — +$19.8K
0xd103…1f12 — +$19.7K
Anoint…nect — +$19.6K
WCBT — +$19.4K
HerrieDavis — +$19.4K
Binotto — +$19.2K
misko1 — +$18.8K
NotBak…nzie — +$18.2K
random…unt7 — +$18.2K
Aeglos — +$17.9K
G.laila — +$17.9K
betwick — +$17.7K
AAVVAA — +$17.6K
minisobaby — +$17.6K
Kamika…n.ir — +$17.4K
Nikitka — +$16.7K
Tbhidk-1767 — +$16.5K
Cungly — +$16.4K
Foresi…acle — +$16.2K
CongMingLabs — +$16.1K
eightp…uins — +$16.0K
aoidwa — +$15.9K
eCash — +$15.8K
vovatoxic — +$15.8K
just.s…2026 — +$15.8K
shuanyang — +$15.7K
Skdel — +$15.7K
Bertap…mous — +$15.7K
ligmaaaaa — +$15.5K
Clear-…idor — +$15.5K
onekey09 — +$15.4K
Jsram — +$15.1K
SitsToPee — +$15.1K
Llalalala — +$15.0K
HysonB — +$14.8K
basedd — +$14.8K
TROLOLO2000 — +$14.6K
Wickier — +$14.6K
MissWo…rfun — +$14.6K
0xFc9D…4643 — +$14.6K
pugdev — +$14.4K
turo — +$14.3K
lissartter — +$14.3K
Kickstand7 — +$14.1K
0xa3FF…3842 — +$14.0K
0xEC1F…5030 — +$13.8K
10thave — +$13.7K
JJo — +$13.7K
MEPP — +$13.6K
0xB886…7794 — +$13.4K
PMPD — +$13.2K
GrokEnjoyer — +$13.2K
patma — +$13.1K
0x8B4b…3952 — +$12.9K
chainoracle — +$12.9K
Crypto
justdance — +$50.7K
Marketing101 — +$49.5K
xuanxuan008 — +$49.4K
SamGTree — +$48.6K
nsh91qaz — +$45.7K
collab…grok — +$43.5K
wkknndoqmz — +$43.4K
0xF5c1…0662 — +$43.2K
CramSc…ub01 — +$38.2K
0x75cc…3ce1 — +$37.5K
glueeater — +$37.0K
WangXingYu — +$36.4K
0xf705…3ca7 — +$33.4K
0x7543…2446 — +$32.5K
Mantronix — +$30.6K
0x3516…5332 — +$30.1K
0x8d88…icai — +$30.1K
0x0377…6534 — +$28.8K
0xE910…3959 — +$28.3K
bnewkoq — +$27.3K
orange-frog — +$26.7K
0xa689…3559 — +$25.9K
0x11a2…5569 — +$24.6K
swrfsg…7744 — +$24.5K
0xba67…1530 — +$24.0K
0xea68…b0a8 — +$23.7K
rwo — +$23.7K
miqbdhlq — +$23.7K
SDWWWS — +$23.2K
0xB27B…1020 — +$23.0K
0x424e…1025 — +$22.9K
N0wh3r…1ght — +$22.4K
snqwqkozmqoc — +$22.2K
oquabqy9713 — +$21.5K
not-gO…nKeR — +$21.3K
shy-bl…rock — +$21.0K
kingof…lips — +$20.3K
0x9F5f…5528 — +$20.1K
winnerz100 — +$19.7K
a4sucks — +$19.6K
0xdf0D…8733 — +$19.3K
0x33d33 — +$18.7K
0x3A84…84D4 — +$18.4K
OhioOhio — +$18.4K
0xjfie…49g9 — +$18.3K
UUDDLRLR — +$18.2K
0xb305…2623 — +$18.1K
osto — +$17.4K
0x652c…1729 — +$17.3K
GGFAFSGH874 — +$17.3K
JetFadil — +$16.5K
0x04b6…9789 — +$16.4K
0x931c…4859 — +$16.1K
0x48AC…4189 — +$16.1K
Sharky6999 — +$16.1K
Parz1vaI — +$15.9K
0xf2db…8fa5 — +$15.3K
Winter…land — +$15.2K
0xD1C5…0956 — +$15.1K
0xe1D6…D907 — +$15.0K
0xd901…0675 — +$14.5K
nndrekop — +$14.2K
purple…tree — +$13.9K
fffsasda988 — +$13.6K
0x5e2b…9101 — +$13.4K
gabigol — +$13.4K
Hyperlong — +$13.2K
0xd32C…4838 — +$13.2K
ethhte — +$13.2K
7eC338B — +$13.1K
pimax1 — +$12.9K
ADAto10 — +$12.9K
ddfs654 — +$12.8K
Marioy — +$12.7K
Economics
Siziriv — +$33.9K
foodenjoyer — +$27.7K
0x11789 — +$26.0K
polywally — +$17.6K
wokerj…eper — +$15.6K
d1k21 — +$14.8K
Finance
yxj425 — +$48.3K
0x1E82…8755 — +$42.5K
pikach…lace — +$39.5K
Hauchn — +$38.6K
0x72a0…c059 — +$36.2K
bin8888 — +$31.0K
C03B — +$29.7K
supers…sbro — +$25.8K
qwerrrty — +$22.3K
0x38D8…0207 — +$17.4K
0xfree-money — +$16.9K
0xFB59…8742 — +$15.5K
ZorroD…Vega — +$15.2K
NiFengFanPan — +$15.1K
bitcoinmafia — +$14.3K
CamelUp — +$13.6K
fitmk — +$13.2K
Tee1000 — +$13.1K
Culture
Valued — +$48.6K
bipbipbop — +$20.3K
deina — +$18.3K
0x0dcb…a7b4 — +$14.4K
ellio8989 — +$12.9K
Tech
Dragontree — +$17.6K
Weather
0xa5Ed…4fE9 — +$27.3K
aHjCz — +$19.9K
Other
Bagwell306 — +$47.9K
0x05E3…8641 — +$30.6K
Afornson — +$27.6K
Sunshi…mile — +$27.4K
MilesY — +$25.6K
02- — +$16.4K
0xE16D…0592 — +$16.3K
ColdW — +$15.3K
LadyLuck2 — +$14.5K
Wimmerr — +$13.9K
0x880b…1268 — +$12.9K
YXT7777777 — +$12.8K
```
