"""Certainty-aware 最重要 order: 高>中>低>极低; unrated use provisional; no value after 极低."""
import os,sys
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
assert B.CERT_RANK['高']<B.CERT_RANK['中']<B.CERT_RANK['低']<B.CERT_RANK['极低']<B.NO_CERT
# unrated with provisional 高 outranks rated 中, same study type (横断面)
assert B.cert_rank(B.get('20005753'))==B.CERT_RANK['高']
assert B.cert_rank(B.get('32139728'))==B.CERT_RANK['中']
assert [p['pmid'] for p in B.tops('behavior')]==['23422366','20005753','32139728']
# unrated with no provisional sorts after 极低
assert B.cert_rank(B.get('11991408'))==B.NO_CERT
assert B.cert_rank(B.get('40470278'))==B.CERT_RANK['极低']
# systematic reviews in dog AD: provisional 高 (20187910) before rated 极低 (40470278)
assert [p['pmid'] for p in B.tops('canine_atopic_dermatitis')]==['42805756','26260508','20187910']
# parent dermatology still has no top_picks row → empty tops(); page fallback is unchanged
assert B.tops('dermatology')==[]
print('ranking certainty tests OK')
