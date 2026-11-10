"""Run: VETLIT_LIVE=1 python3 tests/test_new_guidelines.py — 2026-11-04 guidelines, supersessions, errata, COI line."""
import os, sys, re
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
NEW={'42693626':['ckd','nephrology'],'41224734':['diabetes','endocrinology'],'42014100':['diabetes','endocrinology']}
for pm,ts in NEW.items():
    p=B.get(pm); assert p, pm
    assert set(ts)<=set(p.get('topics') or []), pm
    for t in ts: assert p['sid'] in [q['sid'] for q in B.tops(t)], (pm,t)
# supersessions
assert B.is_full(B.SUPER['26936494']) and B.SUPER['26936494']['by']=='42693626'
assert B.is_full(B.SUPER['25701862']) and B.SUPER['25701862']['by']=='41224734'
s=B.SUPER['29314873']; assert s['by']=='42014100' and s['scope']=='cats_only' and not B.is_full(s)
for t in ('diabetes',): assert 'pmid-29314873' in [q['sid'] for q in B.tops(t)], t
# endocrinology: 29314873 drops out of 最重要 after the 2026-11-09 re-rank (Vibe accepted)
for t in ('ckd','nephrology','diabetes','endocrinology'):
    ids=[q['sid'] for q in B.tops(t)+B.newest3(B.tpapers(B.TBY[t]))]
    assert 'pmid-26936494' not in ids and 'pmid-25701862' not in ids, t
for k in ('26936494','25701862','29314873'): assert B.X.TOP['supersessions'][k].get('supersession_quote'), k
assert '猫部分已有更新版' in B.superlink(B.get('29314873'),'')
# pages
H=lambda pm: open(f'dist/papers/pmid-{pm}/index.html',encoding='utf-8').read()
h=H('29314873'); assert '犬部分仍为现行' in h and '版本关系原文' in h
for pm in ('26936494','25701862'): assert '已有更新版' in H(pm)
# errata
h=H('36002137'); fold=h.split('id="evidence"',1)[1]; first=h.split('id="evidence"',1)[0]
assert 'pubmed.ncbi.nlm.nih.gov/36066350/' in fold and '⚠ 更正' not in first
h=H('42014100'); first=h.split('id="evidence"',1)[0]
assert '⚠ 更正' in first and '5–6' in first and '11–12' in first
assert re.search(r'关键数字.*?</ul><p class="note er">⚠',first,re.S)   # next to key numbers
# COI
for x in ('Adapet Medical','Boehringer Ingelheim','Dechra','Merck Animal Health','作者个人利益冲突声明未获取'): assert x in first, x
assert '利益冲突：无' not in h
# unit: missing erratum_pmid falls back to source; collapsed entries never first-screen
assert B.er_href({'erratum_pmid':None,'source':'https://x'})=='https://x'
assert not B.er_first({'display':'collapsed','affects_clinical':False})
print('new guidelines tests OK')
