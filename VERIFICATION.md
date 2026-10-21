# Verification scope for v0.1.0

Reviewed 2026-10-21. Original runtime and methodology 1.0.0 are unchanged; this release prepares documentation, packaging, and shareable examples only.

## Automated and independent checks

- The original local project passes **52 tests**, including the saved official reference case.
- The public source distribution runs the same 52-test suite: **51 pass and one optional official-snapshot test skips**, because the full original real capture is deliberately not bundled.
- Offline checks cover independent hand calculations, units/currency/frequency/basis/seasonal-adjustment mismatches, duplicate/malformed/future observations, missing endpoints and interior gaps, stale-age boundaries, no-lookahead archive selection, revision classes, exact methodology effects, and raw/manifest tamper detection.
- Synthetic numerical reference: **5,925 + 2 + 13 + 0 = 5,940 USD bn**, with four invented new cells and two invented prior-value changes. These are not real revision observations.
- The [independent baseline audit](docs/BASELINE_AUDIT.md) recomputed all **146 weeks** and separately rechecked **20 official input cells**. Its scope is accounting, alignment, source semantics, and availability claims; it does not establish economic causality or market performance.
- HTML/content checks cover required caveats and synthetic labels, finite SVG coordinates, unique IDs, local evidence-link resolution, and absence of externally loaded assets.
- Range-control code is checked with a minimal Node DOM substitute. This tests the selection behavior in that substitute, not real browser layout, accessibility, or rendering.
- Public release preparation uses an exact file allowlist and SHA-256 inventory. The inspected payload excludes private material, host-specific paths, original live captures and source HTML, caches, and unreviewed files. Pattern scanning is a bounded safeguard, not a proof that all possible secrets can be detected.

```sh
python3 -m unittest discover -s tests -v
python3 scripts/check_report.py examples/synthetic
node scripts/check_interactions.js examples/synthetic/index.html
python3 scripts/package_release.py
```

Node is needed only for the optional interaction check. Python package/report runtime uses no third-party dependencies. The ZIP is intended for local source distribution; the packaging command never publishes.

## Not yet verified

Actual desktop/mobile rendering, real-browser clicks/downloads, screen-reader behavior, and print rendering remain **pending**. No browser, mouse, keyboard, localhost server, or denied preview route was used during release preparation. Authored responsive CSS and static content checks are not claimed as visual verification. See the [later validation plan](docs/VALIDATION_PLAN.md).

The real baseline is one capture. Official revisions between captures are therefore not yet measured. Historical per-observation publication timestamps and vintage access remain unavailable; a historical PIT backtest is unsupported. Neither the tests nor the audit establish a predictive trading edge.
