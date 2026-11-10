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
# lists
imp=B.tops('hyperthyroidism'); new=B.newest3(B.tpapers(t),imp)
assert [p['pmid'] for p in imp]==['27143042','37167252','25673019'], [p['pmid'] for p in imp]
assert [p['pmid'] for p in new]==['42800045','40559809','39831449'], [p['pmid'] for p in new]
s=open('dist/topics/hyperthyroidism/index.html',encoding='utf-8').read()
a,b=s.split('<h4 class="tb">最新</h4>',1)
ids=lambda x: list(dict.fromkeys(re.findall(r'papers/pmid-(\d+)/"',x)))
assert ids(a.split('<h4 class="tb">最重要</h4>')[-1])==['27143042','37167252','25673019']
assert ids(b.split('<h2',1)[0])==['42800045','40559809','39831449']
assert 'class="why"' not in s and '15 篇已速读文献' in s
# ranking pool order in top_picks (manual; team decision)
g=next(x for x in B.X.TOP['topics'] if x['topic']=='hyperthyroidism')
order=[str(i['pmid']) for i in g['items']]
assert order[:3]==['27143042','37167252','25673019'] and sorted(order[3:])==sorted(set(NEW)-{'37167252'}), order
assert all(not i.get('reason') for i in g['items'] if str(i['pmid']) in NEW)
print('hyperthyroid batch tests OK')
