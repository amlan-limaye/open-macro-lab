# Verification scope for v0.2.0

Reviewed 2026-10-22. This version adds an operational capture/report workflow and complete offline report verification. Methodology 1.0.0, the arithmetic engine, all synthetic fixture bytes, and the original real baseline remain unchanged. The original 0.1.0 release is preserved.

## Automated checks

- The public suite runs **76 tests: 75 pass and one optional official-snapshot test skips**, on Python 3.9.6 and 3.13.7. The full original official capture is deliberately not in the public bundle.
- Existing checks cover independent hand calculations; unit/currency/frequency/basis/seasonal mismatches; malformed/future observations; missing endpoints and interior gaps; stale-age boundaries; no-lookahead selection; revision classes; exact method/data bridges; hash tampering; day plurals; and named chart/table scroll regions.
- New workflow tests cover first-run baselines, previous-capture selection, inherited method/coverage, exclusion of future and synthetic captures, idempotent retries, acquisition/write failures, corrupt archives, incomplete-prior recovery, unchanged-value wording, portable output bytes, and CLI behavior.
- Report verification detects altered input bytes, calculations, CSV, HTML, invalid evidence identifiers, and a mismatched source engine. A successful check does not mutate the issue or use network access.
- The acquisition integration test exercises the actual metadata/CSV adapter through the CLI with **fabricated HTTP responses** in temporary directories. Its invented revisions are not official revision evidence.
- Clean wheel installations pass in empty Python 3.9.6 and 3.13.7 virtual environments outside the checkout. Checks cover the console command, isolated module command, packaged method/fixtures/license notices, offline demo, report reproduction, and `pip check`. The wheel has zero runtime dependencies. Building it requires setuptools; installation of the built wheel uses no network.
- Synthetic reference remains **5,925 + 2 prior-data effect + 13 new-endpoint effect + 0 method effect = 5,940 USD bn**.
- Content and Node mock DOM interaction checks pass. These are not browser rendering or screen-reader checks.

```sh
python3 -m unittest discover -s tests -v
python3 -m open_macro_lab verify-report examples/synthetic
python3 scripts/check_report.py examples/synthetic
node scripts/check_interactions.js examples/synthetic/index.html
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 scripts/check_install.py dist/open_macro_lab-0.2.0-py3-none-any.whl
python3 scripts/package_release.py
```

## Existing real evidence

The original official snapshot was captured **2026-10-21 11:37:11 UTC**, with observations through **2026-10-14**. The [independent baseline audit](docs/BASELINE_AUDIT.md) previously recomputed all **146 weeks** and checked **20 official input cells**.

Version 0.2.0 reproduces that saved baseline locally and verifies the complete resulting report. All 146 calculated rows and research values match the prior output; only implementation provenance (source hash and newly recorded package version) changes. This reuses existing evidence; it is **not a new acquisition or observed revision comparison**. Its report and captured source HTML stay outside the public bundle. The separate next-real-release comparison remains pending.

## Visual and evidence boundaries

The publisher reported verification of the prior singular-day and narrow-screen overflow fixes at source commit `72c0652ce84ebdda91e2b921d733e36e2993f212`. Those fixes are preserved. This workflow pass performs no browser actions and claims no new screenshot, screen-reader, or print review. Chart geometry, labels, and table values are unchanged.

Hashes and recomputation establish consistency with saved bytes and the specified implementation. They do not establish signed source authenticity, the exact release/revision time, economic causality, or predictive trading performance. Historical vintages and per-observation publication timestamps remain unavailable; historical point-in-time backtesting is unsupported.

The public allowlist contains original project material and synthetic examples only. Source-data rights remain separate. The MIT scope paragraph was moved verbatim from LICENSE into DATA_LICENSE.md; the grant, disclaimer, and rights boundary were preserved. GitHub license recognition must be checked after publication; this local check does not claim a platform classification result.
