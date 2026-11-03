import os,sys; os.environ.setdefault('VETLIT_LIVE','1')
sys.path.insert(0,os.path.join(os.path.dirname(__file__),'..'))
import build_preview as B
t=B.TBY['fip']; ps=B.tpapers(t); base=B.newest3(ps); top=B.tops('fip')
x=dict(base[0],pmid='0'); x['reporting_inconsistency']={'severity':'affects_conclusion','note_zh':'原文结论与数据不一致'}
assert B.affects_conclusion(x) and '原文结论与数据不一致' in B.ri_notice(x)
assert x['sid'] not in [p['sid'] for p in B._fill([x]+base[1:])]
for sev in ('minor',None):
    y=dict(base[0],pmid='0'); y['reporting_inconsistency']={'severity':sev} if sev else {}
    assert not B.affects_conclusion(y) and B._fill([y])[0]['sid']==y['sid']
# extras path
_saved=dict(B._RI_FILE); pm=str(top[0]['pmid']); B._RI_FILE[pm]={'severity':'affects_conclusion'}
assert B.affects_conclusion(B.get(pm)) and top[0]['sid'] not in [p['sid'] for p in B.tops('fip')]
B._RI_FILE.clear(); B._RI_FILE.update(_saved)
print('reporting_inconsistency tests OK')
# adjudicated file (real data)
import json
R=json.load(open(os.path.join(os.path.dirname(__file__),'..','data/v5/extras/reporting_inconsistency.json'),encoding='utf-8'))
assert sorted(k for k,v in R.items() if v['severity']=='affects_conclusion')==['36297266','39858209','40732763']
assert '26474314' not in R and all(v['status']=='adjudicated' for v in R.values())
for tid,t in B.TBY.items():
    for p in B.tops(tid)+B.newest3(B.tpapers(t)): assert not B.affects_conclusion(p), (tid,p['pmid'])
for k in ('41781382','38952053'):
    p=B.get(k)
    if p: assert R[k]['note_zh'] in B.ri_notice(p) and not B.affects_conclusion(p)
print('adjudicated data OK')
