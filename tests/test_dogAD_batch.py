"""Run: VETLIT_LIVE=1 python3 tests/test_dogAD_batch.py — 2026-11-10 batch of 14 dog atopic dermatitis papers."""
import os, sys, re, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
NEW=['42805756','26260508','20187910','16412115','36940185','40470278','42007020','24581322','25496303','27647569','28906040','34180084','20187911','30115047']
SRC=json.load(open('/workspace/vetlit/extracts/certainty.json',encoding='utf-8'))['papers']
GUIDES={'42805756','26260508'}; REASON='取代 2010 版和 2015 版 ICADA 犬特应性皮炎治疗指南。'
TOPIC,PARENT='canine_atopic_dermatitis','dermatology'
H=lambda pm: open(f'dist/papers/pmid-{pm}/index.html',encoding='utf-8').read()
assert B.TBY[PARENT]['parent'] is None and B.TBY[PARENT]['name_zh']=='皮肤科'
assert B.TBY[TOPIC]['parent']==PARENT and B.TBY[TOPIC]['name_zh']=='犬特应性皮炎'
pool={p['sid'] for p in B.tpapers(B.TBY[TOPIC])}; assert pool=={'pmid-'+p for p in NEW}
assert {p['sid'] for p in B.tpapers(B.TBY[PARENT])}==pool
for pm in NEW:
    p=B.get(pm); assert p and p['topics']==[TOPIC], pm
    assert p['fulltext_translation_allowed'] is False and not B.X.can_translate(p) and not os.path.exists(f'dist/papers/pmid-{pm}/bilingual'), pm
    h=H(pm); top,fold=h.split('id="evidence"',1)
    for bad in ('Vibe','deep extract','裁定','OpenAlex','年均'): assert bad not in h, (pm,bad)
    if pm in GUIDES: assert B.CERT[pm]['certainty'] is None
    elif pm=='30115047': assert B.CERT[pm]['certainty']=='不适用' and 'R-na-nonclinical' in B.CERT[pm]['rules_applied'] and '不分级' in top, pm
    else: assert B.CERT[pm]==SRC[pm], pm
    if B.CERT[pm].get('certainty')=='待评定': assert '证据确定性待评定' in fold, pm
    assert not any(x in str(B.CERT[pm].get('rob_tool') or '') for x in ('AMSTAR','ROBIS')), pm
    assert (B.pick_reason(p,TOPIC,'最重要')==REASON)==(pm=='42805756'), pm
lv=lambda pm: re.search(r'Oxford CEBM 2011</th><td>([^<]*)',H(pm)).group(1)
assert lv('40470278')=='3' and lv('30115047')=='不适用（核心结局集）'
assert lv('16412115')=='待全文核实' and lv('20187911')=='4' and lv('36940185')=='不适用（叙述性综述）'
assert '知识摘要（二次文献）' in B.cmeta(B.get('42007020')) and '叙述性综述' in B.cmeta(B.get('36940185'))
# RoB round 1 (Vibe-reviewed): review-quality row for 40470278 (ROBIS), study-level RoB result shown in 偏倚风险
h=H('40470278'); assert '<tr><th>综述偏倚风险（ROBIS）</th><td>高</td></tr>' in h.split('id="evidence"',1)[1] and '综述偏倚风险' not in h.split('id="evidence"',1)[0]
assert 'RoB 2 总体：一些担忧' in H('24581322')
# 28906040: non-inferiority test value and margin
assert '0.3%' in H('28906040') and '15% 界值' in H('28906040')
# 20456716 / 26276051 not in library -> no supersession wiring, no 已有更新版 links
assert not B.get('20456716') and not B.get('26276051') and '20456716' not in B.SUPER and '26276051' not in B.SUPER
assert '已有更新版' not in H('42805756')
# ranking: single site rule; unverified types rank in the lower type (top_picks 'design' only)
g=next(x for x in B.X.TOP['topics'] if x['topic']==TOPIC); it={str(i['pmid']):i for i in g['items']}
for pm in ('36940185','42007020','30115047'): assert it[pm]['design']=='叙述性综述', pm
assert all(not i.get('reason') for i in g['items'])
L2=lambda t:([p['pmid'] for p in B.tops(t) or B._fill([B.get(c['id']) for c in B.TBY[t].get('core') or []] or sorted(B.tpapers(B.TBY[t]),key=lambda p:p.get('importance_rank') or 999))])
for t in (TOPIC,PARENT):
    s=open(f'dist/topics/{t}/index.html',encoding='utf-8').read(); a,b=s.split('<h4 class="tb">最新</h4>',1)
    ids=lambda x: list(dict.fromkeys(re.findall(r'papers/pmid-(\d+)/"',x)))
    assert ids(a.split('<h4 class="tb">最重要</h4>')[-1])==['42805756','26260508','40470278'], (t,ids(a))
    assert ids(b.split('<h2',1)[0])==['36940185','42007020','34180084'], (t,ids(b))
    assert s.count(f'<p class="why">{REASON}</p>')==1 and len(re.findall(r'<p class="why">',s))==1, t
# 2026-11-09 follow-up: certainty entries from deep extract; 42805756 COI 待查
h=H('42805756'); top=h.split('id="evidence"',1)[0]
fold=h.split('id="evidence"',1)[1]
for x in ('self-funded','World Association for Veterinary Dermatology','Projekt DEAL','R.M.：','D.S.：','不代表 ICADA 为其背书'): assert x in fold, x
assert '待查' not in h and '7.7' not in h and '资助/利益冲突：资金：本文自筹' in top
assert '指南推荐强度：指南自身用 SORT 给推荐强度' in top
assert B.CERT['26260508']['guideline_strength']=='该指南未分级'
assert B.CERT['34180084']['certainty']=='中' and 'R-down-indirectness-population' in B.CERT['34180084']['rules_applied']
M=json.load(open('data/v5/certainty.json',encoding='utf-8'))['_meta']; assert M['rules_v4_amend_2026-11-09_indirectness'].startswith('R-down-indirectness-population')
import glob
for f in glob.glob('dist/**/*.html',recursive=True): assert not re.search(r'\bR-(?:down|nodown|design|VF|na|start|SR|guideline|no|rob)-',open(f,encoding='utf-8').read()), f
print('dogAD batch tests OK')
