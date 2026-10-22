# Verification scope for v0.3.0

Reviewed 2026-10-22. **Ready within the locally reviewed scope**, with GitHub execution and new rendered visual review still pending. This version adds a dated official numerical demonstration, a distinct public evidence/export format, and read-only test CI. Methodology 1.0.0, the arithmetic core, original input bytes, and all baseline calculations remain unchanged. Earlier releases are preserved.

## Observed local results

- **97 tests: 96 pass and one optional full official-capture test skips**, on Python 3.9.6 and 3.13.7 on macOS. The original full capture is deliberately not bundled; the public numerical report has its own checks.
- The existing suite covers independent hand calculations; unit/currency/frequency/basis/seasonal mismatches; malformed/future observations; missing endpoints/interior gaps; stale age; no-lookahead; revision classes; method/data bridges; hash tampering; report verification; update/recovery behavior; singular-day grammar; and accessible scroll cues.
- The 21 new publication tests cover strict file/field allowlisting, actual-date preservation, backdating rejection, no synthetic-to-official export, private-capture removal followed by public-only reproduction, refusal of silently stripped full captures, tampered data/declarations/statistics, explicit verification scope, a fabricated two-capture comparison, and safe site staging. Acquisition/comparison fixtures are deliberately invented and do not establish actual official revisions.
- Both included reports reproduce offline. Content checks find valid local evidence links, no duplicate IDs, matching range controls, correct arithmetic and labels, and no externally loaded resources. Node mock DOM checks cover range selection, overflow cues, keyboard descriptions, resize, and disclosures. **These are not browser or screen-reader checks.**
- The source-independent arithmetic checker reconciles **all 146 real weeks and 584 input cells**, all three derived quantities in JSON/CSV, and available exact-calendar comparisons. Its [machine-readable result](docs/audit/public-arithmetic-0.3.0.json) records the scope. It imports no research engine and performs no reacquisition of historical releases.
- The saved original and public export have byte-identical four input CSVs and methodology. Every calculated row, latest value, calendar comparison, interpretation and baseline comparison state matches the original retained report. No new official acquisition or observed revision comparison occurred.
- The wheel built with the existing local build dependency and no network. Empty Python 3.9.6 and 3.13.7 environments installed the wheel without network and exercised the console entry point, isolated module, packaged fixtures/method/license notices, offline synthetic demo, report verification, and `pip check`. Each also copied only the public real-data folder outside the checkout and reproduced HTML, JSON, CSV and method bytes. Runtime dependencies remain empty.
- UTF-8 reads are explicit in verification scripts/tests, and `.gitattributes` preserves evidence/source bytes across checkouts. The Windows CI job is prepared, but a Windows execution is not claimed from these macOS results.

## Public evidence boundary

The original capture completed **2026-10-21T11:37:11+00:00**, with observations through **2026-10-14**. The numerical export was created **2026-10-22T10:32:28+00:00**. These dates are not interchangeable. The prior [independent audit](docs/BASELINE_AUDIT.md) recomputed 146 weeks and independently rechecked 20 recent official input cells; this release does not claim that every historical row was checked against its original release.

The public `verify-report` path explicitly returns `evidence_scope: numerical_export`. It reproduces published numerical evidence and declarations, computations, CSV and HTML. It cannot repeat source-page metadata checks because captured FRED HTML is excluded. Original full captures retain the stricter verifier; removing their required metadata files does not convert them into valid public exports. See [PUBLIC_EVIDENCE.md](docs/PUBLIC_EVIDENCE.md) for exact files, commands and limitations.

First capture means baseline, not zero revisions or unchanged history. Historical vintages and per-observation publication timestamps remain unavailable. Hashes detect inconsistent bytes but are not signed source authenticity. No historical point-in-time backtest, economic causality, or predictive trading performance is established. The synthetic example remains explicitly invented: **5,925 + 2 prior-data effect + 13 new-endpoint effect + 0 method effect = 5,940 USD bn**.

## CI and deployment scope

The new test workflow uses only `contents: read`, no secrets, and full commit pins for official checkout/setup actions. It covers Linux/Python 3.9 and Windows/Python 3.13: tests, build, clean installation outside checkout, offline examples, report verification, independent arithmetic, and safe staging/source packaging. Local YAML checks confirm the matrix, pinned action syntax, no persisted checkout credentials, and permission boundary. **GitHub Actions execution remains pending publication; local checks do not prove a remote run.**

The separate existing Pages workflow remains manual. It requires the full reviewed source commit SHA and verifies the reports and `SITE_FILES.json` before staging. Its `contents: read`, `pages: write`, and `id-token: write` job permissions are unchanged. The staging allowlist includes only the dated official report at `/`, the synthetic report at `/synthetic/`, and project/data license notices. No raw source-page HTML, private capture directory or source checkout is uploaded by this plan. This build task performs no deployment.

## Repeat the checks

```sh
python3 -m unittest discover -s tests -v
python3 -m open_macro_lab verify-report examples/official
python3 -m open_macro_lab verify-report examples/synthetic
python3 scripts/check_public_example.py examples/official
python3 scripts/check_report.py examples/official examples/synthetic
node scripts/check_interactions.js examples/official/index.html examples/synthetic/index.html
python3 -m pip wheel --no-deps --wheel-dir dist .
python3 scripts/check_install.py dist/open_macro_lab-0.3.0-py3-none-any.whl --public-report examples/official
python3 scripts/stage_site.py --output build/site
python3 scripts/package_release.py
```

Staging requires a new output directory and checks the reviewed source manifest before copying. A wheel build may download the declared setuptools dependency; running the package or installing an already built wheel with the supplied check uses no network.

## Pending separate checks

The publisher previously verified the singular-day and narrow-screen overflow fixes at source commit `72c0652ce84ebdda91e2b921d733e36e2993f212`; they are preserved. The new date notice, native-unit calculation trace and public evidence panel still need desktop/narrow-screen screenshots after authorized deployment. This task performed no browser, native app, localhost server, or file-URL action. The separately scheduled genuine official-release comparison is also still pending and has not been replaced with a synthetic event.

Code/docs/synthetic fixtures remain MIT. The selected official numerical series retain their separate source rights and attributions. The license grant and existing scope paragraph are unchanged; see [DATA_LICENSE.md](DATA_LICENSE.md).
