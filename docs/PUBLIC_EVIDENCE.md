# Reproduce the dated public baseline

Version 0.3.0 presents a real saved baseline as the main example. This is **not a live feed, a new capture, or a real revision comparison**. The independent original audit covered 146 weeks and rechecked 20 recent official input cells. The new public arithmetic check reproduces all 146 rows from the published numerical CSVs without importing the research engine; it does not independently reacquire historical official releases.

## Dates and grain

| Field | Value and meaning |
| --- | --- |
| Observation range | 2024-01-03 through 2026-10-14; 146 Wednesday levels |
| Original capture completed | 2026-10-21T11:37:11+00:00; when this archive finished retrieval |
| WALCL retrieved | 2026-10-21T11:37:03+00:00 |
| WDTGAL retrieved | 2026-10-21T11:37:07+00:00 |
| WLRRAL retrieved | 2026-10-21T11:37:09+00:00 |
| WRBWFRBL retrieved | 2026-10-21T11:37:11+00:00 |
| Numerical export created | 2026-10-22T10:32:28+00:00; packaging existing numbers, not a new observation |
| Historical publication dates | Unknown per observation; not inferred from observation, retrieval, or export dates |

Native inputs are USD millions, not seasonally adjusted. Every join uses the exact Wednesday observation date; missing values are not filled. Current-vintage history means the values returned by the October 21 capture, including any earlier revisions already present. One saved capture cannot reveal those revisions or reconstruct what a researcher knew before that capture. The original manifest hash identifies the referenced capture but is not signed source authentication.

## Run the public checks without network access

From the source checkout using Python 3.9 or later:

```sh
python3 -m open_macro_lab verify-report examples/official
python3 scripts/check_public_example.py examples/official
python3 -m open_macro_lab report \
  --snapshot examples/official/evidence/public-30855ad1a04b2439afc3 \
  --output build/reproduced-official
python3 -m open_macro_lab verify-report build/reproduced-official
```

The original private capture and its source webpages are not needed for these commands. Keep the entire public report folder together, including its seven-file numerical evidence bundle. Use the package version and source hash recorded in `report.json`; verification intentionally refuses a different engine. `scripts/check_install.py WHEEL --public-report examples/official` also tests an installed CLI outside the source checkout, copying only the public report and reproducing all four generated output files byte-for-byte.

## Exactly what is verified

`verify-report` reports `evidence_scope: numerical_export` for this artifact. It checks the public manifest identity; method and CSV hashes; series identities, declared units/frequency/basis; finite values; dates and retrieval chronology; row statistics; analysis fields; and exact regenerated CSV/HTML bytes. The public source contract is a declaration copied from the validated original capture. **The omitted source webpages cannot be rechecked from this bundle.** The existing original-capture verifier still requires its complete evidence and refuses a silently stripped capture.

The separate `check_public_example.py` uses independent Decimal arithmetic for method 1.0.0. It reconstructs the weekly date set, checks all 584 input cells against report JSON, recomputes all three quantities for each of 146 weeks, checks calculated CSV values, and reconciles available calendar-window changes. It does not import the engine or claim to authenticate source servers, verify release times, or test browser rendering.

For the latest observation, in USD millions:

```text
L = (6,755,639 − 885,823 − 326,799) / 1,000 = 5,543.017 USD bn
R = 3,030,854 / 1,000                       = 3,030.854 USD bn
G = L − R                                 = 2,512.163 USD bn
```

WLRRAL is total reverse-repo liabilities, including foreign official accounts. The proxy is not global liquidity or a proven trading signal. Reserves and the proxy share an accounting identity. The [methodology](METHODOLOGY-v1.md) and [baseline audit](BASELINE_AUDIT.md) retain the economic limitations and four-week contribution reference points.

## Format and distribution boundary

Each `public-<hash-prefix>` directory is a distinct `open-macro-lab-numerical-export` artifact, not a partially copied `official-…` capture. It contains exactly:

- `manifest.json` and `manifest.sha256`, with original capture and export times separately recorded.
- `methodology.json`, unchanged from the executed method.
- `raw/WALCL.csv`, `raw/WDTGAL.csv`, `raw/WLRRAL.csv`, and `raw/WRBWFRBL.csv`, byte-identical to the saved numerical inputs.

The public manifest has an explicit field allowlist and records attribution, source URLs, retrieval times, contract declarations, row statistics, and the omitted evidence. It excludes captured HTML, source-site assets, transport headers, private notes, personal paths, and the original full manifest. Source data retain their separate [rights and citation conditions](../DATA_LICENSE.md).

The main static-site route is the dated official report; `/synthetic/` is the clearly labeled fabricated revision example. `SITE_FILES.json` maps every staged file explicitly. Staging verifies report reproduction, reviewed file hashes, the two routes, and the complete report inventories; it refuses unexpected source HTML, unlisted report files, unsafe paths, or altered bytes. It performs no hosting or upload.

## A genuine later comparison

When a separately authorized new official acquisition has actually succeeded, retain its original capture and the October 21 baseline, then run:

```sh
python3 -m open_macro_lab export-public \
  --snapshot NEW_ACTUAL_CAPTURE --previous PREVIOUS_ACTUAL_CAPTURE \
  --output build/new-public-comparison
python3 -m open_macro_lab verify-report build/new-public-comparison
```

Both source captures are verified before preparing separate numerical exports. Their actual retrieval/capture times remain unchanged. The export time records this export operation. Preserve older issues; review actual changed cells, dates, coverage and warnings before updating the public demonstration. A delayed or unchanged source is a valid outcome. This release contains no second real capture, fabricated future observation, automatic refresh, or inferred official revision time.
