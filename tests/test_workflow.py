"""Workflow simulations use fabricated fixtures, never claimed official revisions."""

import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest.mock import patch

from open_macro_lab.analysis import analyze
from open_macro_lab.cli import demo_snapshots, main
from open_macro_lab.core import ResearchError, load_method
from open_macro_lab.report import write_report
from open_macro_lab.store import SERIES, create_snapshot, load_snapshot
from open_macro_lab.workflow import update, verify_report


class WorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        first, last = demo_snapshots(self.root / 'synthetic')
        self.old, self.new = load_snapshot(first), load_snapshot(last)
        self.store, self.output = self.root / 'archive', self.root / 'issues'

    def tearDown(self):
        self.temp.cleanup()

    def official_simulation(self, fixture, captured, store=None, method=None, start='2025-01-01'):
        """Only temporary test data exercises the official acquisition code path."""
        inputs = {s: (fixture.path / 'raw' / (s + '.csv')).read_bytes() for s in SERIES}
        provenance = {s: {'retrieved_at': captured, 'origin': 'Fabricated test simulation'} for s in SERIES}
        return create_snapshot(store or self.store, inputs, provenance, captured,
                               kind='official', method=method, start=start)

    def run_update(self, fixture=None, captured='2025-04-24T21:00:00Z', **kwargs):
        fixture = fixture or self.new
        def acquire(store, start, method):
            return self.official_simulation(fixture, captured, store, method, start)
        with patch('open_macro_lab.workflow.utcnow', return_value=captured), \
             patch('open_macro_lab.workflow.fetch_snapshot', side_effect=acquire) as fetch:
            result = update(self.store, self.output, **kwargs)
        return result, fetch

    def report(self):
        folder = self.root / 'report'
        write_report(analyze(self.new, self.old), self.new, self.old, folder)
        return folder

    def test_first_update_is_baseline_and_is_fully_verifiable(self):
        result, _ = self.run_update(start='2025-01-01')
        self.assertEqual(result['comparison'], 'first_snapshot')
        self.assertEqual(result['change_counts'], {})
        self.assertIsNone(result['previous'])
        self.assertIn('not evidence', result['comparison_note'])
        checked = verify_report(Path(result['report']).parent)
        self.assertEqual(checked['status'], 'verified')

    def test_later_update_inherits_window_and_compares_prior_capture(self):
        first, _ = self.run_update(self.old, '2025-04-17T21:00:00Z', start='2025-01-01')
        before = Path(first['report']).read_bytes()
        result, fetch = self.run_update()
        self.assertEqual(fetch.call_args.args[1], '2025-01-01')
        self.assertEqual(result['previous'], first['snapshot'])
        self.assertEqual(result['change_counts'], {'new_observation': 4, 'revised_prior_value': 2})
        p = json.loads(Path(result['report']).with_name('report.json').read_text(encoding="utf-8"))
        self.assertEqual(p['comparison']['bridge']['recipes']['liquidity']['after'], '5940')
        self.assertEqual(p['comparison']['bridge']['recipes']['liquidity']['prior_data_effect'], '2')
        self.assertEqual(Path(first['report']).read_bytes(), before)

    def test_same_capture_retry_reuses_issue_without_self_comparison(self):
        first, _ = self.run_update(start='2025-01-01')
        again, _ = self.run_update()
        self.assertEqual(again['status'], 'reused')
        self.assertEqual(again['report'], first['report'])
        self.assertEqual(again['comparison'], 'first_snapshot')

    def test_future_archive_and_synthetic_snapshots_are_not_previous(self):
        self.official_simulation(self.new, '2025-05-01T21:00:00Z')
        demo_snapshots(self.store)
        result, _ = self.run_update()
        self.assertIsNone(result['previous'])
        self.assertEqual(result['comparison'], 'first_snapshot')

    def test_method_inherits_and_unversioned_change_fails_before_fetch(self):
        method = load_method(); method['version'] = 'test-explicit-version'
        self.official_simulation(self.old, '2025-04-17T21:00:00Z', method=method)
        _, fetch = self.run_update()
        self.assertEqual(fetch.call_args.args[2], method)
        method = copy.deepcopy(method); method['interpretation'] = 'Changed explanation'
        with patch('open_macro_lab.workflow.fetch_snapshot') as fetch, self.assertRaisesRegex(ResearchError, 'new version'):
            update(self.store, self.output, method=method)
        fetch.assert_not_called()

    def test_fetch_failure_preserves_old_issue(self):
        first, _ = self.run_update(self.old, '2025-04-17T21:00:00Z')
        before = Path(first['report']).read_bytes()
        entries = sorted(p.name for p in self.store.iterdir())
        with patch('open_macro_lab.workflow.fetch_snapshot', side_effect=OSError('source unavailable')):
            with self.assertRaises(OSError): update(self.store, self.output)
        self.assertEqual(Path(first['report']).read_bytes(), before)
        self.assertEqual(sorted(p.name for p in self.store.iterdir()), entries)

    def test_failed_report_keeps_capture_without_partial_issue(self):
        with patch('open_macro_lab.workflow.write_report', side_effect=OSError('disk full')):
            with self.assertRaisesRegex(ResearchError, 'saved snapshot remains'):
                self.run_update()
        self.assertEqual(len(list(self.store.glob('official-*'))), 1)
        self.assertEqual(list(self.output.iterdir()), [])

    def test_corrupt_archive_fails_before_network(self):
        saved = self.official_simulation(self.old, '2025-04-17T21:00:00Z')
        raw = saved / 'raw/WALCL.csv'; raw.chmod(0o644); raw.write_bytes(b'bad')
        with patch('open_macro_lab.workflow.fetch_snapshot') as fetch, self.assertRaisesRegex(ResearchError, 'hash mismatch'):
            update(self.store, self.output)
        fetch.assert_not_called()

    def test_output_cannot_modify_snapshot(self):
        self.output = self.store
        with self.assertRaisesRegex(ResearchError, 'outside'):
            self.run_update()
        self.assertFalse(any(self.store.glob('official-*/index.html')))

    def test_output_inside_an_older_snapshot_fails_before_acquisition(self):
        prior = self.official_simulation(self.old, '2025-04-17T21:00:00Z')
        with patch('open_macro_lab.workflow.fetch_snapshot') as fetch, self.assertRaisesRegex(ResearchError, 'outside'):
            update(self.store, prior / 'reports')
        fetch.assert_not_called()

    def test_incomplete_new_capture_error_identifies_retained_evidence(self):
        inputs = {series: ('observation_date,' + series + '\n2025-01-%02d,1000\n' % (1 + 7 * i)).encode()
                  for i, series in enumerate(SERIES)}
        provenance = {s: {'retrieved_at': '2025-01-30T00:00:00Z'} for s in SERIES}
        captured = create_snapshot(self.root / 'acquired', inputs, provenance, '2025-01-30T00:00:00Z',
                                   kind='official', start='2025-01-01')
        with patch('open_macro_lab.workflow.fetch_snapshot', return_value=captured):
            with self.assertRaisesRegex(ResearchError, 'saved snapshot remains') as error:
                update(self.store, self.output)
        self.assertIn(str(captured), str(error.exception))
        self.assertTrue(captured.exists())
        self.assertFalse(self.output.exists())

    def test_unchanged_values_have_an_explicit_unchanged_explanation(self):
        self.run_update(self.old, '2025-04-17T21:00:00Z')
        result, _ = self.run_update(self.old, '2025-04-24T21:00:00Z')
        self.assertEqual(result['change_counts'], {})
        self.assertIn('No parsed observation values changed', result['comparison_note'])
        self.assertNotIn('Differences observed', result['comparison_note'])

    def test_new_complete_capture_can_recover_from_incomplete_prior_capture(self):
        inputs = {series: ('observation_date,' + series + '\n2025-01-%02d,1000\n' % (1 + 7 * i)).encode()
                  for i, series in enumerate(SERIES)}
        provenance = {s: {'retrieved_at': '2025-01-30T00:00:00Z'} for s in SERIES}
        create_snapshot(self.store, inputs, provenance, '2025-01-30T00:00:00Z',
                        kind='official', start='2025-01-01')
        result, _ = self.run_update()
        self.assertEqual(result['observation_date'], '2025-04-23')
        payload = json.loads(Path(result['report']).with_name('report.json').read_text(encoding="utf-8"))
        self.assertIsNone(payload['comparison']['bridge'])

    def test_issue_serialization_has_explicit_portable_line_endings(self):
        folder = self.report()
        history = (folder / 'history.csv').read_bytes()
        self.assertIn(b'\r\n', history)
        self.assertNotIn(b'\r\r\n', history)
        self.assertNotIn(b'\n', history.replace(b'\r\n', b''))
        self.assertNotIn(b'\r', (folder / 'index.html').read_bytes())

    def test_report_verification_is_offline_and_does_not_modify_issue(self):
        folder = self.report()
        before = {str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob('*') if p.is_file()}
        with patch('open_macro_lab.store.public_get', side_effect=AssertionError('Network forbidden')):
            result = verify_report(folder)
        self.assertEqual(result['status'], 'verified')
        self.assertEqual(result['kind'], 'synthetic')
        self.assertEqual(before, {str(p.relative_to(folder)): p.read_bytes() for p in folder.rglob('*') if p.is_file()})

    def test_report_payload_tampering_is_detected(self):
        folder = self.report(); file = folder / 'report.json'
        payload = json.loads(file.read_text(encoding="utf-8")); payload['latest']['liquidity'] = '99999'
        file.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ResearchError, 'payload does not reproduce'):
            verify_report(folder)

    def test_csv_and_html_tampering_are_detected(self):
        folder = self.report()
        for name in ('history.csv', 'index.html'):
            with self.subTest(file=name):
                file = folder / name; original = file.read_bytes()
                file.write_bytes(original + b'edited')
                with self.assertRaisesRegex(ResearchError, name.replace('.', r'\.')):
                    verify_report(folder)
                file.write_bytes(original)

    def test_attached_raw_input_tampering_is_detected(self):
        folder = self.report(); raw = folder / 'evidence' / self.new.id / 'raw/WALCL.csv'
        raw.chmod(0o644); raw.write_bytes(b'edited')
        with self.assertRaisesRegex(ResearchError, 'hash mismatch'):
            verify_report(folder)

    def test_engine_mismatch_explains_how_to_reproduce_old_report(self):
        folder = self.report(); file = folder / 'report.json'
        payload = json.loads(file.read_text(encoding="utf-8")); payload['engine_sha256'] = '0' * 64
        file.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ResearchError, 'original package version'):
            verify_report(folder)

    def test_report_identifiers_cannot_escape_evidence_directory(self):
        folder = self.report(); file = folder / 'report.json'
        payload = json.loads(file.read_text(encoding="utf-8")); payload['snapshot_id'] = '../../outside'
        file.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ResearchError, 'Invalid report snapshot'):
            verify_report(folder)

    def test_cli_verifies_report_and_returns_actionable_failure(self):
        folder = self.report()
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['verify-report', str(folder)]), 0)
        self.assertEqual(json.loads(output.getvalue())['status'], 'verified')
        (folder / 'history.csv').write_text('changed')
        with redirect_stderr(io.StringIO()) as error:
            self.assertEqual(main(['verify-report', str(folder)]), 2)
        self.assertIn('history.csv', error.getvalue())

    def test_cli_update_runs_acquisition_validation_comparison_and_verification(self):
        from urllib.parse import parse_qs, urlparse
        def acquire(url):
            if '/series/' in url:
                series = url.rsplit('/', 1)[1]
                content = ('<h1>' + self.new.method['series'][series]['title_fragment'] + ' (' + series
                           + ')</h1>Millions of U.S. Dollars Not Seasonally Adjusted As of Wednesday').encode()
            else:
                series = parse_qs(urlparse(url).query)['id'][0]
                content = (self.new.path / 'raw' / (series + '.csv')).read_bytes()
            return content, {'url': url, 'retrieved_at': '2025-04-24T21:00:00Z'}
        self.official_simulation(self.old, '2025-04-17T21:00:00Z')
        with patch('open_macro_lab.store.public_get', side_effect=acquire) as network, \
             patch('open_macro_lab.store.utcnow', return_value='2025-04-24T21:00:00Z'), \
             patch('open_macro_lab.workflow.utcnow', return_value='2025-04-24T21:00:00Z'), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['update', '--store', str(self.store), '--output', str(self.output)]), 0)
        result = json.loads(output.getvalue())
        self.assertEqual(network.call_count, 8)
        self.assertEqual(result['change_counts'], {'new_observation': 4, 'revised_prior_value': 2})
        self.assertEqual(verify_report(Path(result['report']).parent)['status'], 'verified')


if __name__ == '__main__':
    unittest.main()
