"""Run: VETLIT_LIVE=1 python3 tests/test_hyperthyroid_batch.py — 2026-11-09 batch of 13 cat hyperthyroidism papers."""
import os, sys, re, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
NEW=['37167252','42004674','42800045','39831449','39724773','16478432','39019056','31998612','28158908','20695989','26081922','34730466','40559809']
LV={'42004674':'2','42800045':'2','39724773':'2','26081922':'4'}
ABS={'39724773','16478432','39019056','20695989'}
H=lambda pm: open(f'dist/papers/pmid-{pm}/index.html',encoding='utf-8').read()
t=B.TBY['hyperthyroidism']
pool={p['sid'] for p in B.tpapers(t)}
for pm in NEW:
    p=B.get(pm); assert p, pm
    assert 'pmid-'+pm in pool, pm
    assert p.get('fulltext_translation_allowed') is False and not B.X.can_translate(p) and not B.has_tr(p), pm
    assert not os.path.exists(f'dist/papers/pmid-{pm}/bilingual'), pm
    assert B.pick_reason(p)=='' , pm
    h=H(pm); top,fold=h.split('id="evidence"',1)
    assert '不允许全文翻译转载' in fold and '中英对照' not in top, pm
    for bad in ('Vibe','deep extract','裁定','排序规则','OpenAlex'): assert bad not in h, (pm,bad)
    if pm=='37167252':
        assert B.CERT[pm]['certainty'] is None and B.CERT[pm]['guideline_strength']=='该指南未分级'
        assert '该指南未分级' in h and B.level(p)=='指南/共识'
    elif pm=='42004674':   # knowledge summary: 不适用 (deep extract 2026-11-09), own strength Moderate
        assert B.CERT[pm]['certainty']=='不适用' and B.CERT[pm]['own_evidence_strength']=='Moderate'
        assert p['cebm_level']==LV.get(pm,'3'), pm
    elif pm=='31998612':   # full-text ROBINS-I Serious; GRADE 极低 (bias + surrogate at floor)
        assert B.CERT[pm]['certainty']=='极低'
        assert '证据确定性：极低' in h and 'ROBINS-I' in fold
        assert p['cebm_level']==LV.get(pm,'3') and B.level(p)=='Level '+LV.get(pm,'3'), pm
    else:
        assert B.CERT[pm]['certainty']=='待评定', pm
        assert '证据确定性待评定' in fold and '证据确定性：高' not in h and '证据确定性：中' not in h, pm
        assert p['cebm_level']==LV.get(pm,'3') and B.level(p)=='Level '+LV.get(pm,'3'), pm
    assert ('仅基于摘要' in h)==(pm in ABS), pm
    if pm in ABS: assert '资金：仅读摘要，未知' in top, pm
assert '二次文献' in H('42004674')
assert '42800045' in H('39724773') and '39724773' in H('42800045')   # shared Peterson cohort noted both ways
# not a supersession; AAFP 2016 stays current
assert '37167252' not in B.SUPER and '27143042' not in B.SUPER and not B.sup_info(B.get('27143042'))
assert '已有更新版' not in H('27143042')
# lists — single site rule (type > superseded last > 2021+ first > OpenAlex cites/yr); Vibe option (a) 2026-11-09
def L2(tid):
    imp=B.tops(tid); return [p['pmid'] for p in imp],[p['pmid'] for p in B.newest3(B.tpapers(B.TBY[tid]),imp)]
assert L2('hyperthyroidism')==(['37167252','27143042','31998612'],['42800045','40559809','39831449']), L2('hyperthyroidism')
assert L2('endocrinology')==(['37167252','41224734','42014100'],['42800045','40941356','40559809']), L2('endocrinology')
ids=lambda x: list(dict.fromkeys(re.findall(r'papers/pmid-(\d+)/"',x)))
for tid,(I,N) in (('hyperthyroidism',L2('hyperthyroidism')),('endocrinology',L2('endocrinology'))):
    s=open(f'dist/topics/{tid}/index.html',encoding='utf-8').read()
    a,b=s.split('<h4 class="tb">最新</h4>',1)
    assert ids(a.split('<h4 class="tb">最重要</h4>')[-1])==I and ids(b.split('<h2',1)[0])==N, tid
    assert 'OpenAlex' not in s and '年均' not in s and '排序' not in s, tid
    for c in re.findall(r'<article class="card">.*?</article>',s,re.S):
        if any(f'pmid-{p}/' in c for p in NEW): assert 'class="why"' not in c, (tid,c[:120])
for pm in NEW: assert set(B.get(pm)['topics'])=={'endocrinology','hyperthyroidism'}, pm
# 42004674: card label 知识摘要（二次文献）; rank slot = narrative review (top_picks item only, never shown)
assert '知识摘要（二次文献）' in B.cmeta(B.get('42004674')) and '叙述性综述' not in H('42004674')
for tid in ('hyperthyroidism','endocrinology'):
    g=next(x for x in B.X.TOP['topics'] if x['topic']==tid)
    it={str(i['pmid']):i for i in g['items']}
    assert it['42004674']['design']=='叙述性综述' and [str(i['pmid']) for i in g['items']][-1]=='42004674', tid
    assert all(not it[p].get('reason') for p in NEW), tid
print('hyperthyroid batch tests OK')
