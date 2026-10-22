"""Stage only reviewed numerical/synthetic artifacts. Never uploads or deploys."""

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from open_macro_lab.workflow import verify_report


def safe_path(value):
    rel = PurePosixPath(value)
    if not value or rel.is_absolute() or '..' in rel.parts or '\\' in value or ':' in value or rel.as_posix() != value:
        raise ValueError('Unsafe site path: ' + value)
    return rel


def stage(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    if output.exists():
        raise ValueError('Site output must be a new directory')
    plan_raw = (root/'SITE_FILES.json').read_bytes()
    plan = json.loads(plan_raw)
    inventory = json.loads((root/'PUBLIC_MANIFEST.json').read_text(encoding="utf-8"))['files']
    if inventory['SITE_FILES.json'] != {'bytes':len(plan_raw),'sha256':hashlib.sha256(plan_raw).hexdigest()}:
        raise ValueError('Unreviewed site allowlist')
    if plan.get('schema') != 1 or set(plan) != {'schema','files'}:
        raise ValueError('Unsupported site allowlist')
    for report in ('examples/official','examples/synthetic'):
        verify_report(root/report)
    if plan['files'].get('index.html') != 'examples/official/index.html' or plan['files'].get('synthetic/index.html') != 'examples/synthetic/index.html':
        raise ValueError('Main and synthetic routes must remain explicit')
    payload = {}
    for destination, source in plan['files'].items():
        safe_path(destination); safe_path(source)
        if not (source.startswith(('examples/official/','examples/synthetic/')) or source in ('LICENSE','DATA_LICENSE.md')):
            raise ValueError('Unapproved site source: ' + source)
        path = root/source
        if path.is_symlink() or not path.is_file() or root not in path.resolve().parents:
            raise ValueError('Unsafe site source: ' + source)
        raw = path.read_bytes()
        expected = inventory[source]
        if len(raw) != expected['bytes'] or hashlib.sha256(raw).hexdigest() != expected['sha256']:
            raise ValueError('Unreviewed site bytes: ' + source)
        if source.endswith('.html') and source not in ('examples/official/index.html','examples/synthetic/index.html'):
            raise ValueError('Source webpages may not be staged')
        payload[destination] = raw
    # Include every verified report file; never use a recursive copy of a capture.
    for prefix, report in (('', 'examples/official'), ('synthetic/', 'examples/synthetic')):
        for path in (root/report).rglob('*'):
            if path.is_symlink():
                raise ValueError('Symlink in report')
            if path.is_file():
                relative = path.relative_to(root/report).as_posix()
                if plan['files'].get(prefix+relative) != report+'/'+relative:
                    raise ValueError('Unlisted report file: ' + relative)
    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.site-',dir=output.parent) as temp:
        for name, raw in payload.items():
            target=Path(temp)/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
        os.rename(temp,output)
    return {'status':'staged','files':len(payload),'main':'dated official numerical baseline','synthetic_route':'synthetic/','uploaded':False}


if __name__ == '__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--output',type=Path,default=Path('build/site'))
    print(json.dumps(stage(ROOT,p.parse_args().output)))
