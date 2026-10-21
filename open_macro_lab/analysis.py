"""Build a transparent research payload without claiming historical availability."""

from collections import Counter
from datetime import date
from decimal import Decimal
from pathlib import Path

from .core import (ResearchError, aligned_rows, canonical, change_window,
                   classify_changes, revision_bridge, serializable, sha256, timestamp,
                   validate_method)


def engine_hash():
    root = Path(__file__).parent
    return sha256(b"".join(p.name.encode() + b"\0" + p.read_bytes() for p in sorted(root.glob("*.py"))))


def analyze(snapshot, previous=None, as_of=None, method=None):
    as_of = as_of or snapshot.manifest["captured_at"]
    if timestamp(as_of) < timestamp(snapshot.manifest["captured_at"]):
        raise ResearchError("Lookahead blocked: this snapshot was not captured by the requested as-of time")
    method = method or snapshot.method
    validate_method(method)
    if method["series"] != snapshot.method["series"]:
        raise ResearchError("Methodology cannot silently reinterpret saved source contracts")
    if canonical(method) != canonical(snapshot.method) and method["version"] == snapshot.method["version"]:
        raise ResearchError("Methodology edits require a new version")
    rows = aligned_rows(snapshot.data, method)
    complete = [r for r in rows if all(r[k] is not None for k in ("liquidity", "reserves", "gap"))]
    if not complete:
        raise ResearchError("No complete common Wednesday; no research conclusion can be computed")
    latest = complete[-1]
    age = (timestamp(as_of).date() - date.fromisoformat(latest["date"])).days
    missing = [r["date"] for r in rows if any(r[k] is None for k in ("liquidity", "reserves", "gap"))]
    warnings = []
    if age > method["stale_after_days"]:
        warnings.append("STALE: latest complete Wednesday is %d calendar days old as of %s." % (age, as_of))
    if missing:
        warnings.append("%d Wednesday(s) have missing inputs; gaps are retained, with no interpolation or forward fill." % len(missing))
    if latest["date"] < rows[-1]["date"]:
        warnings.append("Latest complete observation predates the newest input date; the headline uses the older complete date.")
    windows = {str(n): change_window(rows, n) for n in (1, 4, 13)}
    for win in windows.values():
        if win:
            win["contributions"] = {s: win["input_deltas"][s] * Decimal(w) for s, w in method["recipes"]["liquidity"]["coefficients"].items()}
            if sum(win["contributions"].values(), Decimal(0)) != win["liquidity"]:
                raise ResearchError("Attribution did not reconcile")
    comparison = {"status": "first_snapshot", "message": "First saved snapshot: no prior capture to test for revisions. This is a baseline, not evidence of unchanged history.", "events": [], "counts": {}, "bridge": None}
    if previous:
        if previous.manifest["kind"] != snapshot.manifest["kind"]:
            raise ResearchError("Synthetic and official snapshots cannot be compared")
        if timestamp(previous.manifest["captured_at"]) > timestamp(snapshot.manifest["captured_at"]):
            raise ResearchError("Previous snapshot was captured after the selected snapshot")
        method_changed = canonical(previous.method) != canonical(method)
        if method_changed and previous.method["version"] == method["version"]:
            raise ResearchError("Changed methodology has the same version; bump it before comparison")
        events = classify_changes(previous.data, snapshot.data)
        window_changed = previous.manifest["requested_start"] != snapshot.manifest["requested_start"]
        if window_changed:
            warnings.append("Retrieval coverage changed; the headline bridge is suppressed. Coverage additions/removals are not called revisions.")
            for event in events:
                s, d = event["series"], date.fromisoformat(event["date"])
                if event["kind"] == "historical_backfill" and d < min(previous.data[s]):
                    event["kind"] = "coverage_added"
                if event["kind"] == "removed_observation" and d < min(snapshot.data[s]):
                    event["kind"] = "coverage_removed"
        comparison = {"status": "compared", "previous_id": previous.id,
                      "previous_captured_at": previous.manifest["captured_at"],
                      "previous_methodology_version": previous.method["version"],
                      "methodology_changed": method_changed, "coverage_changed": window_changed,
                      "events": events, "counts": dict(Counter(e["kind"] for e in events)),
                      "raw_bytes_changed": [s for s in snapshot.data if snapshot.manifest["sources"][s]["sha256"] != previous.manifest["sources"][s]["sha256"]],
                      "bridge": None if window_changed else revision_bridge(previous.data, snapshot.data, previous.method, method),
                      "message": "Differences observed between saved captures. Revised values are detected at the source-series/date level; exact official revision times and causes are unknown."}
    sources = []
    for series, metadata in snapshot.manifest["sources"].items():
        valid = [d for d, v in snapshot.data[series].items() if v is not None]
        sources.append({"series": series, "label": method["series"][series]["label"], **metadata,
                        "latest_valid_observation": max(valid).isoformat(),
                        "latest_age_days": (timestamp(as_of).date() - max(valid)).days,
                        "evidence_path": "evidence/" + snapshot.id + "/" + metadata["file"]})
    four = windows["4"]
    interpretation = "The latest complete Wednesday is %s. " % latest["date"]
    if four:
        direction = "rose" if four["liquidity"] > 0 else "fell" if four["liquidity"] < 0 else "was unchanged"
        interpretation += "Over four calendar weeks the selected liquidity proxy %s by %s USD bn. " % (direction, abs(four["liquidity"]))
        dominant = max(four["contributions"], key=lambda s: abs(four["contributions"][s]))
        if four["contributions"][dominant] != 0:
            interpretation += "%s had the largest absolute accounting contribution (%+s USD bn). " % (method["series"][dominant]["label"], four["contributions"][dominant])
        interpretation += "Observed reserves changed by %s USD bn, while the proxy–reserve gap changed by %s USD bn. " % (four["reserves"], four["gap"])
    else:
        interpretation += "The four-week comparison is unavailable because its exact endpoint is absent or incomplete. "
    interpretation += "These movements describe selected balance-sheet positions; they do not identify a policy shock or establish an asset-price forecast."
    return serializable({"schema": 1, "product": "Open Macro Lab", "provisional_name": True,
                         "snapshot_id": snapshot.id, "kind": snapshot.manifest["kind"],
                         "captured_at": snapshot.manifest["captured_at"], "as_of": as_of,
                         "engine_sha256": engine_hash(), "methodology": method,
                         "methodology_sha256": sha256(canonical(method)), "latest": latest,
                         "observation_age_days": age, "status": "stale" if age > method["stale_after_days"] else "within_age_threshold",
                         "warnings": warnings, "missing_dates": missing, "rows": rows,
                         "windows": windows, "comparison": comparison, "sources": sources,
                         "interpretation": interpretation,
                         "confidence": {"arithmetic": "Exact decimal accounting, checked input contracts and matching observation dates.",
                                        "economic": "Descriptive proxy with incomplete balance-sheet coverage; no causal or predictive confidence claim.",
                                        "temporal": "Current-vintage monitoring. Archive-known availability only, beginning with saved captures; no historical PIT backtest."}})
