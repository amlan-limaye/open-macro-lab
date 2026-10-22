"""Non-visual HTML/evidence checks. This does not claim a browser rendering check."""
import json
import re
import sys
from decimal import Decimal
from html.parser import HTMLParser
from pathlib import Path


class Audit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids=[]; self.links=[]; self.resources=[]; self.buttons=[]; self.panels=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.append(a['id'])
        if tag=='a':self.links.append(a.get('href',''))
        if tag in ('script','link','img','iframe') and (a.get('src') or a.get('href')):
            self.resources.append(a.get('src') or a.get('href'))
        if 'data-range' in a:self.buttons.append(a['data-range'])
        if 'data-range-panel' in a:self.panels.append(a['data-range-panel'])


def check(path):
    folder=Path(path)
    text=(folder/'index.html').read_text(encoding="utf-8")
    p=json.loads((folder/'report.json').read_text(encoding="utf-8"))
    doc=Audit();doc.feed(text)
    assert not doc.resources,doc.resources
    assert len(doc.ids)==len(set(doc.ids)),'Duplicate IDs'
    assert doc.buttons==doc.panels==['13','52','all'],'Range control/panel mismatch'
    for link in doc.links:
        if link.startswith('#'):assert link[1:] in doc.ids,link
        elif not link.startswith('https://'):assert (folder/link).is_file(),link
    for row in p['rows']:
        if row['liquidity'] is not None and row['reserves'] is not None:
            assert Decimal(row['liquidity'])-Decimal(row['reserves'])==Decimal(row['gap'])
    assert 'Historical publication dates: unknown' in text
    assert 'No live trading' in text
    if p['kind']=='synthetic':assert 'SYNTHETIC DATA' in text
    else:assert 'First saved snapshot' in text or p['comparison']['status']=='compared'
    assert not re.search(r'\b(?:nan|infinity)\b',text,re.I)
    # Capture inline interaction code for a JavaScript syntax check without browser UI.
    inline=re.findall(r'<script>(.*?)</script>',text,re.S)
    assert len(inline)==1
    print(json.dumps({'report':str(folder),'content_checks':'passed','rows':len(p['rows']),
                      'linked_files':sum(not l.startswith(('https://','#')) for l in doc.links),
                      'external_loaded_resources':0,'visual_verification':'not performed'}))
    return inline[0]


if __name__=='__main__':
    for name in sys.argv[1:]:
        check(name)
