# VISION

> **Gradimo AI Alpha Engine čija je svrha pronaći, potvrditi i dugoročno iskorištavati statistički održiv edge na stvarnim financijskim tržištima.**
AI Alpha Engine is the quantitative intelligence core that will ultimately power the fully autonomous AI Alpha Trading Agent.

---

# AI Alpha Engine

## Misija

Izgraditi inteligentan sustav koji samostalno istražuje financijska tržišta, pronalazi statistički održiv edge, upravlja rizikom, uči iz vlastitih rezultata i kontinuirano poboljšava kvalitetu svojih odluka.

Konačni cilj nije razviti još jedan trading softver.

Konačni cilj je razviti proizvod koji može djelovati na stvarnim financijskim tržištima i dugoročno ostvarivati održiv edge.

---

# Naša filozofija

Ne gradimo demo.

Ne gradimo školski projekt.

Ne gradimo softver s najviše indikatora.

Ne gradimo najljepše grafove.

Gradimo inteligentan sustav koji svakoga dana postavlja jedno pitanje:

> **"Gdje danas postoji stvarna statistička prednost?"**

Ako postoji edge, sustav djeluje.

Ako edge ne postoji, sustav čeka.

Disciplina je važnija od aktivnosti.

---

# Kako razmišljamo

Svaka komponenta projekta mora imati jednu svrhu:

**Povećati sposobnost AI Alpha Enginea da pronađe, potvrdi i iskoristi održiv edge.**

Ako neka funkcionalnost tome ne doprinosi, nije prioritet.

Toolbox filozofija

AI Alpha Engine nije zamišljen kao sustav koji pokušava pronaći jednu "savršenu" trading strategiju.

Različiti tržišni uvjeti zahtijevaju različite pristupe.

Zbog toga AI Alpha Engine razvijamo kao inteligentnu kutiju alata (toolbox)

Svaka strategija predstavlja jedan specijalizirani alat.

Neke strategije bolje rade u trendu.

Neke bolje rade u konsolidaciji.

Neke bolje rade pri visokoj volatilnosti.

Neke bolje rade pri niskoj volatilnosti.

Zadatak AI Alpha Enginea nije dokazati da je jedna strategija najbolja.

Njegov zadatak je:

- razumjeti trenutno tržišno okruženje
- odabrati najprikladniju strategiju za taj režim
- upravljati rizikom
- upravljati portfeljem
- odlučiti postoji li dovoljno statističke prednosti za ulazak u tržište

Drugim riječima:

Ne tražimo savršen čekić. Gradimo cijelu kutiju alata i inteligenciju koja zna koji alat upotrijebiti u pravom trenutku.

Strategije nisu konkurenti jedna drugoj. One su specijalizirani alati koji zajedno čine inteligenciju AI Alpha Enginea.

---

# Dugoročna vizija

AI Alpha Engine nije zamišljen kao skup Python skripti.

To je inteligentan proizvod koji:

- istražuje financijska tržišta
- prikuplja i analizira podatke
- generira značajke (features)
- razvija biblioteku strategija
- prepoznaje tržišne režime
- odabire najprikladniju strategiju
- testira i optimizira strategije
- upravlja rizikom
- upravlja portfeljem
- uči iz vlastitih rezultata
- kontinuirano poboljšava kvalitetu svojih odluka

Cilj nije imati više funkcionalnosti.

**Cilj je donositi bolje odluke.**

---

# Naša obveza

Prije svake razvojne odluke postavljamo jedno pitanje:

> **"Doprinosi li ovo AI Alpha Engineu i njegovoj sposobnosti stvaranja održivog edgea?"**

Ako je odgovor **DA**, nastavljamo.

Ako je odgovor **NE**, preispitujemo odluku.

---

# Temeljno načelo

Ne gradimo najljepši softver.

Ne gradimo softver s najviše funkcionalnosti.

Ne gradimo Ferrari koji zadnji završi utrku.

**Gradimo proizvod koji svaki dan postavlja jedno pitanje:**

> **"Gdje danas postoji stvarna statistička prednost?"**

Ako je pronađe — djeluje.

Ako je ne pronađe — čeka.

To je filozofija AI Alpha Enginea.

# Kako razvijamo AI Alpha Engine

AI Alpha Engine razvijamo postupno.

Svaka faza mora biti dovršena, testirana i dokumentirana prije prelaska na sljedeću.

Svaka nova funkcionalnost implementira se u malim, jasno definiranim koracima.

Nakon svake implementacije odmah se izrađuju i izvršavaju automatizirani testovi kako bi sustav ostao stabilan tijekom cijelog razvoja.

Na taj način gradimo stabilan sustav čiji se razvoj temelji na provjerenim komponentama, a ne na pretpostavkama.

Ovaj dokument predstavlja temeljnu viziju projekta i služi kao kompas tijekom cijelog razvoja AI Alpha Enginea.

AI Alpha Engine nije razvijen da uvijek trguje. Razvijen je da zna kada ne treba trgovati jednako dobro kao što zna kada treba. Dugoročna uspješnost proizlazi iz kvalitete odluka, a ne iz količine aktivnosti.

---

# Relationship to Other Documents

This document defines **why** the AI Alpha Engine exists.

The remaining project documents define:

- `ROADMAP.md` — what will be built.
- `CURRENT_MISSION.md` — what is currently being developed.
- `ARCHITECTURE.md` — how the system is designed.
- `LOG.md` — what has already been implemented.

Together these documents provide the long-term direction, architecture and development history of the project.







## 24/7 Market-Universe Intelligence

The long-term AI Alpha Trading Agent is not a single-symbol BTC bot. It is intended to operate continuously as a 24/7 market-intelligence service across a broad, configurable universe of supported markets and instruments.

The target operating model is hierarchical rather than brute-force analysis of every strategy on every asset:

**Market Universe -> Lightweight Scanner -> Candidate Ranking -> Deep Strategy/Regime Analysis -> Risk Engine -> Portfolio/Exposure Check -> Execution**

- `Universe Manager` determines which configured venues, asset classes and instruments are currently tradable or relevant. Crypto may be monitored continuously; exchange-traded assets are governed by their own sessions/calendars.
- `Market Scanner` continuously applies inexpensive liquidity, volume, volatility, trend, momentum, breakout and regime filters to reduce the broad universe to a manageable candidate set.
- `Candidate Ranking` prioritizes the strongest opportunities so expensive strategy/regime analysis is focused where evidence is most promising.
- `Trading Engine` performs full strategy, validation and risk analysis only on shortlisted candidates and acts only when the complete decision policy is satisfied.
- Portfolio-level exposure/correlation controls govern simultaneous opportunities before live execution is authorized.

The objective is not maximum trading activity. The objective is continuous awareness of the available market universe and selective allocation of attention and risk to the best validated opportunities.

This capability is intentionally staged after one-symbol live-paper transport/runtime stability is proven. Scaling an unstable single-symbol runtime would multiply operational defects rather than create useful market intelligence.

## Selective Swing Trading Direction v1

The active alpha-research direction is stocks-first selective swing trading,
with crypto retained as an independent secondary opportunity set. The system
observes continuously but is expected to hold cash most of the time. Daily
completed bars are the primary decision resolution; trading frequency is never
an objective by itself.

Two distinct research sleeves anchor this direction:

- faithful, point-in-time replication of documented equity methods beginning
  with the complete CAN SLIM / O'Neil growth-stock framework;
- a separate BTC/ETH/XRP daily capitulation-volume reversal hypothesis derived
  from rare decline, exceptional volume, stabilization and confirmation.

The sleeves share deterministic data, execution, risk and evidence
infrastructure, but they do not share alpha claims. Each must be defined,
tested and closed independently before future AI ranking, regime allocation or
portfolio combination is permitted.

The controlling mandate is
`SELECTIVE_SWING_TRADING_RESEARCH_MANDATE_V1.md`. It preserves every prior
result while replacing incremental six-hour indicator variation as the active
research path. No strategy, PAPER or live authorization follows from the
direction alone.

## Selective Capital Deployment

The long-term agent is selective rather than continuously invested. Every
market sleeve must first establish an independently eligible causal signal.
Capital is then bounded by an equal `1/n` envelope across eligible signals, but
actual position size remains risk based and may leave substantial cash.

Listed-equity operation begins with at most three positions. Losers are removed
under frozen rules; their capital is not automatically chased into prior
winners. Future pyramiding may add smaller tranches only to profitable positions
on fresh causal evidence and never averages down.

General day trading and scalping are outside the mission. A rare explosive
listed-equity breakout from a causal sideways base may be studied later as one
separate, smaller-risk, same-session contingency with its own intraday data,
execution, stop and unseen-validation contract. It cannot weaken or borrow the
identity of faithful CAN SLIM research.

One future portfolio risk engine governs every sleeve. It may size an eligible
signal below its `1/n` envelope or reject it entirely; `NO_TRADE_HOLD_CASH` is a
successful safety outcome. The intended `3R` opportunity is screened before
entry but does not force a full exit at exactly `3R`. PAPER and live policies
remain frozen during operation: learning, threshold changes and new models are
developed offline, versioned and promoted only after independent validation.

## Venue-Bound Crypto Evidence

Selective crypto research treats price and volume as observations from an
identified venue, not as universal market facts. The primary BTC/ETH/XRP daily
dataset therefore uses one reviewed USD spot venue whenever possible, retains
provider identity and exact source hashes, and records missing intervals rather
than manufacturing continuity.

Cross-venue data may provide independent robustness evidence, but raw volumes
are never merged and one venue cannot silently fill another venue's suspension.
This preserves the meaning of capitulation volume before the system attempts to
discover or claim an edge.

The Kraken acquisition boundary is byte-first and fail-closed. Official ZIP
archives are hashed and fully inventoried before three native daily members are
selected. The first archive/REST bridge proposal failed closed because recent
REST volume and trade counts were not identical to the official archive even
though OHLC matched. The locked v2 dataset therefore uses only two exact frozen
official archives through 2026-03-31; REST cannot enter, repair or extend those
historical bytes. Every unavailable day is preserved as a no-trade boundary,
and no dataset becomes visible until all three assets, source evidence, gaps
and canonical hashes pass one atomic lock. That lock and its independent
revalidation are complete; real blinded-replay review remains a separate later
authorization boundary.

That replay boundary is bounded before any chart is shown. One episode per
asset is selected reproducibly from manifest identity and availability alone,
not from attractive historical price or volume events. Future endpoints remain
sealed, each decision must be durably chained before the next bar appears, and
an open episode-end position stays unresolved rather than becoming a fabricated
exit or performance result.

The sealed preflight has independently reproduced the exact locked dataset,
availability segments and price-independent candidate counts without exposing
or persisting the selected timestamps. Passing that data-and-selection gate
does not authorize the participant replay or turn reconstruction into a
strategy or performance claim.

Supervised reconstruction advances only one asset episode at a time and only
after a fresh explicit decision. Every completed episode is independently
locked before the next asset can be considered; an interruption preserves
evidence and stops progression. This makes careful observation reversible at
asset boundaries while keeping hindsight, automatic retry and performance
interpretation outside the replay itself.

## Deterministic AI-Driven Crypto Research

The single completed BTC supervised episode, bound by evidence SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`,
showed why the long-term system must convert visual intuition into explicit,
testable language. Human observation remains useful for forming hypotheses,
but an unassisted operator should not be asked to improvise confirmation,
pullback, volume, stop and exit rules sixty times per asset.

The next system is a deterministic AI-driven research agent. It first measures
completed-bar decline, relative volume, volatility expansion and close
location; a separately frozen state machine will later decide whether an event
is absent, armed, confirmed, invalidated or held. Every runtime decision must
be reproducible from named inputs and versioned rules, with next-bar execution,
risk and evidence outside the language model.

AI may help offline with hypothesis design, code, diagnostics and proposal of
new versions. It cannot use future outcomes, silently mutate active thresholds
or self-promote a strategy. The locked BTC/ETH/XRP dataset can support bounded
development without an immediate update, while later archive extensions form
new immutable datasets. No feature milestone alone authorizes strategy
performance, optimization, Candidate v2, PAPER, cloud or live execution.

The first explicit agent path is
`FLAT -> ARMED -> LONG -> FLAT` under reference identity
`kraken-ai-v2-ccvr-reference-a-v1`. It replaces phrases such as “maybe
confirmation” with exact price, volume, volatility, time and structure gates.
Each transition must explain itself, and a missing required measurement must
hold or cancel safely rather than become a guessed signal.

This layer is still observation and decision logic, not trading. Its
`ENTER_NEXT_OPEN` and `EXIT_NEXT_OPEN` outputs are intents awaiting a separate
risk/execution contract. The prior BTC human reconstruction remains immutable
under SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.
Until fills, gaps, stops, size and causal reward room are frozen and independently
validated, no strategy performance, Candidate v2, PAPER, cloud or live claim
exists.

The next reviewed layer converts those intents into deterministic synthetic
plans under policy `kraken-ai-v2-risk-execution-reference-a-v1`. It admits a
following-open entry only when the fixed structural stop survives the gap and
the causal prior resistance still offers at least net cost-aware `3R` after
adverse taker commission, spread and slippage assumptions. Risk is capped by
equity, total open risk, one-third notional, concurrent positions and cash.

Intent, approved plan, synthetic position and real venue order are different
states of evidence. V2 currently reaches only the synthetic position boundary:
entry-bar protection, stop-first daily ordering and next-open state or 20-bar
maximum-hold exits can be tested, but no broker instruction exists. The human
BTC reconstruction remains immutable context under SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`.

Before the locked history is opened for this full path, the project must freeze
development and genuinely untouched evaluation identities. The adapter is not
profitability evidence and cannot authorize optimization, Candidate v2,
PAPER, cloud or live execution.

## Calendar-Frozen AI-Driven v2 Evidence

Protocol `kraken-btc-eth-xrp-ai-driven-v2-partition-v1` now protects that
evidence boundary without opening the dataset. Development spans
`2019-01-01T00:00:00Z` through `2024-04-01T00:00:00Z` exclusive; calibration
then spans one year; the final year beginning `2025-04-01T00:00:00Z` is the
sealed one-time evaluation. The boundaries are calendar-only and were fixed
before any full-path V2 performance was read.

The prior BTC supervised evidence SHA-256
`56710a21a423a63963e5c97ab6ca956021f9cd7a7d494c3f29a197068367ff60`
falls wholly inside calibration. That window is permanently inspected and can
never support an unseen claim. Evaluation remains genuinely untouched until a
later one-time protocol is explicitly authorized after development,
calibration, parameters, costs and reporting are closed.

Every partition and provider gap starts with empty warmup, flat signal state
and no synthetic position. Nothing crosses those boundaries to manufacture
continuity. This partition milestone is governance, not performance:
optimization, Candidate v2, PAPER, cloud and live execution remain blocked.

## Development-Only Automated Evidence

Protocol `kraken-btc-eth-xrp-ai-driven-v2-development-runner-v1` prepares one
auditable reference-A observation on development through
`2024-04-01T00:00:00Z` exclusive. Its reader combines opaque byte hashing of
the full immutable asset files with OHLCV parsing of the development prefix
only. Calibration and sealed evaluation values never become runner inputs.

The first portfolio path uses USD 5,000 research notional, shared cash and
risk, fixed BTC/ETH/XRP same-time priority and adverse cost-aware synthetic
execution. A provider gap or terminal boundary never manufactures a price or
exit: affected positions remain unresolved and a mid-run gap halts the path.

This is designed to turn one frozen hypothesis into durable development
evidence, not to search for an attractive answer. No parameter sweep, ranking
or automatic promotion exists. Even after an explicitly authorized run,
calibration, evaluation, optimization, Candidate v2, PAPER, cloud and live
execution require separate decisions.

The first authorized attempt exposed an input-representation boundary before
evidence could be written: exact external decimal text passed validation but
was not normalized to the internal `float64` OHLCV contract. Recovery preserves
all research semantics and adds only that explicit conversion plus a matching
real-reader integration test. A technical attempt is never reinterpreted as a
strategy result, and its authorization cannot be silently reused.

Recovery evidence SHA-256
`f537410d2a237be207951b638518d80e861289dafa7db9b5c2322ffa32d4e594`
closes Reference A as
`KRAKEN_AI_V2_DEVELOPMENT_REFERENCE_A_CLOSED_NO_TRADE_HOLD_CASH`. Thirteen
state confirmations proved the decision path was active, but all thirteen
failed the frozen causal/cost-aware entry-feasibility gates. Zero P&L is
therefore absence of exposure, not a break-even edge. Any continuation requires
a new pre-registered development hypothesis; Candidate v2 and every deployment
authorization remain false.

## Bounded Hybrid Strategy Discovery and Learning

Protocol
`kraken-btc-eth-xrp-ai-driven-v2-hybrid-strategy-discovery-learning-v1`
selects a hybrid architecture after Reference A: one shared, economically named
strategy-family catalog with asset/regime-specific routing and one common hard
portfolio safety envelope. BTC, ETH and XRP may justify different causal
mechanisms; an asset without an eligible route remains `HOLD_CASH` rather than
being forced into a universal strategy.

The first catalog bounds research to capitulation recovery, trend-pullback
continuation, range mean reversion and volatility breakout. These are permitted
mechanism classes, not implemented winners. Each future hypothesis must bind
its assets, regimes, two-to-five permitted indicator primitives, causal signal,
family-specific execution, development gates and evidence lineage before data
access. At most six hypotheses may enter one round, and no leaderboard or
Cartesian parameter sweep exists.

Learning is offline and versioned: immutable development evidence may explain
failure and propose a new manifest, but no running strategy can mutate itself.
Reference A stays closed and its exact identities cannot be reused. This layer
opens no market data and creates no strategy runner, performance result,
calibration access or Candidate v2 authorization.

## Pre-Registered Hybrid Discovery Round 1

Protocol `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-1-v1`
turns the shared catalog into four exact, still-nonexecuting hypotheses: a new
volatility-path capitulation recovery, trend-pullback continuation, range mean
reversion and volatility breakout. Each begins with BTC, ETH and XRP routes,
but later retention is decided per asset-family pair; different assets may
retain different mechanisms or remain `HOLD_CASH`.

Round 1 freezes completed-bar indicators, net `3R` family-specific trade paths,
baseline and doubled-friction stress costs, five chronological Development
slices and absolute sample, expectancy, profit-factor, drawdown and outlier
gates. It does not rank terminal returns. More than one passing route for an
asset requires a separate portfolio review rather than automatic selection.

Reference A remains immutable lineage only. No regime, signal or execution
component has yet been implemented, and no data has been opened. Candidate v2,
Calibration, Evaluation and every deployment authorization remain false.

## Round 1 Causal Signals

Round 1 now has one shared causal feature engine and four deterministic entry-
signal paths: capitulation recovery, trend-pullback continuation, range mean
reversion and volatility breakout. Every rolling baseline excludes the current
bar, every decision uses completed-bar evidence and every accepted signal emits
only a following-open research intent.

The four paths are independent state machines bound to the immutable Round 1
configuration. Trend and range permit confirmation only on the immediate next
completed bar; capitulation retains its five-bar window; breakout confirms on
the current completed bar. Gaps, invalid OHLCV, unavailable warm-up features
and unknown families fail closed.

This is not execution or performance evidence. No quantity, fill, position,
cost, P&L, ranking or runner exists and no dataset was opened. Reference A
remains closed and is feedback lineage only; Candidate v2 remains unauthorized.
The next boundary is synthetic implementation of four family-specific
execution adapters under the already frozen shared risk envelope.

## Round 1 Family Execution

Round 1 now has four family-specific synthetic execution adapters bound to the
four causal signal paths. Capitulation recovery, trend-pullback continuation
and volatility breakout calculate the exact adverse-cost target required for
net `3R`; range mean reversion uses its immutable signal-time Bollinger midline
and holds cash when that anchor lacks net `3R` room.

Every adapter preserves next-open timing, baseline and stress cost profiles,
family stops and maximum holds, entry-bar protection, stop-first ambiguity and
the shared `0.50%` position-risk, `1.50%` total-risk, three-position and one-
third asset-notional ceilings. Gaps never widen a stop, and completed position
paths cannot cross a missing daily timestamp.

This completes signal-to-synthetic-execution mechanics, not discovery. No
dataset, runner, route result, ranking or strategy selection exists. Reference A
remains closed and Candidate v2 remains unauthorized. The next boundary is an
unexecuted, hash-bound Development discovery runner followed by a separate
operator decision about one-shot Development authorization.

## Round 1 Discovery Runner

Round 1 now has a one-shot Development-only discovery runner over the exact 12
BTC/ETH/XRP asset-family routes and both frozen cost profiles. Every route and
cost profile receives an independent USD 5,000 research ledger so the absolute
pre-registered gates remain comparable; these are not combined portfolio
allocations and the runner produces no leaderboard or winner.

Five chronological slices measure persistence without resetting positions or
causal state. Known provider gaps do reset feature/signal context; an open
position at a gap or Development end remains unresolved and fails the route
without a synthetic force-close. Route interest requires every absolute gate,
and round interest still requires two assets and two routes. Multiple passing
families for one asset require a new portfolio review.

The implementation and independent evidence lock were integrated at commit
`98a7218`. One separately authorized Development run completed and recorded
canonical report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
No route passed every frozen gate, so the exact result is `HOLD_CASH`.
Calibration, Evaluation, Candidate v2, ranking, PAPER, cloud and live execution
remain unauthorized.

## Round 1 Closure

Round 1 closes as
`KRAKEN_AI_V2_ROUND_1_CLOSED_NO_ELIGIBLE_ROUTE_HOLD_CASH`. Its one-shot
authorization is consumed and no gate may be weakened after inspection.

Offline feedback identifies two descriptive single-gate failures without
promoting either: BTC volatility breakout failed stress profit concentration,
while ETH volatility breakout failed chronological stability by one stress
slice. All range-reversion routes produced no closed trade; XRP trend and
breakout expectancy were negative under both costs. These facts may inform a
new version but are not a leaderboard or Candidate evidence.

Closure was reproduced against the locked evidence and integrated at commit
`58bdae0`. Round 1 remains immutable; its report hash is the feedback lineage
for any later version. Reference A remains closed and Calibration, Evaluation,
Candidate v2, PAPER, cloud and live remain unauthorized.

## Pre-Registered Hybrid Discovery Round 2

Protocol `kraken-btc-eth-xrp-ai-driven-v2-hybrid-discovery-round-2-v1`
registers three new, nonexecuting hypotheses from immutable Round 1 report
SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`.
The set is deliberately smaller than the six-hypothesis ceiling: an ATR-
normalized capitulation recovery for BTC/ETH/XRP, breakout-retest continuation
for BTC/ETH and multi-bar MACD trend resumption for BTC/ETH.

All range routes are retired after producing no closed-trade evidence. XRP
trend and breakout are retired after negative expectancy under both costs.
Retirement preserves the failed evidence; it does not delete history or rank
the retained mechanisms as winners.

Round 2 keeps the exact Round 1 costs, five chronological Development slices,
interest gates and shared safety envelope. Cumulative use is seven of twelve
hypotheses and this is the second of two permitted rounds. No component, data
access, run, Candidate v2 or deployment is authorized by registration. The next
boundary is synthetic-only implementation of the three exact causal paths.

## Round 2 Causal Signals

Round 2 now implements three exact causal state machines against immutable
Round 1 report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`:
ATR-normalized capitulation recovery, breakout-retest continuation and
multi-bar MACD trend resumption. The routes remain asymmetric exactly as
registered; implementation does not restore retired range or XRP routes.

All rolling decision baselines exclude the current bar. Capitulation requires
at least two completed post-setup bars, breakout requires an ordered breakout,
later retest and still-later confirmation, and trend requires a two-to-five-bar
pullback plus a real MACD histogram zero cross. Every success emits only an
`ENTER_NEXT_OPEN` research intent.

This is causal mechanics, not strategy evidence. No dataset, execution plan,
position, fill, performance, ranking or runner exists in this milestone.
Candidate v2, Calibration, Evaluation, PAPER, cloud and live remain
unauthorized. The next boundary is synthetic implementation of three exact
family execution adapters under the unchanged shared safety envelope.

## Round 2 Family Execution

Round 2 now has three exact synthetic execution adapters bound to immutable
Round 1 report SHA-256
`3ce14fda95f657c0b671b74c702d55ec4102da303e9e033ebaf0e02ff5c2fa9b`
and the Round 2 causal signals. The asymmetric scope is enforced: capitulation
may route BTC/ETH/XRP, while breakout-retest and MACD trend resumption remain
BTC/ETH only.

Every family uses next-open entry, both unchanged adverse cost profiles, exact
net `3R`, the shared `0.50%` position-risk and `1.50%` total-risk envelope,
one-third asset notional and three-position limits. Stops remain tied to the
causal setup/retest/pullback low minus `0.25` signal-time ATR. Maximum holds are
25, 60 and 40 completed bars respectively.

This completes synthetic signal-to-position mechanics, not discovery
evidence. No dataset, runner, route result, ranking or strategy selection
exists. Candidate v2, Calibration, Evaluation, PAPER, cloud and live remain
unauthorized. The next boundary is an unexecuted, hash-bound Round 2
Development discovery runner followed by a separate one-shot operator choice.

## Round 2 Discovery Runner

Round 2 now has a nonexecuting one-shot Development runner for exactly seven
registered routes: three each for BTC and ETH and capitulation recovery only
for XRP. Retired range routes and retired XRP trend/breakout routes cannot
silently return through a cross-product loop.

Each route and cost profile has an independent USD 5,000 research ledger. The
five slices remain reporting windows; known gaps reset causal context and an
open position at a gap or Development end remains unresolved. There is no
synthetic terminal force-close, ranking, automatic strategy selection or
portfolio combination.

The runner reuses the locked Development-only reader, opaque full-file hashes,
atomic external evidence and an independent evidence lock. This milestone only
implements and hash-reviews those mechanics. The dataset remains unopened and
the exact one-shot phrase is inactive. Reference A and Round 1 remain closed;
Calibration, Evaluation, Candidate v2, PAPER, cloud and live remain
unauthorized pending a separate operator decision.

## Round 2 Closure and True Learning Transition

Round 2 Attempt 1 executed once from commit
`a601a322b353179663a96423bc29d50adc28627e`. Its canonical report SHA-256 is
`5f9acde53d0e2cf35cd1010d0002222182670d7255bdf44e18715f4902c85a01`.
All seven routes were ineligible, so Round 2 Closure preserves `HOLD_CASH` and
permanently prohibits a rerun.

The existing deterministic state, feature, execution, partition and discovery
stack is now named the **Rule Discovery Foundation**. It is valuable causal and
audit infrastructure, but it is not the intended system.
The True Learning Engine is not yet implemented. It must learn model parameters
from labeled market examples rather than receive them from us.

The project therefore returns to its intended V2 goal. The next deliverable is
a True Learning Contract; after that come data-sufficiency review, offline
model training, Development walk-forward prediction, a frozen Candidate v2,
one-time Calibration, untouched Evaluation and only then bounded PAPER.
Calibration, Evaluation and Candidate v2 remain unauthorized.
