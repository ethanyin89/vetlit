"""Run: VETLIT_LIVE=1 python3 tests/test_same_cohort.py — a topic's 最重要+最新 hold at most one paper per same_cohort_as group."""
import os, sys, re, glob
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
PAIRS=[(k,str(x)) for k,m in B.CMETA.items() if isinstance(m,dict) for x in (m.get('same_cohort_as') or [])]
assert ('42800045','39724773') in PAIRS and ('39724773','42800045') in PAIRS, PAIRS
def bad(ids):
    s=set(ids); return [(a,b) for a,b in PAIRS if a in s and b in s]
ids=lambda x: list(dict.fromkeys(re.findall(r'papers/pmid-(\d+)/"',x)))
n=0
for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'):
    s=open(f,encoding='utf-8').read()
    blocks=[m.group(1) for m in re.finditer(r'<section class="tp">(.*?)</section>',s,re.S)] if f=='dist/index.html' else [s.split('<h2 class="sec"><span>03</span>',1)[0]]
    for b in blocks:
        if '最重要' not in b: continue
        L=ids(b.split('<h4 class="tb">最重要</h4>',1)[1]); n+=1
        assert not bad(L), (f,bad(L))
for t in B.TP:
    imp=B.tops(t['id']) or []; new=B.newest3(B.tpapers(t),imp)
    assert not bad([p['pmid'] for p in imp+new]), (t['id'],bad([p['pmid'] for p in imp+new]))
# unit: partner already in 最重要 is skipped in 最新; higher-ranked partner wins within a list
a,b=B.get('42800045'),B.get('39724773'); x=B.get('40559809'); y=B.get('39831449'); z=B.get('39019056')
assert [p['pmid'] for p in B._fill([b,a,x,y])]==['39724773','40559809','39831449']
assert [p['pmid'] for p in B._fill([a,x,y,z],taken=[b])]==['40559809','39831449','39019056']
assert [p['pmid'] for p in B.newest3([a,b,x,y])]==['42800045','40559809','39831449']
print(f'same-cohort dedupe tests OK ({n} list blocks)')
