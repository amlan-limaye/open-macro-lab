# Maintainer handoff

The minimum maintenance task is small: preserve four public series contracts, one versioned definition, the archive format, and the independent tests. Another author should be able to keep the publication running without the original author's accounts or machine.

## Routine update

1. Run the offline tests and verify the last good snapshot or complete issue.
2. Run `python3 -m open_macro_lab update --store data/live --output build/issues`. It inherits the latest known capture's retrieval window and method unless you explicitly override them.
3. Inspect the returned JSON and open its report path. Check the observation date, warnings, unchanged/new/revised counts, and interpretation. The first capture remains a baseline.
4. Run `python3 -m open_macro_lab verify-report REPORT_DIRECTORY` before transferring a report folder. Keep the attached evidence and the package version recorded in `report.json`.
5. Preserve old issues and releases. The update command writes one verified issue per capture ID and never replaces an old issue. It has no publish/send/deploy action.

For exact control, the separate `fetch`, `verify`, and `report --previous` commands remain available. An incomplete older capture does not prevent acquisition of a new complete one; its attribution bridge may be unavailable. Corrupt archive evidence stops the update before network access. If a capture succeeds but report writing fails, the snapshot is retained and the error identifies its path. Rerunning can recover the issue. If an existing issue fails verification or uses a different comparison, select a new output parent; do not overwrite its evidence.

There is no background job, hidden scheduler, auto-refresh, database service, user tracking, or market execution. Running the tool daily is allowed but often produces unchanged weekly observations. A daily reading should explain unchanged evidence instead of manufacturing a daily signal.

## Source change or acquisition failure

An HTTP error, metadata mismatch, malformed CSV, or invalid value aborts acquisition. Previously saved snapshots remain available for offline reports. Do not relabel that old issue as fresh; build with `--as-of now` to expose age. Inspect the official series page and H.4.1 release. If the endpoint or title changed, update the narrow adapter, add a meaningful regression test, and record the version change. Do not silently switch from Wednesday levels to weekly averages or from total RRP to overnight RRP.

Metadata checks assert the selected title and unit/cadence markers in the captured source page. This catches common endpoint/series drift, but is not a machine-readable official unit schema and cannot detect every upstream methodology change. Review any material H.4.1 definition notice manually before continuing a series.

## Methodology or engine changes

Preserve `v1.json`. Copy to a new version, explain the economic reason in a corresponding method document, revise coefficients and formula text together, bump the version, and add independent reference cases. Pass `--methodology` while building a comparison. Input identity/unit/basis changes are intentionally refused by this generic override; they need an engine and archive-contract change. All source changes should be versioned, and old package releases retained with old issues. The package version and source hash in report JSON identify the Python implementation but do not bundle every historical executable version automatically. `verify-report` deliberately refuses a different source hash; retain the original release or rebuild from evidence in a new directory. The verifier does not execute the report, contact the source, or certify source authenticity.

Snapshots embed the method current at ingestion. For subsequent captures with a revised definition, use `fetch --methodology PATH` so it remains attached to the evidence. An analysis-only experiment can use `report --methodology PATH`, but the v1 CLI compares against the **method embedded in the previous snapshot**, not an arbitrary earlier report. This boundary is explicit; do not claim that it automatically compares every successive editorial issue.

## Immutability and backups

Snapshot files are exclusive-created, made read-only, hash-checked, and never overwritten by the CLI. A content-derived directory ID anchors the manifest. Reports copy their evidence so the folder can move with its raw inputs. Failed acquisitions do not replace a good capture. Derived HTML/CSV/JSON can be rebuilt.

This is application-level append-only storage with tamper detection, not privileged WORM storage or signed provenance. The computer owner can change permissions and rewrite bytes; a fully malicious rewrite of hashes is not independently authenticated. Back up the whole project or snapshot directory. Keep original capture paths/IDs; renaming a snapshot directory invalidates its identity check. No retention deletion is automatic.

## Honest review boundary

Automated checks cover calculations, source contracts, missingness, stale age, no-lookahead, revision classes, methodology effects, evidence integrity, complete report reproduction, and report interactions in a Node mock DOM. Version 0.2.0 also has a repeatable clean-wheel installation check. See `VERIFICATION.md` for observed results and distinctions between simulated acquisition, saved real evidence, and browser verification.

The publisher reported desktop/narrow-screen verification of the prior visual fixes at source commit `72c0652ce84ebdda91e2b921d733e36e2993f212`. This workflow pass preserves those rendering fixes. It does not claim a new browser or screen-reader review. The scheduled real-release comparison remains separate from tests against the saved baseline.

## Deliberately out of scope

No market-price joins, predictive backtest, global aggregate, private data, proprietary feeds, portfolio, account, paid subscription system, ingestion platform, hosted API, or deployment. Historical vintage access would be a distinct future evidence feature, not a renamed current-vintage chart.
