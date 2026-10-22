"""Explicit numerical exports: no captured source HTML, new capture, or publication."""

import json
import os
import re
import tempfile
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from .core import ResearchError, canonical, parse_csv, sha256, timestamp, utcnow, validate_method
from .store import SERIES, Snapshot, _write_once, load_snapshot

ARTIFACT = "open-macro-lab-numerical-export"
OMITTED = ["Captured source HTML and site assets", "Private capture directory and original full manifest"]
SCOPE = ("Published numerical input hashes, declared contracts, calculations, CSV and HTML output. "
         "Original source-page metadata checks cannot be repeated because those webpages are omitted. "
         "Neither signed source authenticity nor historical release/revision times are verified.")
ORIGIN = "Board of Governors of the Federal Reserve System (US), H.4.1, via FRED"
LICENSE = "Public Domain: Citation Requested; see DATA_LICENSE.md"
AVAILABILITY = "captured_at is the original archive retrieval completion; exported_at is this numerical export's creation, not a new observation or historical publication date."
SOURCE_FIELDS = {"file", "sha256", "bytes", "retrieved_at", "url", "source_page", "origin", "license",
                 "publication_dates", "contract", "observations", "missing_values", "first_observation", "last_observation"}
MANIFEST_FIELDS = {"schema", "artifact", "kind", "captured_at", "exported_at", "original_snapshot_id",
                   "original_manifest_sha256", "requested_start", "methodology_version", "methodology_sha256",
                   "sources", "files", "omitted", "availability_policy"}


def _source_url(url, series, start):
    parsed = urlparse(url)
    if (parsed.scheme != "https" or parsed.netloc != "fred.stlouisfed.org" or parsed.path != "/graph/fredgraph.csv"
            or parsed.fragment or parse_qs(parsed.query) != {"id": [series], "cosd": [start]}):
        raise ResearchError("Numerical export requires the documented FRED source URL for " + series)


def load_public_snapshot(path):
    """Validate only the explicitly published evidence; omitted HTML is not verified."""
    root = Path(path)
    raw = (root / "manifest.json").read_bytes()
    fingerprint = (root / "manifest.sha256").read_text().strip()
    if sha256(raw) != fingerprint or root.name != "public-" + fingerprint[:20]:
        raise ResearchError("Public evidence identity/hash mismatch")
    m = json.loads(raw)
    if set(m) != MANIFEST_FIELDS or m["schema"] != 1 or m["artifact"] != ARTIFACT or m["kind"] != "official":
        raise ResearchError("Unsupported public numerical evidence schema")
    if m["omitted"] != OMITTED or m["availability_policy"] != AVAILABILITY or timestamp(m["exported_at"]) < timestamp(m["captured_at"]):
        raise ResearchError("Invalid numerical export scope or chronology")
    original = m["original_manifest_sha256"]
    if not re.fullmatch(r"[0-9a-f]{64}", original) or m["original_snapshot_id"] != "official-" + original[:20]:
        raise ResearchError("Invalid original capture reference")
    expected = {"methodology.json"} | {"raw/" + s + ".csv" for s in SERIES}
    if set(m["files"]) != expected or set(m["sources"]) != set(SERIES):
        raise ResearchError("Unexpected public numerical input set")
    for entry in root.rglob("*"):
        relative = entry.relative_to(root).as_posix()
        if (entry.is_symlink() or (entry.is_dir() and relative != "raw")
                or (entry.is_file() and relative not in expected | {"manifest.json", "manifest.sha256"})):
            raise ResearchError("Unlisted or unsafe public evidence: " + relative)
    for name, digest in m["files"].items():
        if sha256((root / name).read_bytes()) != digest:
            raise ResearchError("Public numerical evidence hash mismatch: " + name)
    method = json.loads((root / "methodology.json").read_bytes())
    validate_method(method)
    if m["methodology_sha256"] != m["files"]["methodology.json"] or m["methodology_version"] != method["version"]:
        raise ResearchError("Public methodology identity mismatch")
    data = {}
    for s, meta in m["sources"].items():
        name = "raw/" + s + ".csv"
        if set(meta) != SOURCE_FIELDS or meta["file"] != name or meta["sha256"] != m["files"][name]:
            raise ResearchError("Public source identity mismatch")
        if meta["contract"] != method["series"][s] or timestamp(meta["retrieved_at"]) > timestamp(m["captured_at"]):
            raise ResearchError("Invalid public source contract or retrieval chronology")
        _source_url(meta["url"], s, m["requested_start"])
        if meta["origin"] != ORIGIN or meta["license"] != LICENSE or meta["source_page"] != "https://fred.stlouisfed.org/series/" + s:
            raise ResearchError("Missing public source attribution")
        if meta["publication_dates"] != "unknown; not supplied by this CSV":
            raise ResearchError("Historical publication dates must remain explicitly unknown")
        content = (root / name).read_bytes()
        records = parse_csv(content, s, meta["contract"], meta["retrieved_at"])
        for key, value in {"bytes": len(content), "observations": len(records),
                           "missing_values": sum(v is None for v in records.values()),
                           "first_observation": min(records).isoformat(), "last_observation": max(records).isoformat()}.items():
            if meta[key] != value:
                raise ResearchError("Public source statistics mismatch: " + s + " / " + key)
        data[s] = records
    return Snapshot(root, m, method, data)


def load_evidence(path):
    return load_public_snapshot(path) if Path(path).name.startswith("public-") else load_snapshot(path)


def export_snapshot(snapshot, store, exported_at):
    """Copy an allowlisted numerical projection; preserve actual capture/retrieval dates."""
    if snapshot.manifest.get("schema") != 1 or snapshot.manifest.get("kind") != "official" or "artifact" in snapshot.manifest:
        raise ResearchError("Export requires an original official capture, not synthetic or already exported data")
    if timestamp(exported_at) < timestamp(snapshot.manifest["captured_at"]):
        raise ResearchError("Export cannot precede the original capture")
    files = {"methodology.json": (snapshot.path / "methodology.json").read_bytes()}
    sources = {}
    for s in SERIES:
        original = snapshot.manifest["sources"][s]
        name = "raw/" + s + ".csv"
        files[name] = (snapshot.path / name).read_bytes()
        _source_url(original["url"], s, snapshot.manifest["requested_start"])
        records = snapshot.data[s]
        sources[s] = {"file": name, "sha256": sha256(files[name]), "bytes": len(files[name]),
                      "retrieved_at": original["retrieved_at"], "url": original["url"],
                      "source_page": "https://fred.stlouisfed.org/series/" + s, "origin": ORIGIN, "license": LICENSE,
                      "publication_dates": "unknown; not supplied by this CSV", "contract": snapshot.method["series"][s],
                      "observations": len(records), "missing_values": sum(v is None for v in records.values()),
                      "first_observation": min(records).isoformat(), "last_observation": max(records).isoformat()}
    m = {"schema": 1, "artifact": ARTIFACT, "kind": "official", "captured_at": snapshot.manifest["captured_at"],
         "exported_at": exported_at, "original_snapshot_id": snapshot.id,
         "original_manifest_sha256": sha256((snapshot.path / "manifest.json").read_bytes()),
         "requested_start": snapshot.manifest["requested_start"], "methodology_version": snapshot.method["version"],
         "methodology_sha256": sha256(files["methodology.json"]), "sources": sources,
         "files": {name: sha256(raw) for name, raw in files.items()}, "omitted": OMITTED,
         "availability_policy": AVAILABILITY}
    raw = canonical(m)
    root = Path(store); root.mkdir(parents=True, exist_ok=True)
    destination = root / ("public-" + sha256(raw)[:20])
    if destination.exists():
        return load_public_snapshot(destination)
    with tempfile.TemporaryDirectory(prefix=".partial-", dir=root) as temp:
        stage = Path(temp); (stage / "raw").mkdir()
        for name, content in files.items():
            _write_once(stage / name, content)
        _write_once(stage / "manifest.json", raw)
        _write_once(stage / "manifest.sha256", (sha256(raw) + "\n").encode())
        os.rename(stage, destination)
    return load_public_snapshot(destination)


def public_scope(snapshot, previous=None):
    selected = [s for s in (snapshot, previous) if s is not None]
    exported = [s for s in selected if s.manifest.get("artifact") == ARTIFACT]
    if not exported:
        return None
    if len(exported) != len(selected):
        raise ResearchError("A public report must use numerical exports for both captures")
    return {"type": "numerical_export", "verification": SCOPE, "omitted": OMITTED,
            "exports": [{"id": s.id, "exported_at": s.manifest["exported_at"],
                         "original_snapshot_id": s.manifest["original_snapshot_id"],
                         "original_manifest_sha256": s.manifest["original_manifest_sha256"]} for s in selected]}


def export_public_report(snapshot_path, output, previous_path=None):
    """Prepare an offline public artifact. No upload, fresh acquisition, or scheduler."""
    from .analysis import analyze
    from .report import write_report
    from .workflow import verify_report
    snapshot = load_snapshot(snapshot_path)
    previous = load_snapshot(previous_path) if previous_path else None
    destination = Path(output)
    if destination.exists():
        raise ResearchError("Public export requires a new output directory; preserve earlier issues")
    for saved in (snapshot, previous):
        if saved and (destination.resolve() == saved.path.resolve() or saved.path.resolve() in destination.resolve().parents):
            raise ResearchError("Public export must be outside the private capture")
    # Validate chronology/method compatibility before creating any output.
    analyze(snapshot, previous)
    exported_at = utcnow()
    destination.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".public-", dir=destination.parent) as temp:
        root = Path(temp)
        public = export_snapshot(snapshot, root / "evidence", exported_at)
        prior = export_snapshot(previous, root / "evidence", exported_at) if previous else None
        write_report(analyze(public, prior), public, prior, root)
        verify_report(root)
        os.rename(root, destination)
    return destination / "index.html"
