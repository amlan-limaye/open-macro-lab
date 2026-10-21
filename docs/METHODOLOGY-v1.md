# Methodology 1.0.0 — selected US liquidity and reserve cross-check

Status: first local release. Definition frozen in `open_macro_lab/methodologies/v1.json`; future changes require a new version. The snapshot embeds this JSON so later code cannot silently substitute a different definition.

## Question and perimeter

How have selected positions on the Federal Reserve balance sheet changed, which of the selected components account for that movement, and how closely does the resulting proxy track actual reserve balances? The target is readable accounting research. It is not a global liquidity aggregate, broad money measure, shock identification exercise, forecast, or trading model.

The package deliberately contains two linked recipes rather than a large indicator catalog. Recipe 1 is a balance-sheet proxy and contribution calculation. Recipe 2 is a directly observed reserve comparison and residual calculation; `reserves` and `gap` are the two outputs of that second recipe.

## Inputs and transformations

| Symbol | Official series | Native scale and observation basis | Transform |
| --- | --- | --- | --- |
| A | WALCL, total assets less consolidation eliminations | USD millions, NSA, Wednesday level | / 1,000 |
| T | WDTGAL, Treasury general account | USD millions, NSA, Wednesday level | / 1,000 |
| Q | WLRRAL, total reverse-repo liabilities | USD millions, NSA, Wednesday level | / 1,000 |
| R | WRBWFRBL, reserve balances | USD millions, NSA, Wednesday level | / 1,000 |

Original units are checked before conversion. All calculations use Python `Decimal`; rounding to three decimals occurs only in the display. JSON retains exact decimal strings. CSV export labels derived values as USD billions and identifies official versus synthetic data. Missing data is blank in exports, not zero.

### Recipe 1

`L_t = A_t − T_t − Q_t`, after converting all inputs to USD billions.

`Δ_h L_t = (A_t − A_(t−h)) − (T_t − T_(t−h)) − (Q_t − Q_(t−h))`.

The three signed terms are exhaustive **accounting contributions to this defined proxy**, not causal estimates. Horizons are one, four, and thirteen calendar weeks (7, 28, 91 days). They use exact endpoint dates; absent intermediate weeks are disclosed, and a missing endpoint makes that horizon unavailable.

WLRRAL includes foreign official and international accounts and other reverse repos. It is not just the overnight facility. This definition is a deliberate scope choice for consistent H.4.1 measurement, not an assertion that it is economically superior to every alternative. Never compare it as though it were the familiar assets-minus-TGA-minus-ON-RRP metric without explaining the difference.

### Recipe 2

`R_t = WRBWFRBL_t / 1000`.

`G_t = L_t − R_t`; `Δ_h G_t = Δ_h L_t − Δ_h R_t`.

The positive level of G is largely balance-sheet positions omitted from L, including other liabilities and capital. This release does not separately reconcile each omitted item. A widening gap means the proxy rose relative to reserves (or fell less), not necessarily that liquidity improved. Reserve quantity alone does not measure its distribution or the marginal price of funding.

## Three different clocks

1. **Observation date:** the Wednesday balance-sheet measurement date supplied by each CSV.
2. **Publication/first availability:** historical per-observation dates are **unknown** here. Current FRED metadata update text and HTTP `Date` headers do not establish them.
3. **Archive capture:** actual UTC retrieval per input and completion of the entire saved snapshot. This is the conservative knowledge timestamp used by `--store --as-of`.

All historical rows in the CSV are current-vintage values as of acquisition. No vintage archive is fetched in v1. No fixed one-day lag is promoted into evidence of first release. The system must refuse to answer archive-known queries before a stored snapshot, rather than leaking a future revision backward. A full historical point-in-time backtest remains unsupported.

Acquisition is sequential, not an atomic upstream transaction. A capture may straddle an upstream update. Differing latest input dates and incomplete common endpoints are disclosed. Matching observation dates alone cannot prove all series came from an identical release vintage.

## Alignment and data health

Expect USD millions, USD currency, NSA, weekly, Wednesday level. Fail on a wrong contract, unexpected CSV columns, duplicate dates, non-Wednesday dates, observations after source retrieval, nonfinite/negative input balances, or balances above the documented sanity bound of 1e12 million USD. The bound is a corruption guard, not an economic forecast. Valid negative **derived** L or G is not clamped to zero.

Build a Wednesday calendar spine from the earliest to latest downloaded observations. Never resample, interpolate, backfill, or forward-fill. Preserve `.` and empty values as missing. A headline requires a complete common date for both recipes. If newer incomplete rows exist, show the older complete date with a warning. If none exists, fail without creating a report.

Ten calendar days is the warning threshold for the latest complete observation. As-of defaults to the saved capture for reproducibility; `--as-of now` checks present age. This is not a publication calendar and can warn around unusual release schedules. A report is a saved issue, not an automatically updating screen.

## Changes between captures

Compare exact series/date cells, in native units. Numeric equality ignores formatting changes such as `1.0` versus `1.000`. Classifications:

| Class | Evidence |
| --- | --- |
| New observation | Date later than that series' previous maximum appears |
| Revised prior value | Same date, two nonmissing unequal numeric values |
| Historical backfill | Previously absent historical date appears |
| Filled missing / became missing | An existing cell changes between missing and numeric |
| Removed observation | A previously present date disappears |
| Coverage added / removed | Changed requested start window explains coverage differences |
| Methodology change | Effective versioned method JSON hash differs |

These classes describe archive differences. They do not establish a statistical agency's motivation or exact revision timestamp. A dropped row can reflect a retrieval problem, not an official deletion. An earlier missing observation can be a source backfill or coverage issue; its provenance needs investigation. A first capture supplies no revision evidence at all.

For old complete endpoint t0 and new complete endpoint t1, the bridge is:

`old_method(old_data[t0])`

`+ [old_method(new_data[t0]) − old_method(old_data[t0])]` — changed prior endpoint data

`+ [old_method(new_data[t1]) − old_method(new_data[t0])]` — new endpoint

`+ [new_method(new_data[t1]) − old_method(new_data[t1])]` — methodology

`= new_method(new_data[t1])`.

This ordered decomposition allocates interactions to the later step. It is an accounting convention, not a unique causal attribution. It is suppressed if coverage changes or required endpoints are missing. The cell log still includes all differences, including revisions that do not affect t0 or t1. A report can explicitly record unchanged data without asserting that history was never revised before the first capture.

## Reproducible hand example — synthetic

The baseline endpoint is 2025-04-16, with A=7,150bn, T=875bn, Q=350bn, R=3,120bn: L=5,925bn and G=2,805bn.

In the later **fabricated** capture, the old endpoint's A is changed to 7,152bn. The new 2025-04-23 endpoint is A=7,160bn, T=880bn, Q=340bn, R=3,128bn: L=5,940bn, G=2,812bn.

The proxy bridge is **5,925 + 2 + 13 + 0 = 5,940bn**. The reserve bridge is **3,120 + 0 + 8 + 0 = 3,128bn**. A separate earlier Treasury revision is visible in the log but does not affect these headline endpoints. The fixtures deliberately produce four new cells and two changed prior values. These are not claims about actual official revisions.

## Limits to confidence

Arithmetic is exact within source precision and the stated contracts. Economic interpretation is limited to the chosen accounting perimeter. Temporal confidence begins at the archive's own captures. No uncertainty intervals, economic significance thresholds, causal effects, or out-of-sample return claims have been estimated. A small proxy movement may reflect routine Treasury flows, maturity/settlement effects, or other changing balance-sheet items; the recipe cannot establish the cause by itself.
