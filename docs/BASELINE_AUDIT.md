# Audited real baseline — 2026-10-21

An independent computational review found no material arithmetic error or unsupported historical-backtest claim in methodology 1.0.0 for the original saved capture `official-1c1dd1e38793565f2b84`. Capture completed at **2026-10-21 11:37:11 UTC**. It contained **146 complete weekly observations**, 2024-01-03 through 2026-10-14.

The separate audit used integer subtraction and rational equality without importing the project's calculations as its arithmetic oracle. It reproduced all 146 liquidity, reserve, and gap values in JSON, CSV, and the static HTML history table. It verified the manifest and nine referenced file hashes. **Twenty official input cells**—the latest five dates across four series—were independently checked against the four official FRED pages; the latest date was also checked against the [original October 15 H.4.1 release](https://www.federalreserve.gov/releases/h41/20261015/). The older history was recomputed from the saved raw capture, not individually verified against every original historical release.

The [arithmetic audit results](audit/arithmetic-results.json) preserve the numerical evidence and scope. The original full raw snapshot is not bundled in this public release. These results do not claim to be a newly captured or complete historical vintage archive.

## Official reference points

Inputs are **USD millions**, all Wednesday levels and NSA. Sources: Board of Governors of the Federal Reserve System (US), via FRED: [WALCL](https://fred.stlouisfed.org/series/WALCL), [WDTGAL](https://fred.stlouisfed.org/series/WDTGAL), [WLRRAL](https://fred.stlouisfed.org/series/WLRRAL), [WRBWFRBL](https://fred.stlouisfed.org/series/WRBWFRBL). Retrieved and reviewed 2026-10-21.

| Wednesday | Assets | Treasury account | Total RRP | Reserves | Derived L, USD bn |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2026-09-16 | 6,746,548 | 991,708 | 323,803 | 2,921,536 | 5,431.037 |
| 2026-09-23 | 6,747,704 | 947,317 | 320,725 | 2,969,922 | 5,479.662 |
| 2026-09-30 | 6,743,031 | 984,046 | 361,883 | 2,881,686 | 5,397.102 |
| 2026-10-07 | 6,747,560 | 885,783 | 333,739 | 3,022,066 | 5,528.038 |
| 2026-10-14 | 6,755,639 | 885,823 | 326,799 | 3,030,854 | 5,543.017 |

For the latest row, `6,755,639 − 885,823 − 326,799 = 5,543,017m = 5,543.017bn`. The reserve level is 3,030.854bn and the proxy–reserve gap is 2,512.163bn. Over four exact calendar weeks, the proxy change is **+111.980bn**: assets **+9.091bn**, Treasury-account contribution **+105.885bn**, reverse-repo contribution **−2.996bn**. Reserve balances changed **+109.318bn**, leaving **+2.662bn** of change in the gap.

## Meaning and limits

The proxy is assets net of two distinct liability categories. Total RRP includes foreign official/international accounts and other reverse repos. Reserves remain inside the proxy, alongside omitted liabilities and capital. The reserve cross-check shares the same accounting identity; it is not an independent market signal. Published values may be rounded.

October 14 is the observation date; October 15 is the dated Board release; October 21 is this archive's capture. The current-page update timestamp does not prove first availability for every historical row. Archive queries before capture must fail. A single real capture leaves official revision history **unknown**, not zero. Historical vintages, historical release timestamps, causal effects, and predictive trading performance remain unverified or unsupported.

The separate synthetic pair reconciles **5,925 + 2 prior-data effect + 13 new-endpoint effect + 0 method effect = 5,940bn**. Four new cells and two changed prior cells are intentionally invented. A separate audit fixture tested a nonzero methodology effect; it was an artificial test, not an economic recommendation.

The public release retains the audited Python runtime and frozen methodology bytes. Public documentation, packaging, and example selection are release preparation. Rendered visual inspection was outside the audit's scope and remains pending; matching static HTML values is a content check only.
