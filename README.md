# Open Macro Lab

**Executable US macro research with inspectable inputs, calculations, and explanations of changed readings.** Version 0.2.0; working name.

Two linked recipes describe the Federal Reserve balance sheet. The package uses Python's standard library, four public data series, exact arithmetic, immutable captured inputs, and a local HTML research report. No API key or account is required.

- **Selected US liquidity proxy:** `L = (WALCL − WDTGAL − WLRRAL) / 1000`, in USD billions. This is assets net of the Treasury general account and **total reverse-repo liabilities**, including foreign official accounts. It differs from a formula subtracting only overnight RRP.
- **Reserve cross-check:** `R = WRBWFRBL / 1000`, `G = L − R`. The proxy and reserves share an accounting identity; this is a linked accounting comparison, not independent economic validation.

Both use unadjusted Wednesday levels. The proxy is not global liquidity, broad money, investable cash, a causal model, or a demonstrated predictive signal. This is research and education software, with no live trading or investment recommendation.

## Start in two minutes

Download or clone this repository, then choose a source checkout or a virtual environment. The project is not claimed to be published on PyPI.

For an installed CLI, from the repository root:

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install .
open-macro-lab --version
open-macro-lab demo
open-macro-lab verify-report build/demo
```

On Windows, activate with `.venv\Scripts\activate`. Building an installation may download the declared setuptools build dependency; the installed research package has **zero runtime dependencies**. The CLI works outside the checkout. To avoid installation and network altogether, use the source commands below.

## Try it offline

Python 3.9 or later; no installation or network is needed. From the repository root:

```sh
python3 -m open_macro_lab demo
python3 -m open_macro_lab verify-report build/demo
python3 -m unittest discover -s tests -v
```

The demo writes `build/demo/index.html`, `report.json`, `history.csv`, `methodology.json`, and raw evidence. The generated report is a local file; keep its folder together to preserve evidence links.

A ready-made [synthetic example](examples/synthetic/index.html) is included. Its values, capture dates, and revisions are **deliberately fabricated**. It demonstrates an exact bridge of **5,925 + 2 prior-data effect + 13 new-endpoint effect + 0 method effect = 5,940 USD bn**. It is not a historical official revision record. The [hosted demonstration](https://amlan-limaye.github.io/open-macro-lab/) contains synthetic data; your own saved report opens locally. The hosted copy is a separate deployment and may lag the source version.

The report includes component histories, exact 1/4/13-week comparisons, formulas, interpretation, limitations, original input dates, a changed-observation ledger, and CSV/JSON evidence. No remote scripts, fonts, tracking, or backend service are required.

## One command for an official research issue

```sh
python3 -m open_macro_lab update --store data/live --output build/issues
```

This captures the four official sources, validates them, selects the most recent prior capture already known to the archive, computes the comparison, and verifies the complete report before committing it. JSON output gives the report path, capture and observation dates, data warnings, change counts, and an interpretation. Open the printed `report` path locally.

The **first run is a baseline**, with no revision claim. Later runs compare saved observations. Unchanged values are explicitly reported as unchanged. Each issue is saved to `build/issues/SNAPSHOT_ID/`; existing issues are not overwritten. The report directory must be outside the snapshot archive. Running the command is an explicit one-time action, not a scheduler.

The retrieval start and methodology inherit from the latest prior capture. For the first capture the start defaults to `2024-01-01`; set `--start YYYY-MM-DD` explicitly to change coverage. Coverage changes remain disclosed and suppress the attribution bridge. `--methodology PATH` requires an explicitly versioned change; the shipped definition remains 1.0.0.

A failed download preserves the prior archive and issue. If report construction fails after acquisition, the validated capture is retained and its path is reported; rerun or use the manual command below. Corrupt prior evidence fails before fetching. The CLI never silently substitutes synthetic data for a failed official request.

## Capture and reproduce manually

`fetch` reads the four official FRED series and their metadata over certificate-verified HTTPS. It preserves original response bytes and retrieval times, verifies the metadata contract, and commits a complete snapshot only after validation.

```sh
python3 -m open_macro_lab fetch --store data/live --start 2024-01-01
```

Use the path printed by `fetch` in place of `SNAPSHOT_PATH`:

```sh
python3 -m open_macro_lab verify SNAPSHOT_PATH
python3 -m open_macro_lab report --snapshot SNAPSHOT_PATH --output build/live
```

On a later capture, compare against the saved previous path:

```sh
python3 -m open_macro_lab report \
  --snapshot NEW_SNAPSHOT_PATH --previous PREVIOUS_SNAPSHOT_PATH \
  --as-of now --output build/latest
```

Network access is needed only for `fetch`. Use a Python environment with a functioning trusted certificate store; do not disable TLS verification to work around a certificate error. The generated `data/` and `build/` folders are ignored by Git. Review data rights before separately distributing a new capture, especially its source HTML metadata.

## Verify a received report offline

Keep the report directory together with `evidence/`, then run:

```sh
python3 -m open_macro_lab verify-report build/demo
```

The check validates attached input hashes, loads the effective method, recomputes all research fields, and compares the CSV and HTML byte-for-byte with regenerated output. It returns JSON and exits 0 on success, 2 on invalid evidence or output. It never executes report scripts or contacts a source.

Verification requires the same Python source hash used to create the issue. `report.json` records the package version and source hash; keep its package release. A different version fails with instructions to use the original release or rebuild into a new directory. This is reproducibility and tamper detection, **not signed source authenticity, validation of historical release times, or browser QA**. The older `verify SNAPSHOT_PATH` command remains available for raw snapshots alone.

## Why a reading changed

The cell log distinguishes new observations, changed prior values, historical backfills, filled or newly missing values, and removed observations. Numeric formatting changes are not called revisions. A changed retrieval window is disclosed and suppresses the headline bridge.

For comparable complete endpoints, the numerical bridge applies three steps:

1. Update values at the previous endpoint under the old methodology.
2. Move to the new endpoint, still under the old methodology.
3. Apply the new methodology at that new endpoint.

These effects reconcile exactly to the changed result. Revisions elsewhere in history remain visible even when the headline does not move. This is an ordered accounting decomposition; it does not establish the economic cause or timestamp of an official revision.

## Observation dates are not publication dates

Reports use current-vintage history from a selected capture. Historical per-observation publication dates and vintages are not retrieved. A first capture supplies no revision evidence; it is a baseline, not evidence of unchanged history.

`report` defaults its as-of time to capture completion for reproducibility. `--as-of now` evaluates present age; the stale warning starts after 10 calendar days since the latest complete Wednesday. This is an operational threshold, not a release calendar.

To select a capture this archive actually knew by a timezone-qualified timestamp, use `report --store data/live --as-of ISO_TIMESTAMP`. Requests before the first saved capture fail. This conservative archive-known view does **not** constitute a historical point-in-time backtest.

The [real baseline audit](docs/BASELINE_AUDIT.md) documents the separate original capture: 146 weeks through 2026-10-14, with all derived rows independently recomputed and 20 official input cells rechecked. The original captured FRED webpages and full real snapshot are not bundled in this public source release. The existing optional real-snapshot test therefore skips here; all other tests run offline. The acquisition integration tests use fabricated responses in temporary directories, not observed official revisions.

## Method and maintenance

- [Methodology 1.0.0](docs/METHODOLOGY-v1.md) and [executed JSON definition](open_macro_lab/methodologies/v1.json)
- [Maintainer handoff](docs/MAINTAINING.md)
- [Verification scope](VERIFICATION.md) and [0.2.0 workflow changes/evidence](docs/WORKFLOW-0.2.0.md)
- [Next-release check and later visual review](docs/VALIDATION_PLAN.md)
- [Prior-art and license review](docs/PRIOR_ART.md)

Snapshots embed the method and its hash. Research payloads also hash the Python implementation. Preserve old methods and captures. Intentional methodology edits must change `version`; pass `--methodology PATH` to `fetch` to retain the new method in a capture, or to `report` for an explicitly analysis-only experiment. Source contract changes require a deliberate engine/recipe change and tests.

## Public release contents

`PUBLIC_FILES.txt` is the exact file allowlist. `PUBLIC_MANIFEST.json` records each payload file's SHA-256 and size. `python3 scripts/package_release.py` verifies those bytes and creates a deterministic source ZIP under `dist/`; it performs no network or GitHub action.

Included: original source, tests, documentation, method definition, synthetic fixtures, and the synthetic report with its evidence. Excluded: credentials, personal machine paths, private messages, original live captures, captured source webpages, browser profiles, caches, local logs, and unrelated projects. Version 0.2.0 adds workflow and verification code. The economic method, arithmetic engine, synthetic input bytes, and original audited baseline are unchanged; the [verification record](VERIFICATION.md) states the new checks and their limits.

## Build and test a distributable package

```sh
python3 -m unittest discover -s tests -v
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 scripts/check_install.py dist/open_macro_lab-0.2.0-py3-none-any.whl
```

The install check creates a disposable environment, installs only the supplied wheel without network access, runs the console command outside the checkout, and verifies its generated synthetic report. Building the wheel may require the declared build dependency. `scripts/package_release.py` separately verifies the public allowlist and builds the reviewed source ZIP.

## License and attribution

Original code, documentation, and synthetic fixtures: [MIT](LICENSE). Source-data rights remain separate; see [DATA_LICENSE.md](DATA_LICENSE.md). The selected official Board series are tagged public domain with citation requested; source attribution and all limitations remain attached to the research. There is no Board or FRED endorsement.

Relevant prior art includes [macro-liquidity-pipeline](https://github.com/lauren-shih/macro-liquidity-pipeline), [macro-data-service](https://github.com/R1cK-ChaN/macro-data-service), and [puremacro](https://github.com/jalonso1979/puremacro). No third-party source code was copied or imported. The contribution is a small maintainable executable research publication, not a claim of novel ingestion technology.
