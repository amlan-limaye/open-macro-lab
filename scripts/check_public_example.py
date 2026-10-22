"""Independent numerical check: standard library only; never imports the research engine."""

import csv
import hashlib
import json
from datetime import date, timedelta
from decimal import Decimal as D
from pathlib import Path
import sys

SERIES = ('WALCL', 'WDTGAL', 'WLRRAL', 'WRBWFRBL')


def check(directory):
    root = Path(directory)
    payload = json.loads((root / 'report.json').read_text(encoding="utf-8"))
    assert payload['kind'] == 'official' and payload['evidence_scope']['type'] == 'numerical_export'
    evidence = root / 'evidence' / payload['snapshot_id']
    manifest_raw = (evidence / 'manifest.json').read_bytes()
    fingerprint = hashlib.sha256(manifest_raw).hexdigest()
    assert (evidence / 'manifest.sha256').read_text(encoding="utf-8").strip() == fingerprint
    assert evidence.name == 'public-' + fingerprint[:20]
    manifest = json.loads(manifest_raw)
    method = json.loads((root / 'methodology.json').read_text(encoding="utf-8"))
    coefficients = {
        'liquidity': {'WALCL': '1', 'WDTGAL': '-1', 'WLRRAL': '-1'},
        'reserves': {'WRBWFRBL': '1'},
        'gap': {'WALCL': '1', 'WDTGAL': '-1', 'WLRRAL': '-1', 'WRBWFRBL': '-1'},
    }
    assert method['version'] == '1.0.0' and method['output_unit'] == 'USD billions'
    assert {k: v['coefficients'] for k, v in method['recipes'].items()} == coefficients
    inputs = {}
    for series in SERIES:
        source = manifest['sources'][series]
        raw = (evidence / source['file']).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == source['sha256']
        rows = list(csv.DictReader(raw.decode('utf-8-sig').splitlines()))
        date_key = 'observation_date' if 'observation_date' in rows[0] else 'DATE'
        assert len({row[date_key] for row in rows}) == len(rows)
        inputs[series] = {row[date_key]: None if row[series] in ('', '.') else D(row[series]) for row in rows}
        assert all(date.fromisoformat(day).weekday() == 2 for day in inputs[series])
        assert all(value is None or value.is_finite() for value in inputs[series].values())
    all_dates = sorted({day for data in inputs.values() for day in data})
    start, end = date.fromisoformat(all_dates[0]), date.fromisoformat(all_dates[-1])
    expected_dates = [(start + timedelta(weeks=n)).isoformat() for n in range((end-start).days//7 + 1)]
    assert [row['date'] for row in payload['rows']] == expected_dates
    calculated = {}
    history = list(csv.DictReader((root / 'history.csv').read_text(encoding="utf-8").splitlines()))
    assert [row['observation_date'] for row in history] == expected_dates
    for row, exported in zip(payload['rows'], history):
        day = row['date']
        a, t, rr, r = [inputs[s].get(day) for s in SERIES]
        # Explicit independent method-1.0.0 reference, not the engine evaluator.
        liquidity = (a-t-rr)/D(1000) if None not in (a,t,rr) else None
        reserves = r/D(1000) if r is not None else None
        gap = liquidity-reserves if liquidity is not None and reserves is not None else None
        expected = {'liquidity':liquidity, 'reserves':reserves, 'gap':gap}
        calculated[day] = expected
        for key, value in expected.items():
            assert (D(row[key]) if row[key] is not None else None) == value, (day,key)
            assert (D(exported[key+'_usd_bn']) if exported[key+'_usd_bn'] else None) == value, (day,key,'CSV')
        for s, value in zip(SERIES,(a,t,rr,r)):
            assert (D(row['inputs'][s]) if row['inputs'][s] is not None else None) == value
    complete = [day for day in expected_dates if None not in calculated[day].values()]
    assert payload['latest']['date'] == complete[-1]
    for n, window in payload['windows'].items():
        if window is None:
            continue
        assert (date.fromisoformat(window['end'])-date.fromisoformat(window['start'])).days == int(n)*7
        for key in ('liquidity','reserves','gap'):
            assert D(window[key]) == calculated[window['end']][key]-calculated[window['start']][key]
    result = {'status':'passed','scope':'Independent method-1.0.0 arithmetic from published numerical CSVs only',
              'rows':len(expected_dates),'input_cells':sum(len(v) for v in inputs.values()),
              'observation_date':payload['latest']['date'],'captured_at':payload['captured_at'],
              'comparison':payload['comparison']['status'],'metadata_webpages_checked':False}
    print(json.dumps(result))
    return result


if __name__ == '__main__':
    check(sys.argv[1] if len(sys.argv)>1 else 'examples/official')
