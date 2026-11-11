"""Certainty-aware 最重要 order: rated 高>中>低>极低; all unrated (provisional ignored) after every rated paper of that type."""
import os,sys
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
assert B.CERT_RANK['高']<B.CERT_RANK['中']<B.CERT_RANK['低']<B.CERT_RANK['极低']<B.NO_CERT
# unrated (even with provisional 高) does not outrank rated 中, same study type (横断面)
assert B.cert_rank(B.get('20005753'))==B.NO_CERT
assert B.cert_rank(B.get('32139728'))==B.CERT_RANK['中']
assert [p['pmid'] for p in B.tops('behavior')]==['23422366','32139728','20005753']
# 待评定 with or without provisional is NO_CERT; a final 极低 is still rated
assert B.cert_rank(B.get('11991408'))==B.NO_CERT
assert B.cert_rank(B.get('20187910'))==B.NO_CERT
assert B.cert_rank(B.get('40470278'))==B.CERT_RANK['极低']
# systematic reviews in dog AD: rated 极低 (40470278) before unrated 20187910
assert [p['pmid'] for p in B.tops('canine_atopic_dermatitis')]==['42805756','26260508','40470278']
# same type (队列): two rated 中 before unrated 25896026; among rated, higher cites/year first
assert [p['pmid'] for p in B.tops('epidemiology')]==['23647231','26581469','25896026']
# same type (RCT): rated 高 (23078651) before unrated 26776588
assert [p['pmid'] for p in B.tops('cardiomyopathy')]==['28965673','23078651','26776588']
# parent dermatology still has no top_picks row → empty tops(); page fallback is unchanged
assert B.tops('dermatology')==[]

# IRIS 2026 has no calendar date on iris-kidney.com; placeholder 2026-01-01 must not lose the date tie to 42693626
IRIS='x-international-renal-interest-society-2026-iris-staging-of-ckd-modified-2026'
assert B._pub_date(B.get(IRIS)) is None
for tid in ('nephrology','ckd'):
    ids=[p.get('pmid') or p.get('sid') or p.get('v5id') for p in B.tops(tid)]
    assert ids[0]==IRIS and ids[1]=='42693626', (tid, ids[:3])
print('ranking certainty tests OK')
