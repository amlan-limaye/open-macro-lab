"""Install a built wheel in an empty virtual environment and exercise it offline."""

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import venv
import zipfile
from email.parser import Parser


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('wheel', type=Path)
    parser.add_argument('--public-report', type=Path,
                        help='Also copy and reproduce this public numerical report outside the checkout')
    args = parser.parse_args()
    wheel = args.wheel.resolve()
    with zipfile.ZipFile(wheel) as archive:
        files = archive.namelist()
        metadata_name, = [name for name in files if name.endswith('.dist-info/METADATA')]
        metadata = Parser().parsestr(archive.read(metadata_name).decode())
        if metadata['Name'] != 'open-macro-lab' or metadata.get_all('Requires-Dist'):
            raise SystemExit('Expected the dependency-free Open Macro Lab wheel')
        for name in ('LICENSE', 'DATA_LICENSE.md'):
            if not any(path.endswith('/' + name) for path in files):
                raise SystemExit('Missing licensing notice: ' + name)
    env = dict(os.environ)
    env.pop('PYTHONPATH', None)
    env.pop('PYTHONHOME', None)
    with tempfile.TemporaryDirectory(prefix='open-macro-lab-install-') as temp:
        root = Path(temp)
        venv.EnvBuilder(with_pip=True).create(root / 'venv')
        bin_dir = root / 'venv' / ('Scripts' if os.name == 'nt' else 'bin')
        python = bin_dir / ('python.exe' if os.name == 'nt' else 'python')
        cli = bin_dir / ('open-macro-lab.exe' if os.name == 'nt' else 'open-macro-lab')
        def run(*command):
            result = subprocess.run([str(x) for x in command], cwd=root, env=env,
                                    check=True, text=True, capture_output=True)
            return result.stdout
        run(python, '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install',
            '--no-index', '--no-deps', wheel)
        assert run(cli, '--version').strip().endswith(metadata['Version'])
        run(cli, 'demo', '--output', 'report')
        checked = json.loads(run(python, '-I', '-m', 'open_macro_lab', 'verify-report', 'report'))
        assert checked['status'] == 'verified' and checked['kind'] == 'synthetic'
        public_check = None
        if args.public_report:
            # Only the public report is copied. No original capture or repository imports.
            supplied = root / 'published'
            shutil.copytree(args.public_report.resolve(), supplied)
            public_check = json.loads(run(cli, 'verify-report', supplied))
            assert public_check['evidence_scope'] == 'numerical_export'
            payload = json.loads((supplied / 'report.json').read_text(encoding="utf-8"))
            command = [cli, 'report', '--snapshot', supplied / 'evidence' / payload['snapshot_id'],
                       '--methodology', supplied / 'methodology.json', '--as-of', payload['as_of'],
                       '--output', root / 'reproduced']
            if payload['comparison']['status'] == 'compared':
                command += ['--previous', supplied / 'evidence' / payload['comparison']['previous_id']]
            run(*command)
            run(cli, 'verify-report', root / 'reproduced')
            for name in ('index.html', 'report.json', 'history.csv', 'methodology.json'):
                assert (supplied / name).read_bytes() == (root / 'reproduced' / name).read_bytes(), name
        run(python, '-m', 'pip', '--isolated', '--disable-pip-version-check', 'check')
    print(json.dumps({'status': 'passed', 'version': metadata['Version'], 'python': sys.version.split()[0],
                      'runtime_dependencies': [], 'network_used_for_install_or_demo': False,
                      'public_report_reproduced_outside_checkout': public_check is not None,
                      'checks': ['clean wheel installation', 'license notices', 'console entry point',
                                 'bundled fixtures and method', 'offline demo', 'isolated module entry point',
                                 'complete report reproduction', 'pip check']}))


if __name__ == '__main__':
    main()
