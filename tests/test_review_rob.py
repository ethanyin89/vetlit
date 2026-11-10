"""Run: VETLIT_LIVE=1 python3 tests/test_review_rob.py — 综述偏倚风险 row (certainty.json review_rob_tool / review_rob_overall)."""
import os, sys, re, glob, copy
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
PM='40470278'   # systematic review (dog AD); fixture only, live data untouched
p=B.get(PM); base={k:v for k,v in copy.deepcopy(B.CERT[PM]).items() if not k.startswith('review_rob_')}; LIVE0=copy.deepcopy(B.CERT[PM])
def with_fields(**kw):
    B.CERT[PM]=dict(base,**kw); B.CERT[PM]={k:v for k,v in B.CERT[PM].items() if v is not None}
    try: return B.grade(p), B.chip(p,'#evidence'), B.cmeta(p), B.paper(p)
    finally: B.CERT[PM]=copy.deepcopy(LIVE0)
(chip0,fold0),c0,m0,h0=with_fields()
(chip1,fold1),c1,m1,h1=with_fields(review_rob_tool='ROBIS',review_rob_overall='高')
row='<tr><th>综述偏倚风险（ROBIS）</th><td>高</td></tr>'
assert row in fold1 and fold1==fold0.replace('</table>',row+'</table>',1), fold1
assert re.search(r'<tr><th>结果</th><td>[^<]*</td></tr>'+re.escape(row),fold1)   # right after the certainty row
assert chip1==chip0 and c1==c0 and m1==m0, 'badge / card line must not change'
top1,ev1=h1.split('id="evidence"',1)
assert '综述偏倚风险' not in top1 and row in ev1 and h1.count(row)==1
for kw in ({'review_rob_tool':'AMSTAR 2'},{'review_rob_overall':'低'},{'review_rob_tool':'','review_rob_overall':'低'},{'review_rob_tool':'ROBIS','review_rob_overall':''}):
    (c,f),_,_,h=with_fields(**kw); assert f==fold0 and h==h0 and '<th>综述偏倚风险' not in h, kw
(_,f),_,_,_=with_fields(review_rob_tool='AMSTAR 2',review_rob_overall='极低'); assert '<th>综述偏倚风险（AMSTAR 2）</th><td>极低</td>' in f
assert B.review_rob_rows({})==[] and B.review_rob_rows(None)==[]
# live data (2026-11-09 sync): only entries with BOTH fields show the row, once, inside 证据与方法; all other pages never show it
HAS={k for k,r in B.CERT.items() if isinstance(r,dict) and r.get('review_rob_tool') and r.get('review_rob_overall')}
assert HAS=={'39858209','40941356','40470278'}, HAS
for f in glob.glob('dist/papers/*/index.html'):
    h=open(f,encoding='utf-8').read(); pm=f.split('/')[-2].replace('pmid-','')
    if pm in HAS:
        r=B.CERT[pm]; row=f'<tr><th>综述偏倚风险（{r["review_rob_tool"]}）</th><td>{r["review_rob_overall"]}</td></tr>'
        assert h.count('<th>综述偏倚风险')==1 and row in h.split('id="evidence"',1)[1] and '综述偏倚风险' not in h.split('id="evidence"',1)[0], f
    else: assert '综述偏倚风险' not in h, f
for f in glob.glob('dist/**/*.html',recursive=True):
    if '/papers/' not in f: assert '综述偏倚风险' not in open(f,encoding='utf-8').read(), f
print('review RoB row tests OK')
