"""Run: VETLIT_LIVE=1 python3 tests/test_review_rob.py — 综述偏倚风险 row (certainty.json review_rob_tool / review_rob_overall)."""
import os, sys, re, glob, copy
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
PM='40470278'   # systematic review (dog AD); fixture only, live data untouched
p=B.get(PM); base=copy.deepcopy(B.CERT[PM])
def with_fields(**kw):
    B.CERT[PM]=dict(base,**kw); B.CERT[PM]={k:v for k,v in B.CERT[PM].items() if v is not None}
    try: return B.grade(p), B.chip(p,'#evidence'), B.cmeta(p), B.paper(p)
    finally: B.CERT[PM]=copy.deepcopy(base)
(chip0,fold0),c0,m0,h0=with_fields()
(chip1,fold1),c1,m1,h1=with_fields(review_rob_tool='ROBIS',review_rob_overall='高')
row='<tr><th>综述偏倚风险（ROBIS）</th><td>高</td></tr>'
assert row in fold1 and fold1==fold0.replace('</table>',row+'</table>',1), fold1
assert re.search(r'<tr><th>结果</th><td>[^<]*</td></tr>'+re.escape(row),fold1)   # right after the certainty row
assert chip1==chip0 and c1==c0 and m1==m0, 'badge / card line must not change'
top1,ev1=h1.split('id="evidence"',1)
assert '综述偏倚风险' not in top1 and row in ev1 and h1.count('综述偏倚风险')==1
for kw in ({'review_rob_tool':'AMSTAR 2'},{'review_rob_overall':'低'},{'review_rob_tool':'','review_rob_overall':'低'},{'review_rob_tool':'ROBIS','review_rob_overall':''}):
    (c,f),_,_,h=with_fields(**kw); assert f==fold0 and h==h0 and '综述偏倚风险' not in h, kw
(_,f),_,_,_=with_fields(review_rob_tool='AMSTAR 2',review_rob_overall='极低'); assert '<th>综述偏倚风险（AMSTAR 2）</th><td>极低</td>' in f
assert B.review_rob_rows({})==[] and B.review_rob_rows(None)==[]
# pages without these fields are unchanged: no live entry has them yet, and no built page shows the row
assert not any(r.get('review_rob_tool') or r.get('review_rob_overall') for r in B.CERT.values())
for f in glob.glob('dist/**/*.html',recursive=True): assert '综述偏倚风险' not in open(f,encoding='utf-8').read(), f
print('review RoB row tests OK')
