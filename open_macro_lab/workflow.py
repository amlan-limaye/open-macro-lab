"""Capture-to-report workflow and offline verification of a complete research issue."""

import json
import os
import re
import tempfile
from pathlib import Path

from .analysis import analyze, engine_hash
from .core import ResearchError, canonical, load_method, timestamp, utcnow, validate_method
from .report import write_report
from .store import fetch_snapshot, load_snapshot
from .publication import load_evidence


def _evidence(root, identifier):
    if not isinstance(identifier, str) or not re.fullmatch(r"(?:official|synthetic|public)-[0-9a-f]{20}", identifier):
        raise ResearchError("Invalid report snapshot identifier")
    return load_evidence(root / "evidence" / identifier)


def verify_report(directory):
    """Recompute an issue from its attached evidence; never execute its HTML/JS."""
    root = Path(directory)
    payload = json.loads((root / "report.json").read_bytes())
    if not isinstance(payload, dict) or payload.get("schema") != 1 or payload.get("product") != "Open Macro Lab":
        raise ResearchError("Unsupported research report")
    snapshot = _evidence(root, payload["snapshot_id"])
    comparison = payload["comparison"]
    if not isinstance(comparison, dict) or comparison.get("status") not in ("first_snapshot", "compared"):
        raise ResearchError("Unsupported comparison status")
    previous = _evidence(root, comparison["previous_id"]) if comparison["status"] == "compared" else None
    method = load_method(root / "methodology.json")
    if payload["engine_sha256"] != engine_hash():
        raise ResearchError("Report engine differs from this installation. Use the original package version (%s), or rebuild from its saved evidence into a new output directory." % payload.get("package_version", "not recorded"))
    expected = analyze(snapshot, previous, payload["as_of"], method)
    if payload != expected:
        changed = sorted(key for key in set(payload) | set(expected) if payload.get(key) != expected.get(key))
        raise ResearchError("Research payload does not reproduce: " + ", ".join(changed))
    with tempfile.TemporaryDirectory(prefix="open-macro-lab-verify-") as temp:
        write_report(expected, snapshot, previous, temp)
        for name in ("history.csv", "index.html"):
            if (root / name).read_bytes() != (Path(temp) / name).read_bytes():
                raise ResearchError("Derived file does not reproduce: " + name)
    return {"status": "verified", "kind": payload["kind"], "snapshot_id": snapshot.id,
            "comparison": comparison["status"], "observation_date": payload["latest"]["date"],
            "as_of": payload["as_of"], "engine_sha256": payload["engine_sha256"],
            "checks": ["evidence hashes", "methodology", "research payload", "history.csv", "index.html"],
            "evidence_scope": payload.get("evidence_scope", {}).get("type", "complete_capture"),
            "scope": payload.get("evidence_scope", {}).get("verification", "Offline reproducibility, not source authenticity, historical publication timing, or browser rendering.")}


def update(store="data/live", output="build/issues", start=None, method=None):
    """Append one official capture and one verified issue; never replace an old issue."""
    archive, reports = Path(store).resolve(), Path(output).resolve()
    if reports == archive or archive in reports.parents:
        raise ResearchError("Report output must be outside the immutable snapshot archive")
    began = timestamp(utcnow())
    known = []
    for path in Path(store).glob("official-*"):
        saved = load_snapshot(path)  # Corrupt archives fail closed before acquisition.
        if timestamp(saved.manifest["captured_at"]) <= began:
            known.append(saved)
    known.sort(key=lambda saved: (timestamp(saved.manifest["captured_at"]), saved.id))
    seed = known[-1] if known else None
    method = method or (seed.method if seed else load_method())
    start = start or (seed.manifest["requested_start"] if seed else None) or "2024-01-01"
    validate_method(method)
    if seed:
        if method["series"] != seed.method["series"]:
            raise ResearchError("Methodology cannot silently reinterpret saved source contracts")
        if canonical(method) != canonical(seed.method) and method["version"] == seed.method["version"]:
            raise ResearchError("Methodology edits require a new version")
    snapshot = load_snapshot(fetch_snapshot(store, start, method))
    if snapshot.manifest["kind"] != "official":
        raise ResearchError("The update command requires an official capture")
    prior = [saved for saved in known if saved.id != snapshot.id
             and timestamp(saved.manifest["captured_at"]) <= timestamp(snapshot.manifest["captured_at"])]
    previous = prior[-1] if prior else None
    try:
        payload = analyze(snapshot, previous)
    except (ValueError, KeyError) as exc:
        raise ResearchError("No report was committed; saved snapshot remains at %s. %s" % (snapshot.path, exc)) from exc
    destination = Path(output) / snapshot.id
    if destination.exists():
        verify_report(destination)
        if json.loads((destination / "report.json").read_bytes()) != payload:
            raise ResearchError("An existing issue uses a different comparison; choose a new output directory")
        status = "reused"
    else:
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.TemporaryDirectory(prefix=".partial-", dir=destination.parent) as temp:
                write_report(payload, snapshot, previous, temp)
                verify_report(temp)
                os.rename(temp, destination)
            status = "created"
        except (OSError, ValueError, KeyError) as exc:
            raise ResearchError("Report was not committed; saved snapshot remains at %s. %s" % (snapshot.path, exc)) from exc
    return {"status": status, "kind": snapshot.manifest["kind"], "snapshot": str(snapshot.path),
            "previous": str(previous.path) if previous else None, "report": str(destination / "index.html"),
            "captured_at": payload["captured_at"], "observation_date": payload["latest"]["date"],
            "data_status": payload["status"], "warnings": payload["warnings"],
            "comparison": payload["comparison"]["status"], "change_counts": payload["comparison"]["counts"],
            "comparison_note": payload["comparison"]["message"], "interpretation": payload["interpretation"]}
