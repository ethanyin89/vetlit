"""Run: python3 tests/test_superseded.py — papers with superseded_by never appear in 最重要/最新 top-3 lists."""
import os, re, sys, glob
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
# 1) unit: synthetic superseded paper is skipped and the next fills the slot
ps=sorted(B.P.values(),key=lambda p:p.get('pub_date') or '',reverse=True)[:5]
ps=[p for p in ps if not B.has_contra(p)]
saved=dict(B.SUPER); B.SUPER[str(ps[0].get('pmid'))]={'by':'999','scope':'full'}
try:
    got=[p['sid'] for p in B.newest3(ps)]
    assert ps[0]['sid'] not in got and got==[p['sid'] for p in ps[1:4]], got
finally:
    B.SUPER.clear(); B.SUPER.update(saved)
# 1b) partial (scoped) supersession does not exclude, and link text names the scope
B.SUPER[str(ps[0].get('pmid'))]={'by':'999','scope':'treatment_only'}
try:
    assert ps[0]['sid'] in [p['sid'] for p in B.newest3(ps)]
    assert '治疗部分已有更新版' in B.superlink(ps[0],'')
finally:
    B.SUPER.clear(); B.SUPER.update(saved)
# 1c) contradiction-flagged papers never in 最新
for t in B.TP:
    for p in B.newest3(B.tpapers(t)): assert not B.has_contra(p), (t['id'],p['sid'])
# 2) real data: no superseded paper in any topic's lists, and each list is full when enough papers exist
for g in B.X.TOP.get('topics') or []:
    tid=g['topic']; t=B.TBY.get(tid)
    imp=B.tops(tid); new=B.newest3(B.tpapers(t)) if t else []
    for p in imp+new: assert not B.is_super(p), (tid,p['sid'])
    if t: assert len(new)==min(3,len([p for p in B.tpapers(t) if not B.is_super(p) and not B.has_contra(p)])), tid
# 3) built HTML: superseded sids do not appear inside 最重要/最新 blocks
sup={'pmid-'+k for k,v in B.SUPER.items() if B.is_full(v)}
for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'):
    if not os.path.exists(f): continue
    h=open(f,encoding='utf-8').read()
    for blk in re.findall(r'<h4 class="tb">(?:最重要|最新)</h4>(.*?)(?=<h4 class="tb">|</section>)',h,re.S):
        for s in sup: assert f'papers/{s}/"' not in blk.replace('../','').replace('papers/'+s+'/bilingual','x'), (f,s)
# the speed-read page itself still exists with its link
for k in B.SUPER:
    if not B.is_full(B.SUPER[k]): continue
    f=f'dist/papers/pmid-{k}/index.html'
    if os.path.exists(f): assert '已有更新版' in open(f,encoding='utf-8').read(), f
# real data from deep extract
assert B.is_full(B.SUPER['19481039']) and B.SUPER['19481039']['by']=='37766254'
assert not B.is_full(B.SUPER['37766254'])
assert '治疗部分已有更新版' in B.superlink(B.get('37766254'),'')
assert B._sup_rec({'superseded_by':'1'})['scope']=='full'  # missing scope = full
print('superseded tests OK')
