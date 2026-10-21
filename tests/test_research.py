import copy
import io
import json
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from decimal import Decimal as D
from html.parser import HTMLParser
from pathlib import Path
from unittest.mock import patch

from open_macro_lab.analysis import analyze
from open_macro_lab.cli import demo_snapshots, main
from open_macro_lab.core import (ResearchError, aligned_rows, canonical, change_window,
                                 classify_changes, evaluate, load_method, parse_csv,
                                 percent_change, revision_bridge, timestamp)
from open_macro_lab.report import chart, render, write_report
from open_macro_lab.store import (SERIES, Snapshot, create_snapshot, load_snapshot,
                                  select_known_snapshot, validate_source_metadata, fetch_snapshot)

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.method = load_method()
        self.meta = self.method["series"]["WALCL"]

    def parse(self, body, meta=None, captured="2025-04-24T21:00:00Z"):
        return parse_csv(("observation_date,WALCL\n"+body).encode(), "WALCL", meta or self.meta, captured)

    def test_hand_calculated_formula_and_units(self):
        # 7,000bn - 800bn - 500bn = 5,700bn; actual reserves 3,000bn; gap 2,700bn.
        values = dict(zip(SERIES, map(D, ("7000000","800000","500000","3000000"))))
        self.assertEqual(evaluate(values,"liquidity",self.method),D("5700"))
        self.assertEqual(evaluate(values,"reserves",self.method),D("3000"))
        self.assertEqual(evaluate(values,"gap",self.method),D("2700"))

    def test_fractional_precision(self):
        v={"WALCL":D("1000.1"),"WDTGAL":D("100.2"),"WLRRAL":D("0.3"),"WRBWFRBL":D("500")}
        self.assertEqual(evaluate(v,"liquidity",self.method),D("0.8996"))

    def test_unit_currency_frequency_basis_and_seasonal_mismatches(self):
        for key,value in (("unit","USD billions"),("currency","EUR"),("frequency","daily"),("basis","Week average"),("seasonal_adjustment","SA")):
            with self.subTest(key=key), self.assertRaises(ResearchError):
                self.parse("2025-01-01,1000\n",dict(self.meta,**{key:value}))

    def test_duplicate_dates_are_rejected_even_if_identical(self):
        with self.assertRaisesRegex(ResearchError,"Duplicate"):
            self.parse("2025-01-01,1\n2025-01-01,1\n")

    def test_non_wednesday_rejected(self):
        with self.assertRaisesRegex(ResearchError,"Wednesday"):
            self.parse("2025-01-02,1\n")

    def test_future_observation_rejected(self):
        with self.assertRaisesRegex(ResearchError,"Future"):
            self.parse("2025-04-30,1\n")

    def test_invalid_numbers_dates_and_rows(self):
        for body in ("2025-01-01,NaN\n","2025-01-01,Infinity\n","2025-01-01,-1\n","2025-01-01,1e15\n","2025-99-99,1\n","2025-01-01,garbage\n","2025-01-01,1,2\n","2025-01-01\n"):
            with self.subTest(body=body), self.assertRaises(ResearchError):
                self.parse(body)

    def test_missing_is_not_zero(self):
        rows=self.parse("2025-01-01,1\n2025-01-08,.\n2025-01-15,\n2025-01-22,0\n")
        self.assertIsNone(rows[date(2025,1,8)])
        self.assertIsNone(rows[date(2025,1,15)])
        self.assertEqual(rows[date(2025,1,22)],D(0))

    def test_empty_and_wrong_series_rejected(self):
        for raw in (b"observation_date,WALCL\n", b"observation_date,WALCL\n2025-01-01,.\n",b"observation_date,WDTGAL\n2025-01-01,1\n"):
            with self.assertRaises(ResearchError):
                parse_csv(raw,"WALCL",self.meta,"2025-01-02T00:00:00Z")

    def test_timezone_is_required(self):
        with self.assertRaises(ResearchError):
            timestamp("2025-01-02T00:00:00")

    def test_negative_derived_proxy_and_zero_denominator(self):
        self.assertEqual(evaluate({"WALCL":D(1000),"WDTGAL":D(1500),"WLRRAL":D(500)},"liquidity",self.method),D(-1))
        self.assertIsNone(percent_change(D(0),D(1)))
        self.assertEqual(percent_change(D(100),D(90)),D(-10))

    def test_missing_required_value_suppresses_only_affected_recipe(self):
        values={"WALCL":D(1000),"WDTGAL":None,"WLRRAL":D(0),"WRBWFRBL":D(300)}
        self.assertIsNone(evaluate(values,"liquidity",self.method))
        self.assertEqual(evaluate(values,"reserves",self.method),D(".3"))

    def test_metadata_contract_checks_actual_heading(self):
        good='<h1>'+self.meta['title_fragment']+' (WALCL)</h1><p>Millions of U.S. Dollars · Not Seasonally Adjusted · As of Wednesday</p>'
        validate_source_metadata(good.encode(),"WALCL",self.meta)
        with self.assertRaises(ResearchError):
            validate_source_metadata(good.replace("Wednesday Level","Week Average").encode(),"WALCL",self.meta)


class SnapshotCase(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root=Path(self.temp.name)
        self.first,self.last=demo_snapshots(self.root/'snapshots')
        self.old,self.new=load_snapshot(self.first),load_snapshot(self.last)

    def tearDown(self):
        self.temp.cleanup()


class StorageTests(SnapshotCase):
    def test_content_addressed_idempotence_and_readonly_files(self):
        self.assertEqual(demo_snapshots(self.root/'snapshots'),[self.first,self.last])
        self.assertEqual((self.last/'manifest.json').stat().st_mode & 0o222,0)

    def test_raw_tampering_is_detected(self):
        target=self.last/'raw/WALCL.csv'
        target.chmod(0o644)
        target.write_bytes(target.read_bytes().replace(b'7160000',b'7160001'))
        with self.assertRaisesRegex(ResearchError,"hash mismatch"):
            load_snapshot(self.last)

    def test_manifest_tampering_is_detected(self):
        target=self.last/'manifest.json'
        target.chmod(0o644)
        target.write_bytes(target.read_bytes()+b' ')
        with self.assertRaisesRegex(ResearchError,"Manifest hash mismatch"):
            load_snapshot(self.last)

    def test_archived_selection_never_uses_future_capture(self):
        selected=select_known_snapshot(self.root/'snapshots',"2025-04-20T00:00:00Z",kind="synthetic")
        self.assertEqual(selected.id,self.old.id)
        # The later +2bn revision must not leak into an earlier archive-known query.
        self.assertEqual(selected.data['WALCL'][date(2025,4,16)],D('7150000'))

    def test_before_first_capture_cannot_reconstruct_history(self):
        with self.assertRaisesRegex(ResearchError,"No saved snapshot"):
            select_known_snapshot(self.root/'snapshots',"2025-04-01T00:00:00Z",kind="synthetic")

    def test_future_per_source_record_cannot_be_committed(self):
        inputs={s:(self.last/'raw'/(s+'.csv')).read_bytes() for s in SERIES}
        provenance={s:{'retrieved_at':'2025-04-01T00:00:00Z'} for s in SERIES}
        with self.assertRaisesRegex(ResearchError,"Future observation"):
            create_snapshot(self.root/'bad',inputs,provenance,'2025-05-01T00:00:00Z')
        self.assertFalse((self.root/'bad').exists())

    def test_missing_series_never_committed(self):
        with self.assertRaises(ResearchError):
            create_snapshot(self.root/'bad',{}, {},'2025-05-01T00:00:00Z')
        self.assertFalse((self.root/'bad').exists())

    def test_fetch_failure_keeps_existing_snapshots_and_commits_nothing(self):
        before=sorted(p.name for p in (self.root/'snapshots').iterdir())
        with patch('open_macro_lab.store.public_get',side_effect=OSError('source unavailable')):
            with self.assertRaises(OSError):
                fetch_snapshot(self.root/'snapshots')
        self.assertEqual(sorted(p.name for p in (self.root/'snapshots').iterdir()),before)

    def test_fetch_preserves_new_methodology_in_capture(self):
        method=copy.deepcopy(self.new.method)
        method['version']='1.0.1-test'
        method['interpretation']='Synthetic method-preservation test'
        def mocked_get(url):
            if '/series/' in url:
                s=url.rsplit('/',1)[1]
                b=('<h1>'+method['series'][s]['title_fragment']+' ('+s+')</h1>Millions of U.S. Dollars Not Seasonally Adjusted As of Wednesday').encode()
            else:
                from urllib.parse import parse_qs,urlparse
                s=parse_qs(urlparse(url).query)['id'][0]
                b=(self.last/'raw'/(s+'.csv')).read_bytes()
            return b,{'url':url,'retrieved_at':'2025-04-24T21:00:00Z'}
        with patch('open_macro_lab.store.public_get',side_effect=mocked_get),patch('open_macro_lab.store.utcnow',return_value='2025-04-24T21:00:00Z'):
            result=fetch_snapshot(self.root/'mocked','2025-01-01',method)
        self.assertEqual(load_snapshot(result).method['version'],'1.0.1-test')


class AnalysisTests(SnapshotCase):
    def test_independent_fixture_endpoint_and_window_values(self):
        p=analyze(self.new,self.old)
        self.assertEqual(p['latest']['liquidity'],'5940')
        self.assertEqual(p['latest']['reserves'],'3128')
        self.assertEqual(p['latest']['gap'],'2812')
        self.assertEqual(p['windows']['4']['liquidity'],'60')
        self.assertEqual(p['windows']['4']['contributions'],{'WALCL':'40','WDTGAL':'-20','WLRRAL':'40'})

    def test_revision_bridge_has_hand_calculated_effects(self):
        p=analyze(self.new,self.old)
        self.assertEqual(p['comparison']['counts'],{'new_observation':4,'revised_prior_value':2})
        self.assertEqual(p['comparison']['bridge']['recipes']['liquidity'],
                         {'before':'5925','prior_data_effect':'2','new_observation_effect':'13','methodology_effect':'0','after':'5940','total':'15'})

    def test_earlier_historical_revision_not_lost_in_headline_bridge(self):
        p=analyze(self.new,self.old)
        events=p['comparison']['events']
        self.assertTrue(any(e['series']=='WDTGAL' and e['date']=='2025-03-12' and e['kind']=='revised_prior_value' for e in events))

    def test_asof_before_capture_fails_even_if_observation_is_old(self):
        with self.assertRaisesRegex(ResearchError,"Lookahead"):
            analyze(self.new,as_of='2025-04-23T23:00:00Z')

    def test_backwards_snapshot_comparison_fails(self):
        with self.assertRaisesRegex(ResearchError,"after"):
            analyze(self.old,self.new)

    def test_cross_kind_comparison_fails(self):
        self.old.manifest['kind']='official'
        with self.assertRaisesRegex(ResearchError,"Synthetic and official"):
            analyze(self.new,self.old)

    def test_stale_threshold_boundary(self):
        self.assertEqual(analyze(self.new,as_of='2025-05-03T21:00:00Z')['status'],'within_age_threshold')
        p=analyze(self.new,as_of='2025-05-04T21:00:00Z')
        self.assertEqual(p['status'],'stale')
        self.assertTrue(any('STALE' in w for w in p['warnings']))

    def test_no_complete_date_fails_instead_of_fake_zero(self):
        self.new.data['WDTGAL']={d:None for d in self.new.data['WDTGAL']}
        with self.assertRaisesRegex(ResearchError,"No complete"):
            analyze(self.new)

    def test_missing_endpoint_not_replaced_with_next_earlier_row(self):
        self.new.data['WALCL'][date(2025,3,26)]=None
        p=analyze(self.new)
        self.assertIsNone(p['windows']['4'])
        self.assertEqual(p['latest']['date'],'2025-04-23')

    def test_interior_gap_kept_and_calendar_horizon_preserved(self):
        for data in self.new.data.values():
            del data[date(2025,4,2)]
        p=analyze(self.new)
        self.assertIn('2025-04-02',p['missing_dates'])
        self.assertEqual(p['windows']['4']['liquidity'],'60')
        self.assertEqual(p['windows']['4']['missing_interior_weeks'],1)

    def test_incomplete_latest_uses_explicit_older_complete_date(self):
        self.new.data['WALCL'][date(2025,4,23)]=None
        p=analyze(self.new)
        self.assertEqual(p['latest']['date'],'2025-04-16')
        self.assertTrue(any('predates' in w for w in p['warnings']))

    def test_method_edits_require_new_version(self):
        method=copy.deepcopy(self.new.method)
        method['interpretation']='A documented clarification'
        with self.assertRaisesRegex(ResearchError,"new version"):
            analyze(self.new,method=method)

    def test_methodology_effect_is_separate_and_reconciles(self):
        # A deliberately synthetic coefficient experiment, not a recommended economic recipe.
        method=copy.deepcopy(self.new.method)
        method['version']='test-2.0'
        method['recipes']['liquidity']['coefficients']['WDTGAL']='-2'
        method['recipes']['gap']['coefficients']['WDTGAL']='-2'
        b=analyze(self.new,self.old,method=method)['comparison']['bridge']['recipes']['liquidity']
        self.assertEqual(b['methodology_effect'],'-880')
        self.assertEqual(b['after'],'5060')
        self.assertEqual(b['total'],'-865')

    def test_invalid_gap_methodology_rejected(self):
        method=copy.deepcopy(self.new.method)
        method['version']='test-invalid'
        method['recipes']['gap']['coefficients']['WDTGAL']='0'
        with self.assertRaisesRegex(ResearchError,'Gap'):
            analyze(self.new,method=method)

    def test_first_snapshot_is_not_zero_revision_evidence(self):
        p=analyze(self.old)
        self.assertEqual(p['comparison']['status'],'first_snapshot')
        self.assertIsNone(p['comparison']['bridge'])
        self.assertIn('not evidence',p['comparison']['message'])

    def test_coverage_change_suppresses_headline_bridge(self):
        self.new.manifest['requested_start']='2025-02-01'
        p=analyze(self.new,self.old)
        self.assertTrue(p['comparison']['coverage_changed'])
        self.assertIsNone(p['comparison']['bridge'])

    def test_unchanged_snapshots_have_no_data_revision(self):
        self.assertEqual(analyze(self.old,self.old)['comparison']['events'],[])

    def test_removed_prior_endpoint_makes_bridge_unavailable(self):
        self.new.data['WALCL'][date(2025,4,16)]=None
        self.assertIsNone(analyze(self.new,self.old)['comparison']['bridge'])


class RevisionClassificationTests(unittest.TestCase):
    def test_all_data_classifications(self):
        days=[date(2025,1,d) for d in (1,8,15,22,29)]
        a={days[0]:D(1),days[2]:None,days[3]:D(3),days[4]:D(4)}
        b={days[0]:D(2),days[1]:D(7),days[2]:D(2),days[3]:None,date(2025,2,5):D(6)}
        kinds={e['date']:e['kind'] for e in classify_changes({'S':a},{'S':b})}
        self.assertEqual(kinds,{'2025-01-01':'revised_prior_value','2025-01-08':'historical_backfill','2025-01-15':'filled_missing','2025-01-22':'became_missing','2025-01-29':'removed_observation','2025-02-05':'new_observation'})

    def test_decimal_formatting_is_not_a_revision(self):
        d=date(2025,1,1)
        self.assertEqual(classify_changes({'S':{d:D('1.0')}},{'S':{d:D('1.000')}}),[])


class Document(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[];self.links=[];self.external_resources=[];self.scripts=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag in ('script','img','link','iframe') and (a.get('src') or a.get('href')):
            self.external_resources.append(a.get('src') or a.get('href'))


class ReportAndCLITests(SnapshotCase):
    def test_self_contained_report_all_evidence_links_resolve(self):
        output=self.root/'report'
        file=write_report(analyze(self.new,self.old),self.new,self.old,output)
        doc=Document();doc.feed(file.read_text())
        self.assertEqual(len(doc.ids),len(set(doc.ids)))
        self.assertEqual(doc.external_resources,[])
        for link in doc.links:
            if link.startswith('#'):self.assertIn(link[1:],doc.ids)
            elif not link.startswith('https://'):self.assertTrue((output/link).is_file(),link)

    def test_report_contains_required_limitations_and_synthetic_labels(self):
        content=render(analyze(self.new,self.old))
        for required in ('SYNTHETIC DATA','not a market reading','Historical publication dates: unknown','No live trading','global liquidity','SHA-256','WRESBAL','Prior data','New endpoint'):
            self.assertIn(required,content)

    def test_report_is_deterministic_at_fixed_snapshot_and_asof(self):
        p=analyze(self.new,self.old)
        self.assertEqual(render(p),render(analyze(self.new,self.old)))

    def test_html_dynamic_text_is_escaped(self):
        p=analyze(self.new)
        p['interpretation']='<script>alert(1)</script>'
        content=render(p)
        self.assertNotIn('<script>alert(1)',content)
        self.assertIn('&lt;script&gt;alert(1)',content)

    def test_single_point_and_all_zero_chart_are_finite(self):
        result=chart([{'date':'2025-01-01','x':'0'}],[('x','zero','#000','')],'zero')
        self.assertIn('<circle',result)
        self.assertNotIn('nan',result.lower())
        self.assertNotIn('inf',result.lower())

    def test_line_breaks_at_missing_data(self):
        result=chart([{'date':'2025-01-01','x':'1'},{'date':'2025-01-08','x':None},{'date':'2025-01-15','x':'2'}],[('x','test','#000','')],'test')
        path=result.split('<path d="')[1].split('"')[0]
        self.assertEqual(path.count('M'),2)
        self.assertNotIn('L',path)

    def test_offline_cli_demo_never_calls_network(self):
        with patch('open_macro_lab.store.public_get',side_effect=AssertionError('Network forbidden')),redirect_stdout(io.StringIO()):
            self.assertEqual(main(['demo','--output',str(self.root/'offline')]),0)

    def test_cli_known_at_fails_closed(self):
        with redirect_stderr(io.StringIO()) as errors:
            result=main(['report','--snapshot',str(self.last),'--as-of','2025-01-01T00:00:00Z','--output',str(self.root/'bad')])
        self.assertEqual(result,2)
        self.assertIn('Lookahead',errors.getvalue())
        self.assertFalse((self.root/'bad').exists())

    def test_cli_verify(self):
        with redirect_stdout(io.StringIO()) as output:
            self.assertEqual(main(['verify',str(self.last)]),0)
        self.assertEqual(json.loads(output.getvalue())['status'],'verified')


class SavedOfficialReferenceTests(unittest.TestCase):
    def test_saved_official_snapshot_matches_independent_published_reference(self):
        path=ROOT/'data/live/official-1c1dd1e38793565f2b84'
        if not path.exists():self.skipTest('Optional official snapshot is not bundled')
        p=analyze(load_snapshot(path))
        # Published 2026-10-14 levels, independently inspected on the four FRED pages.
        # 6,755,639 - 885,823 - 326,799 = 5,543,017 million.
        self.assertEqual(p['latest']['date'],'2026-10-14')
        self.assertEqual(p['latest']['liquidity'],'5543.017')
        self.assertEqual(p['latest']['reserves'],'3030.854')
        self.assertEqual(p['latest']['gap'],'2512.163')
        self.assertEqual(p['windows']['4']['liquidity'],'111.980')
        self.assertEqual(len(p['rows']),146)


if __name__=='__main__':
    unittest.main()
