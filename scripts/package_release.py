"""Verify the exact reviewed payload and create a deterministic local source ZIP.

No Git operation, credential access, network request, installation, or publication.
Update the reviewed allowlist and manifest deliberately for a later release.
"""
import hashlib
import json
import zipfile
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    root = Path(__file__).resolve().parents[1]
    allowlist = (root / "PUBLIC_FILES.txt").read_text().splitlines()
    if len(allowlist) != len(set(allowlist)) or allowlist != sorted(allowlist):
        raise SystemExit("The public file list must be unique and sorted")
    manifest = json.loads((root / "PUBLIC_MANIFEST.json").read_text())
    expected = set(allowlist) - {"PUBLIC_MANIFEST.json"}
    if set(manifest["files"]) != expected:
        raise SystemExit("Manifest/file-list mismatch")
    payload = {}
    for name in allowlist:
        rel = Path(name)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts:
            raise SystemExit("Unsafe public path")
        path = root / rel
        if path.is_symlink() or not path.is_file() or not path.resolve().is_relative_to(root):
            raise SystemExit("Expected an ordinary allowlisted file: " + name)
        raw = path.read_bytes()
        if name != "PUBLIC_MANIFEST.json":
            entry = manifest["files"][name]
            if digest(raw) != entry["sha256"] or len(raw) != entry["bytes"]:
                raise SystemExit("Reviewed bytes changed: " + name)
        payload[name] = raw
    # Runtime-generated files are never added to a public bundle implicitly.
    ignored_dirs = {".git", ".venv", "venv", "__pycache__", "build", "data", "dist", "output", "node_modules"}
    unexpected = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if set(rel.parts) & ignored_dirs or any(part.endswith('.egg-info') for part in rel.parts):
            continue
        if path.is_file() and rel.as_posix() not in payload:
            unexpected.append(rel.as_posix())
    if unexpected:
        raise SystemExit("Unreviewed files present: " + ", ".join(sorted(unexpected)))
    version = manifest["package_version"]
    destination = root / "dist" / ("open-macro-lab-" + version + "-public.zip")
    destination.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(destination, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for name, raw in payload.items():
            item = zipfile.ZipInfo("open-macro-lab-" + version + "/" + name, (2026, 10, 21, 0, 0, 0))
            item.compress_type = zipfile.ZIP_DEFLATED
            item.create_system = 3
            item.external_attr = 0o100644 << 16
            archive.writestr(item, raw, compresslevel=9)
    fingerprint = digest(destination.read_bytes())
    destination.with_suffix(destination.suffix + ".sha256").write_text(fingerprint + "  " + destination.name + "\n")
    print(json.dumps({"archive": str(destination.relative_to(root)), "version": version,
                      "files": len(payload), "bytes": destination.stat().st_size, "sha256": fingerprint}))


if __name__ == "__main__":
    main()
