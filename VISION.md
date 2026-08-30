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
