"""Append-only, hash-checked local evidence. No historical release dates are guessed."""

import html
import json
import os
import re
import shutil
import ssl
import tempfile
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from .core import (ResearchError, canonical, load_method, parse_csv, sha256,
                   timestamp, utcnow, validate_contract, validate_method)

SERIES = ("WALCL", "WDTGAL", "WLRRAL", "WRBWFRBL")


@dataclass
class Snapshot:
    path: Path
    manifest: dict
    method: dict
    data: dict

    @property
    def id(self):
        return self.path.name


def _write_once(path, raw):
    with path.open("xb") as handle:
        handle.write(raw)
        handle.flush()
        os.fsync(handle.fileno())
    path.chmod(0o444)


def create_snapshot(store, inputs, provenance, captured_at, kind="synthetic", method=None, start=None):
    if kind not in ("synthetic", "official"):
        raise ResearchError("Unknown snapshot kind")
    method = method or load_method()
    validate_method(method)
    timestamp(captured_at)
    if set(inputs) != set(SERIES) or set(provenance) != set(SERIES):
        raise ResearchError("A snapshot requires all four sources")
    files, sources = {}, {}
    for series in SERIES:
        p = dict(provenance[series])
        if timestamp(p["retrieved_at"]) > timestamp(captured_at):
            raise ResearchError("Capture must finish after all input retrievals")
        records = parse_csv(inputs[series], series, method["series"][series], p["retrieved_at"])
        p.update({"file": "raw/" + series + ".csv", "sha256": sha256(inputs[series]),
                  "bytes": len(inputs[series]), "observations": len(records),
                  "missing_values": sum(v is None for v in records.values()),
                  "first_observation": min(records).isoformat(), "last_observation": max(records).isoformat(),
                  "publication_dates": "unknown; not supplied by this CSV",
                  "contract": method["series"][series]})
        metadata = p.pop("metadata_bytes", None)
        files[p["file"]] = inputs[series]
        if metadata is not None:
            p["metadata_file"] = "raw/" + series + "-metadata.html"
            p["metadata_sha256"] = sha256(metadata)
            files[p["metadata_file"]] = metadata
        sources[series] = p
    files["methodology.json"] = canonical(method)
    manifest = {"schema": 1, "kind": kind, "captured_at": captured_at,
                "requested_start": start, "sources": sources, "methodology_version": method["version"],
                "methodology_sha256": sha256(files["methodology.json"]),
                "files": {p: sha256(b) for p, b in files.items()},
                "availability_policy": "All rows become known to this archive at captured_at, never at observation_date."}
    raw_manifest = canonical(manifest)
    identifier = kind + "-" + sha256(raw_manifest)[:20]
    root = Path(store)
    root.mkdir(parents=True, exist_ok=True)
    destination = root / identifier
    if destination.exists():
        existing = load_snapshot(destination)
        if canonical(existing.manifest) != raw_manifest:
            raise ResearchError("Snapshot identifier collision")
        return destination
    staging = Path(tempfile.mkdtemp(prefix=".partial-", dir=root))
    try:
        (staging / "raw").mkdir()
        for p, raw in files.items():
            _write_once(staging / p, raw)
        _write_once(staging / "manifest.json", raw_manifest)
        _write_once(staging / "manifest.sha256", (sha256(raw_manifest) + "\n").encode())
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return destination


def load_snapshot(path):
    path = Path(path)
    raw = (path / "manifest.json").read_bytes()
    expected = (path / "manifest.sha256").read_text().strip()
    if sha256(raw) != expected:
        raise ResearchError("Manifest hash mismatch: " + str(path))
    manifest = json.loads(raw)
    if manifest.get("schema") != 1 or manifest.get("kind") not in ("official", "synthetic"):
        raise ResearchError("Unsupported snapshot schema/kind")
    if path.name != manifest["kind"] + "-" + expected[:20]:
        raise ResearchError("Snapshot directory must preserve its content identifier")
    if set(manifest["sources"]) != set(SERIES):
        raise ResearchError("Snapshot source set mismatch")
    expected_files = {"methodology.json"} | {"raw/" + s + ".csv" for s in SERIES}
    expected_files |= {"raw/" + s + "-metadata.html" for s in SERIES if "metadata_file" in manifest["sources"][s]}
    if set(manifest["files"]) != expected_files:
        raise ResearchError("Unexpected snapshot paths")
    for name, digest in manifest["files"].items():
        file = path / name
        if file.is_symlink() or sha256(file.read_bytes()) != digest:
            raise ResearchError("Evidence hash mismatch: " + name)
    method = json.loads((path / "methodology.json").read_bytes())
    validate_method(method)
    if manifest["methodology_sha256"] != manifest["files"]["methodology.json"] or manifest["methodology_version"] != method["version"]:
        raise ResearchError("Methodology identity mismatch")
    data = {}
    for series, meta in manifest["sources"].items():
        name = "raw/" + series + ".csv"
        if meta["file"] != name or meta["sha256"] != manifest["files"][name]:
            raise ResearchError("Source file identity mismatch")
        validate_contract(meta["contract"])
        if meta["contract"] != method["series"][series]:
            raise ResearchError("Source/methodology contract mismatch")
        if timestamp(meta["retrieved_at"]) > timestamp(manifest["captured_at"]):
            raise ResearchError("Invalid capture chronology")
        data[series] = parse_csv((path / name).read_bytes(), series, meta["contract"], meta["retrieved_at"])
    return Snapshot(path, manifest, method, data)


def select_known_snapshot(store, known_at, kind="official"):
    cutoff = timestamp(known_at)
    snapshots = []
    for path in Path(store).glob(kind + "-*"):
        s = load_snapshot(path)
        if timestamp(s.manifest["captured_at"]) <= cutoff:
            snapshots.append(s)
    if not snapshots:
        raise ResearchError("No saved snapshot was known by that timestamp. Historical vintages are unavailable.")
    return max(snapshots, key=lambda s: (timestamp(s.manifest["captured_at"]), s.id))


class OfficialRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urllib.parse.urlparse(newurl)
        if parsed.scheme != "https" or parsed.hostname != "fred.stlouisfed.org":
            raise ResearchError("Unexpected source redirect")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def public_get(url):
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme != "https" or parsed.hostname != "fred.stlouisfed.org":
        raise ResearchError("Only the documented HTTPS FRED source is supported")
    opener = urllib.request.build_opener(OfficialRedirect(), urllib.request.HTTPSHandler(context=ssl.create_default_context()))
    request = urllib.request.Request(url, headers={"User-Agent": "OpenMacroLab/0.1 (local research; public data)", "Accept-Encoding": "identity"})
    with opener.open(request, timeout=30) as response:
        raw = response.read(8 * 1024 * 1024 + 1)
        if len(raw) > 8 * 1024 * 1024:
            raise ResearchError("Source response exceeds size limit")
        return raw, {"url": url, "final_url": response.geturl(), "retrieved_at": utcnow(),
                     "http_date": response.headers.get("Date"), "content_type": response.headers.get("Content-Type")}


def validate_source_metadata(raw, series, contract):
    source = raw.decode("utf-8")
    headings = re.findall(r"<h1\b[^>]*>(.*?)</h1>", source, re.I | re.S)
    clean = lambda s: " ".join(html.unescape(re.sub("<[^>]+>", " ", s)).split())
    title = " ".join(clean(s) for s in headings)
    text = clean(source)
    if contract["title_fragment"] not in title or series not in title:
        raise ResearchError("Source series/title changed for " + series)
    for token in ("Millions of U.S. Dollars", "Not Seasonally Adjusted", "As of Wednesday"):
        if token not in text:
            raise ResearchError("Source metadata contract not confirmed for " + series + ": " + token)
    return title


def fetch_snapshot(store, start="2024-01-01", method=None):
    date.fromisoformat(start)
    if date.fromisoformat(start) > timestamp(utcnow()).date():
        raise ResearchError("Start date is in the future")
    method, inputs, provenance = method or load_method(), {}, {}
    validate_method(method)
    for series in SERIES:
        metadata, metadata_provenance = public_get("https://fred.stlouisfed.org/series/" + series)
        title = validate_source_metadata(metadata, series, method["series"][series])
        url = "https://fred.stlouisfed.org/graph/fredgraph.csv?" + urllib.parse.urlencode({"id": series, "cosd": start})
        raw, source = public_get(url)
        records = parse_csv(raw, series, method["series"][series], source["retrieved_at"])
        if min(records) < date.fromisoformat(start):
            raise ResearchError("Source ignored requested start window")
        inputs[series] = raw
        provenance[series] = {**source, "metadata_url": metadata_provenance["url"],
                              "metadata_retrieved_at": metadata_provenance["retrieved_at"],
                              "verified_title": title, "metadata_bytes": metadata,
                              "origin": "Board of Governors of the Federal Reserve System (US), H.4.1, via FRED",
                              "license": "Public Domain: Citation Requested; see DATA_LICENSE.md"}
    return create_snapshot(store, inputs, provenance, utcnow(), "official", method, start)
