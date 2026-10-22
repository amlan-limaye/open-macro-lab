"""Public-export tests use invented fixtures, not new official observations."""

import io
import importlib.util
import json
import shutil
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from open_macro_lab.analysis import analyze
from open_macro_lab.cli import demo_snapshots, main
from open_macro_lab.core import ResearchError, canonical, sha256
from open_macro_lab.publication import export_public_report, export_snapshot, load_public_snapshot
from open_macro_lab.report import write_report
from open_macro_lab.store import SERIES, create_snapshot, load_snapshot
from open_macro_lab.workflow import verify_report


class PublicationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name)
        first,last=demo_snapshots(self.root/'synthetic')
        self.synthetic=load_snapshot(last)
        self.captures=[]
        for fixture in (load_snapshot(first),self.synthetic):
            captured=fixture.manifest['captured_at']
            sources={s:{'url':'https://fred.stlouisfed.org/graph/fredgraph.csv?id='+s+'&cosd=2025-01-01',
                        'retrieved_at':captured,'metadata_bytes':b'<html>PRIVATE_SOURCE_MARKER</html>',
                        'private_note':'PRIVATE_NOTE_MARKER'} for s in SERIES}
            raw={s:(fixture.path/'raw'/(s+'.csv')).read_bytes() for s in SERIES}
            self.captures.append(load_snapshot(create_snapshot(self.root/'private',raw,sources,captured,
                                                               kind='official',start='2025-01-01')))
        self.old,self.new=self.captures
        self.exported_at='2025-04-25T12:00:00+00:00'

    def tearDown(self):
        self.temp.cleanup()

    def public_report(self, previous=None):
        with patch('open_macro_lab.publication.utcnow',return_value=self.exported_at):
            export_public_report(self.new.path,self.root/'public',previous.path if previous else None)
        return self.root/'public'

    def evidence(self, report):
        payload=json.loads((report/'report.json').read_text(encoding="utf-8"))
        return load_public_snapshot(report/'evidence'/payload['snapshot_id'])

    def rewrite_manifest(self, snapshot, edit):
        m=json.loads((snapshot.path/'manifest.json').read_text(encoding="utf-8"));edit(m)
        raw=canonical(m)
        for name,data in (('manifest.json',raw),('manifest.sha256',(sha256(raw)+'\n').encode())):
            p=snapshot.path/name;p.chmod(0o644);p.write_bytes(data)
        target=snapshot.path.with_name('public-'+sha256(raw)[:20]);snapshot.path.rename(target)
        return target

    def test_export_is_allowlisted_and_preserves_actual_capture_and_input_bytes(self):
        before={p.relative_to(self.new.path).as_posix():p.read_bytes() for p in self.new.path.rglob('*') if p.is_file()}
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        self.assertEqual(public.manifest['captured_at'],self.new.manifest['captured_at'])
        self.assertEqual(public.manifest['exported_at'],self.exported_at)
        self.assertEqual(public.manifest['original_snapshot_id'],self.new.id)
        self.assertEqual(public.manifest['original_manifest_sha256'],sha256((self.new.path/'manifest.json').read_bytes()))
        self.assertEqual(len([p for p in public.path.rglob('*') if p.is_file()]),7)
        for s in SERIES:
            self.assertEqual((public.path/'raw'/(s+'.csv')).read_bytes(),before['raw/'+s+'.csv'])
            self.assertEqual(public.manifest['sources'][s]['retrieved_at'],self.new.manifest['sources'][s]['retrieved_at'])
        for p in public.path.rglob('*'):
            if p.is_file():
                self.assertNotIn(b'PRIVATE_SOURCE_MARKER',p.read_bytes())
                self.assertNotIn(b'PRIVATE_NOTE_MARKER',p.read_bytes())
                self.assertNotEqual(p.suffix,'.html')
        self.assertEqual(before,{p.relative_to(self.new.path).as_posix():p.read_bytes() for p in self.new.path.rglob('*') if p.is_file()})

    def test_first_export_is_dated_baseline_with_explicit_verification_scope(self):
        root=self.public_report();result=verify_report(root)
        self.assertEqual(result['evidence_scope'],'numerical_export')
        self.assertIn('cannot be repeated',result['scope'])
        self.assertEqual(result['comparison'],'first_snapshot')
        content=(root/'index.html').read_text(encoding="utf-8")
        for text in ('Dated official baseline','Not a live feed.','2025-04-23','2025-04-24T21:00:00+00:00',self.exported_at,
                     'Calculation trace','trace inputs in USD millions','7,160,000.000','5,940.000','open-macro-lab verify-report .'):
            self.assertIn(text,content)

    def test_published_bundle_alone_reproduces_after_private_capture_is_removed(self):
        root=self.public_report();public=self.evidence(root)
        for path in (self.root/'private').rglob('*'):
            if path.is_file():path.chmod(0o644)
        shutil.rmtree(self.root/'private')
        with patch('open_macro_lab.publication.load_snapshot',side_effect=AssertionError('Private capture unavailable')), \
             patch('open_macro_lab.store.public_get',side_effect=AssertionError('Network unavailable')),redirect_stdout(io.StringIO()):
            self.assertEqual(main(['report','--snapshot',str(public.path),'--output',str(self.root/'reproduced')]),0)
            self.assertEqual(main(['verify-report',str(root)]),0)
        for name in ('report.json','history.csv','methodology.json','index.html'):
            self.assertEqual((root/name).read_bytes(),(self.root/'reproduced'/name).read_bytes())

    def test_private_verifier_does_not_accept_a_silently_stripped_capture(self):
        root=self.root/'private-report';write_report(analyze(self.new),self.new,None,root)
        for path in (root/'evidence'/self.new.id/'raw').glob('*-metadata.html'):
            path.chmod(0o644);path.unlink()
        with self.assertRaises(OSError):verify_report(root)

    def test_cannot_claim_full_capture_scope_for_a_numerical_export(self):
        root=self.public_report();p=root/'report.json';payload=json.loads(p.read_text(encoding="utf-8"))
        del payload['evidence_scope'];p.write_text(json.dumps(payload))
        with self.assertRaisesRegex(ResearchError,'payload does not reproduce'):verify_report(root)

    def test_public_csv_tampering_is_detected(self):
        root=self.public_report();public=self.evidence(root)
        raw=public.path/'raw/WALCL.csv';raw.chmod(0o644);raw.write_bytes(b'edited')
        with self.assertRaisesRegex(ResearchError,'hash mismatch'):verify_report(root)

    def test_public_source_page_files_are_rejected_even_if_unreferenced(self):
        root=self.public_report();public=self.evidence(root)
        (public.path/'raw/source.html').write_text('PRIVATE_SOURCE_MARKER')
        with self.assertRaisesRegex(ResearchError,'Unlisted'):verify_report(root)

    def test_public_statistics_are_checked_against_numerical_inputs(self):
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        path=self.rewrite_manifest(public,lambda m:m['sources']['WALCL'].update(observations=999))
        with self.assertRaisesRegex(ResearchError,'statistics mismatch'):load_public_snapshot(path)

    def test_historical_publication_dates_cannot_be_invented(self):
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        path=self.rewrite_manifest(public,lambda m:m['sources']['WALCL'].update(publication_dates='2025-04-23'))
        with self.assertRaisesRegex(ResearchError,'explicitly unknown'):load_public_snapshot(path)

    def test_original_capture_reference_is_not_relabelled(self):
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        path=self.rewrite_manifest(public,lambda m:m.update(original_snapshot_id='official-'+'0'*20))
        with self.assertRaisesRegex(ResearchError,'capture reference'):load_public_snapshot(path)

    def test_export_cannot_be_backdated_before_capture(self):
        with self.assertRaisesRegex(ResearchError,'precede'):
            export_snapshot(self.new,self.root/'export','2025-04-01T00:00:00Z')
        self.assertFalse((self.root/'export').exists())

    def test_synthetic_values_cannot_be_exported_as_official(self):
        with self.assertRaisesRegex(ResearchError,'original official'):
            export_public_report(self.synthetic.path,self.root/'public')
        self.assertFalse((self.root/'public').exists())

    def test_existing_output_is_not_overwritten(self):
        self.public_report();before=(self.root/'public/index.html').read_bytes()
        with self.assertRaisesRegex(ResearchError,'new output'):
            export_public_report(self.new.path,self.root/'public')
        self.assertEqual((self.root/'public/index.html').read_bytes(),before)

    def test_future_comparison_path_uses_only_saved_fixture_captures(self):
        root=self.public_report(self.old);p=json.loads((root/'report.json').read_text(encoding="utf-8"))
        self.assertEqual(p['comparison']['counts'],{'new_observation':4,'revised_prior_value':2})
        self.assertEqual(p['comparison']['bridge']['recipes']['liquidity']['total'],'15')
        self.assertEqual(len(p['evidence_scope']['exports']),2)
        self.assertEqual(verify_report(root)['evidence_scope'],'numerical_export')

    def test_public_and_private_evidence_cannot_be_mixed_in_a_public_report(self):
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        with self.assertRaisesRegex(ResearchError,'both captures'):analyze(public,self.old)

    def test_original_capture_asof_guard_is_preserved(self):
        public=export_snapshot(self.new,self.root/'export',self.exported_at)
        with self.assertRaisesRegex(ResearchError,'Lookahead'):analyze(public,as_of='2025-04-23T00:00:00Z')

    def script(self, name):
        path=Path(__file__).resolve().parents[1]/'scripts'/(name+'.py')
        spec=importlib.util.spec_from_file_location(name,path)
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        return module

    def site(self):
        root=self.root/'site-source'
        shutil.copytree(self.public_report(),root/'examples/official')
        write_report(analyze(self.synthetic),self.synthetic,None,root/'examples/synthetic')
        (root/'LICENSE').write_text('Fixture project license')
        (root/'DATA_LICENSE.md').write_text('Fixture data attribution')
        files={'LICENSE':'LICENSE','DATA_LICENSE.md':'DATA_LICENSE.md'}
        for prefix,report in (('', 'examples/official'),('synthetic/','examples/synthetic')):
            for file in (root/report).rglob('*'):
                if file.is_file():files[prefix+file.relative_to(root/report).as_posix()]=file.relative_to(root).as_posix()
        self.site_plan(root,{'schema':1,'files':files})
        return root

    def site_plan(self, root, plan):
        (root/'SITE_FILES.json').write_bytes(canonical(plan))
        files={p.relative_to(root).as_posix():{'bytes':len(p.read_bytes()),'sha256':sha256(p.read_bytes())}
               for p in root.rglob('*') if p.is_file() and p.name!='PUBLIC_MANIFEST.json'}
        (root/'PUBLIC_MANIFEST.json').write_bytes(canonical({'files':files}))

    def test_independent_checker_uses_published_values_and_detects_changed_results(self):
        root=self.public_report();checker=self.script('check_public_example')
        with redirect_stdout(io.StringIO()):result=checker.check(root)
        self.assertEqual(result['rows'],17)
        p=root/'report.json';payload=json.loads(p.read_text(encoding="utf-8"));payload['rows'][0]['liquidity']='1'
        p.write_text(json.dumps(payload))
        with self.assertRaises(AssertionError):checker.check(root)

    def test_site_contains_only_approved_real_synthetic_and_license_files(self):
        root=self.site();(root/'private-note.txt').write_text('PRIVATE_NOTE_MARKER')
        output=self.root/'staged';result=self.script('stage_site').stage(root,output)
        self.assertEqual(result['uploaded'],False)
        self.assertEqual((output/'index.html').read_bytes(),(root/'examples/official/index.html').read_bytes())
        self.assertEqual((output/'synthetic/index.html').read_bytes(),(root/'examples/synthetic/index.html').read_bytes())
        self.assertFalse((output/'private-note.txt').exists())
        self.assertFalse(any('metadata.html' in p.name for p in output.rglob('*')))
        self.assertEqual(verify_report(output)['evidence_scope'],'numerical_export')

    def test_staging_rejects_unlisted_source_html(self):
        root=self.site();(root/'examples/official/accidental-source.html').write_text('PRIVATE_SOURCE_MARKER')
        with self.assertRaisesRegex(ValueError,'Unlisted report file'):
            self.script('stage_site').stage(root,self.root/'staged')
        self.assertFalse((self.root/'staged').exists())

    def test_staging_rejects_path_traversal_and_unapproved_sources(self):
        root=self.site();original=json.loads((root/'SITE_FILES.json').read_text(encoding="utf-8"))
        for destination,source,message in (('../escape','LICENSE','Unsafe site path'),('private.txt','private.txt','Unapproved site source')):
            with self.subTest(destination=destination):
                plan=json.loads(json.dumps(original));plan['files'][destination]=source
                (root/'private.txt').write_text('PRIVATE_NOTE_MARKER');self.site_plan(root,plan)
                with self.assertRaisesRegex(ValueError,message):self.script('stage_site').stage(root,self.root/'staged')
                self.assertFalse((self.root/'staged').exists())

    def test_staging_rejects_altered_allowlist_or_license_bytes(self):
        root=self.site();plan=root/'SITE_FILES.json';original=plan.read_bytes()
        plan.write_bytes(original+b' ')
        with self.assertRaisesRegex(ValueError,'Unreviewed site allowlist'):
            self.script('stage_site').stage(root,self.root/'staged')
        plan.write_bytes(original);(root/'DATA_LICENSE.md').write_text('altered notice')
        with self.assertRaisesRegex(ValueError,'Unreviewed site bytes'):
            self.script('stage_site').stage(root,self.root/'staged')


if __name__=='__main__':unittest.main()
