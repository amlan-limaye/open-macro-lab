# Maintainer handoff

The minimum maintenance task is small: preserve four public series contracts, one versioned definition, the archive format, and the independent tests. Another author should be able to keep the publication running without the original author's accounts or machine.

## Routine update

1. Run the offline tests and verify the last good snapshot.
2. Run `fetch` with the same `--start` window. It fetches official public FRED CSVs and metadata with ordinary certificate verification. Do not add credentials or turn TLS checking off to make an endpoint work.
3. Build with the printed new snapshot path and explicit `--previous` last good path. Check age, latest common date, missing data, and the archive change ledger before interpreting a change.
4. Keep the raw inputs and method alongside each saved issue. For a publication, obtain separate authorization; this CLI has no publish/send/deploy action.

There is no background job, hidden scheduler, auto-refresh, database service, user tracking, or market execution. Running the tool daily is allowed but often produces unchanged weekly observations. A daily reading should explain unchanged evidence instead of manufacturing a daily signal.

## Source change or acquisition failure

An HTTP error, metadata mismatch, malformed CSV, or invalid value aborts acquisition. Previously saved snapshots remain available for offline reports. Do not relabel that old issue as fresh; build with `--as-of now` to expose age. Inspect the official series page and H.4.1 release. If the endpoint or title changed, update the narrow adapter, add a meaningful regression test, and record the version change. Do not silently switch from Wednesday levels to weekly averages or from total RRP to overnight RRP.

Metadata checks assert the selected title and unit/cadence markers in the captured source page. This catches common endpoint/series drift, but is not a machine-readable official unit schema and cannot detect every upstream methodology change. Review any material H.4.1 definition notice manually before continuing a series.

## Methodology or engine changes

Preserve `v1.json`. Copy to a new version, explain the economic reason in a corresponding method document, revise coefficients and formula text together, bump the version, and add independent reference cases. Pass `--methodology` while building a comparison. Input identity/unit/basis changes are intentionally refused by this generic override; they need an engine and archive-contract change. All source changes should be versioned, and old package releases retained with old issues. The source hash in report JSON identifies the Python implementation but does not bundle every historical executable version automatically.

Snapshots embed the method current at ingestion. For subsequent captures with a revised definition, use `fetch --methodology PATH` so it remains attached to the evidence. An analysis-only experiment can use `report --methodology PATH`, but the v1 CLI compares against the **method embedded in the previous snapshot**, not an arbitrary earlier report. This boundary is explicit; do not claim that it automatically compares every successive editorial issue.

## Immutability and backups

Snapshot files are exclusive-created, made read-only, hash-checked, and never overwritten by the CLI. A content-derived directory ID anchors the manifest. Reports copy their evidence so the folder can move with its raw inputs. Failed acquisitions do not replace a good capture. Derived HTML/CSV/JSON can be rebuilt.

This is application-level append-only storage with tamper detection, not privileged WORM storage or signed provenance. The computer owner can change permissions and rewrite bytes; a fully malicious rewrite of hashes is not independently authenticated. Back up the whole project or snapshot directory. Keep original capture paths/IDs; renaming a snapshot directory invalidates its identity check. No retention deletion is automatic.

## Honest review boundary

Automated checks cover calculations, units, currencies, frequency/basis, missingness, stale age, no-lookahead, revision classes, methodology effects, evidence integrity, links, and report content. A responsive stylesheet is included, but actual browser rendering, narrow-screen visual inspection, print rendering, and click behavior in a real browser remain pending. See `VALIDATION_PLAN.md` for the scoped later review; content checks alone are not visual verification.

## Deliberately out of scope

No market-price joins, predictive backtest, global aggregate, private data, proprietary feeds, portfolio, account, paid subscription system, ingestion platform, hosted API, or deployment. Historical vintage access would be a distinct future evidence feature, not a renamed current-vintage chart.
