"""Small local CLI; offline demo and report commands need no dependencies."""

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .analysis import analyze
from .core import ResearchError, load_method, utcnow
from .report import write_report
from .store import SERIES, create_snapshot, fetch_snapshot, load_snapshot, select_known_snapshot
from .workflow import update, verify_report


def demo_snapshots(store):
    fixtures = Path(__file__).parent / "fixtures"
    paths = []
    for folder, captured in (("baseline", "2025-04-17T21:00:00+00:00"), ("later", "2025-04-24T21:00:00+00:00")):
        raw = {s: (fixtures / folder / (s + ".csv")).read_bytes() for s in SERIES}
        provenance = {s: {"url": "synthetic://" + folder + "/" + s,
                          "retrieved_at": captured, "origin": "Deliberately fabricated offline fixture",
                          "license": "MIT; synthetic values, not official observations"} for s in SERIES}
        paths.append(create_snapshot(store, raw, provenance, captured, start="2025-01-01"))
    return paths


def parser():
    p = argparse.ArgumentParser(description="Open Macro Lab — local, inspectable US balance-sheet research")
    p.add_argument("--version", action="version", version="%(prog)s " + __version__)
    commands = p.add_subparsers(dest="command", required=True)
    demo = commands.add_parser("demo", help="Build a clearly labeled synthetic example, fully offline")
    demo.add_argument("--output", default="build/demo")
    fetch = commands.add_parser("fetch", help="Capture four official public FRED series over verified HTTPS")
    fetch.add_argument("--store", default="data/live")
    fetch.add_argument("--start", default="2024-01-01")
    fetch.add_argument("--methodology", help="Versioned method to preserve in this new capture")
    report = commands.add_parser("report", help="Build HTML, JSON, and CSV from a verified saved snapshot")
    selection = report.add_mutually_exclusive_group(required=True)
    selection.add_argument("--snapshot")
    selection.add_argument("--store", help="Select the latest official snapshot known by --as-of")
    report.add_argument("--previous")
    report.add_argument("--as-of", help="ISO time with timezone; defaults to capture time; 'now' checks current age")
    report.add_argument("--methodology", help="Versioned effective method JSON; edits must bump the version")
    report.add_argument("--output", default="build/live")
    verify = commands.add_parser("verify", help="Check all snapshot hashes and data contracts")
    verify.add_argument("snapshot")
    issue = commands.add_parser("verify-report", help="Recompute a complete report from its attached evidence, fully offline")
    issue.add_argument("directory")
    refresh = commands.add_parser("update", help="Capture official data, compare the prior capture, and save a verified issue")
    refresh.add_argument("--store", default="data/live")
    refresh.add_argument("--output", default="build/issues", help="Parent directory for immutable per-capture reports")
    refresh.add_argument("--start", help="Inherit the last capture's start window; first capture defaults to 2024-01-01")
    refresh.add_argument("--methodology", help="Explicit versioned method; otherwise inherit the last saved method")
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    try:
        if args.command == "update":
            result = update(args.store, args.output, args.start, load_method(args.methodology) if args.methodology else None)
            print(json.dumps(result, indent=2))
        elif args.command == "verify-report":
            print(json.dumps(verify_report(args.directory), indent=2))
        elif args.command == "fetch":
            path = fetch_snapshot(args.store, args.start, load_method(args.methodology) if args.methodology else None)
            print(path)
        elif args.command == "verify":
            snapshot = load_snapshot(args.snapshot)
            print(json.dumps({"status": "verified", "id": snapshot.id, "kind": snapshot.manifest["kind"],
                              "captured_at": snapshot.manifest["captured_at"], "series": len(snapshot.data)}))
        elif args.command == "demo":
            first, last = demo_snapshots(Path(args.output) / "snapshots")
            snapshot, previous = load_snapshot(last), load_snapshot(first)
            result = write_report(analyze(snapshot, previous), snapshot, previous, args.output)
            print("SYNTHETIC demo (invented values and revisions): " + str(result))
        else:
            as_of = utcnow() if args.as_of == "now" else args.as_of
            if args.store:
                if not as_of:
                    raise ResearchError("--store requires --as-of; availability must be explicit")
                snapshot = select_known_snapshot(args.store, as_of)
            else:
                snapshot = load_snapshot(args.snapshot)
            previous = load_snapshot(args.previous) if args.previous else None
            method = load_method(args.methodology) if args.methodology else None
            payload = analyze(snapshot, previous, as_of, method)
            print(write_report(payload, snapshot, previous, args.output))
    except (ResearchError, OSError, ValueError, KeyError) as exc:
        print("Open Macro Lab: " + str(exc), file=sys.stderr)
        return 2
    return 0
