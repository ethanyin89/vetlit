"""Idempotent: add deep extract's 13 cat hyperthyroidism treatment papers (speed reads 2026-11-05, CEBM levels
re-graded 2026-11-09 per Vibe) to site data. Touches ONLY these 13 PMIDs plus the hyperthyroidism topic pool/picks.
Sources: /workspace/vetlit/extracts/*_hyperthyroid_2026-11-05.json (speedread_fields_v5_, card_meta_, cebm_,
pick_reason_, text_source_, text_source_detail_). Bibliographic dates: Europe PMC firstPublicationDate (as the
rest of the library); first author / full title: PubMed esummary (fetched 2026-11-09), embedded below.
Team decisions: certainty 待评定 (no RoB yet); pick reasons empty; full-text translation off for all 13;
37167252 (AAHA 2023) sits beside 27143042 (AAFP 2016), not a supersession.
Re-run after scripts/sync_extras.py (sync overwrites speedread/certainty/card_meta/top_picks/text_source)."""
import json, os
S='/workspace/vetlit/extracts'; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); V=os.path.join(R,'data','v5'); X=os.path.join(V,'extras')
TAG='hyperthyroid_2026-11-05'
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
SR={r['pmid']:r for r in L(os.path.join(S,f'speedread_fields_v5_{TAG}.json'))}
CM=L(os.path.join(S,f'card_meta_{TAG}.json'))['papers']
CE=L(os.path.join(S,f'cebm_{TAG}.json'))['records']
PR=L(os.path.join(S,f'pick_reason_{TAG}.json'))
TS=L(os.path.join(S,f'text_source_{TAG}.json'))
TD=L(os.path.join(S,f'text_source_detail_{TAG}.json'))
# pmid: (title, first_author, pub_date[Europe PMC firstPublicationDate], design_category)
BIB={
 '37167252':('2023 AAHA Selected Endocrinopathies of Dogs and Cats Guidelines.','Bugbee A','2023-05-01','指南/共识'),
 '42004674':('In clinically hyperthyroid cats, is I-131 treatment superior to thyroidectomy in normalising serum T4 level?','Davies A','2022-10-01','知识摘要（二次文献）'),
 '42800045':('Long-term thyroid outcomes and survival in hyperthyroid cats treated with radioiodine: association with overt and subclinical hypothyroidism and levothyroxine.','Peterson ME','2026-09-01','队列研究'),
 '39831449':('Survival of radioiodine treated hyperthyroid cats that are euthyroid and hypothyroid after treatment, and effect of levothyroxine supplementation on survival.','Cox SE','2025-01-01','队列研究'),
 '39724773':('Hyperthyroid cats that develop azotemia following successful radioiodine treatment have shorter survival times compared to cats that remain nonazotemic.','Peterson ME','2024-12-26','队列研究'),
 '16478432':('Survival times for cats with hyperthyroidism treated with iodine 131, methimazole, or both: 167 cases (1996-2003).','Milner RJ','2006-02-01','队列研究'),
 '39019056':('Comparison of survival times of cats with hyperthyroidism treated with thyroidectomy or methimazole at a primary care hospital in Japan.','Naito E','2024-07-17','队列研究'),
 '31998612':('Iodine-restricted food versus pharmacological therapy in the management of feline hyperthyroidism: A controlled trial in 34 cats.','Grossi G','2019-07-24','非随机对照试验'),
 '28158908':('Efficacy of Low-dose (2 millicurie) versus Standard-dose (4 millicurie) Radioiodine Treatment for Cats with Mild-to-Moderate Hyperthyroidism.','Lucy JM','2017-02-03','队列研究'),
 '20695989':('Association of iatrogenic hypothyroidism with azotemia and reduced survival time in cats treated for hyperthyroidism.','Williams TL','2010-07-28','队列研究'),
 '26081922':('Effect of Feeding an Iodine-Restricted Diet in Cats with Spontaneous Hyperthyroidism.','Hui TY','2015-06-17','病例系列（无对照）'),
 '34730466':('Radioactive iodine dose and survival in cats with hyperthyroidism (2015-2020).','Chow JL','2021-11-03','队列研究'),
 '40559809':('Comparison of the Changes in Quality-of-Life of Cats with Hyperthyroidism Treated with Radioiodine or Antithyroid Drugs-A Preliminary Study.','Blunschi F','2025-06-11','队列研究'),
}
# reader-facing CEBM basis: short design wording condensed from cebm_*.json `reasoning` (which names reviewers/rules)
BASIS={'42004674':'二次文献（知识摘要）：按所引最高证据（1 项 RCT）定级','42800045':'前瞻性起始队列（预后）','39724773':'起始队列（预后），与 42800045 同一队列',
 '39831449':'非随机、有同期对照（补 LT4 vs 不补）','16478432':'非随机、同期比较三种疗法','39019056':'非随机、有同期对照','31998612':'前瞻性非随机、有同期对照',
 '28158908':'非随机、同期剂量比较','20695989':'回顾性预后队列（非明确起始队列）','26081922':'无对照病例系列','34730466':'回顾性预后队列','40559809':'非随机、有同期对照'}
NEW=list(BIB); assert set(BASIS)|{'37167252'}==set(NEW); assert set(NEW)==set(SR)==set(CM)==set(CE)==set(TS)==set(TD)==set(k for k in PR if k!='_meta'), 'source files disagree on the 13 PMIDs'
GUIDE='37167252'; ANCHOR='27143042'; TOPIC='hyperthyroidism'
EXPECT={'37167252':None,'42004674':'2','42800045':'2','39724773':'2','26081922':'4'}
for pm in NEW:
    lv=CE[pm]['new_level']
    if pm in EXPECT and EXPECT[pm] is not None: assert lv==EXPECT[pm],(pm,lv)
    elif pm==GUIDE: assert CE[pm]['card_display']=='该指南未分级'
    else: assert lv=='3',(pm,lv)
    assert not PR[pm].get('pick_reason_zh'), pm        # team decision: reasons empty
assert CE['42004674'].get('secondary_literature') is True
TOOL={'42004674':'ROBIS'}
def rob_tool(pm,cs):
    for t in ('ROBINS-I','QUIPS','ROBIS','JBI 病例系列清单'):
        if t in cs: return t
    return 'AGREE II' if pm==GUIDE else ''
def oa(v): return {'Y':'是','N':'否'}.get(v,'未核')
seed=L(os.path.join(V,'seed_library_v6.json')); byp={r.get('pmid'):i for i,r in enumerate(seed)}
for pm in NEW:
    s=SR[pm]; m=CM[pm]; c=CE[pm]; d=TD[pm]; ti,fa,pd,dc=BIB[pm]; g=pm==GUIDE
    absonly=TS[pm]=='abstract'
    if g: lvl='不适用（指南/共识，OCEBM 不分级）'
    else: lvl=c['new_level']
    basis='' if g else BASIS[pm]
    rec={'id':pm,'specialty':'内分泌','species':'cat+dog' if m['species_zh']=='猫和犬' else 'cat','title':ti,'first_author':fa,'year':m['year'],'journal':m['journal'],
      'doi':s['doi'],'pmid':pm,'pmcid':d.get('pmcid') or '','source':'deep extract 速读（'+('仅摘要' if absonly else '全文')+'，2026-11-05；CEBM 2026-11-09 按 Vibe 裁定）；PMID 经 Vibe 在 PubMed 核实',
      'oa':oa(d.get('is_open_access')),'doc_type':m['design_zh'],'recommendation_basis':'部分基于专家意见' if g else '不适用','sample_size_analysed':'未核',
      'multicenter':'不适用' if g else '未核','funding':s['funding_coi_zh'],'errata':'','internal_inconsistency':'',
      'one_line_conclusion_zh':s['one_line_conclusion_zh'],'clinical_utility':'','verified':'partial','japan_source':'是' if pm=='39019056' else '否',
      'cebm_question':'—' if g else c['question'],'cebm_level':lvl,'cebm_basis':basis,
      'rob_tool':rob_tool(pm,s.get('confidence_sentence') or ''),'rob_judgement':('未做 AGREE II 正式评分' if g else ('未评（仅摘要）' if absonly else '未评')),'rob_rationale':'',
      'guideline_recommendation':'该指南未分级' if g else '不适用','reporting_checklist':'AGREE 报告清单 / RIGHT' if g else '','grade_certainty_topic':'',
      'species_zh':'猫/犬' if m['species_zh']=='猫和犬' else m['species_zh'],'topics':[TOPIC],
      'n_enrolled':(m['n_label_zh']+('（纳入文献）' if pm=='42004674' else '')) if m.get('n_label_zh') else ('不适用' if g else '未核'),'n_analysed':'未核',
      'license':d.get('license') or '未核','license_source':d.get('license_source') or '','fulltext_translation_allowed':False,'results':'',
      'design_category':dc,'design_detail':m['design_zh'],'pub_date':pd,'pub_date_source':'Europe PMC firstPublicationDate',
      'importance_sort_key':None,'importance_rank':None,
      'population_type':'na' if pm in (GUIDE,'42004674') else 'natural','population_type_note':'指南/共识，无原始研究对象' if g else ('二次文献（知识摘要），无原始研究对象' if pm=='42004674' else ''),
      'rob_tool_note':'指南' if g else '','text_source_force':'摘要' if absonly else '全文'}
    if m.get('design_note_zh'): rec['cebm_note']=m['design_note_zh']
    if absonly: rec['basis_label']='仅基于摘要'
    if pm in byp: seed[byp[pm]]=rec
    else: seed.append(rec)
W(os.path.join(V,'seed_library_v6.json'),seed)
sr=L(os.path.join(V,'speedread_fields_v5.json')); sr=[r for r in sr if r.get('pmid') not in BIB]+[dict(SR[p]) for p in NEW]; W(os.path.join(V,'speedread_fields_v5.json'),sr)
cm=L(os.path.join(V,'card_meta.json')); cm['papers'].update({p:CM[p] for p in NEW}); W(os.path.join(V,'card_meta.json'),cm)
ce=L(os.path.join(V,'certainty.json'))
for pm in NEW:
    if pm==GUIDE:
        ce['papers'][pm]={'rules_applied':['R-guideline-own-strength'],'question_type':None,'question_basis':None,'start':None,'start_basis':'指南/共识：按团队规则不套用 GRADE','downgrades':[],'provisional':None,'certainty':None,
          'notes_zh':'指南/共识不评证据确定性，首屏显示指南自身推荐强度','guideline_strength':'该指南未分级','guideline_strength_source':f'extracts/cebm_{TAG}.json（card_display）'}
    else:
        t=rob_tool(pm,SR[pm].get('confidence_sentence') or '')
        ce['papers'][pm]={'rules_applied':['R-no-RoB-pending'],'question_type':CE[pm]['question'],'question_basis':f'extracts/cebm_{TAG}.json','start':None,'start_basis':'','downgrades':[],'provisional':None,
          'certainty':'待评定','notes_zh':'未做偏倚风险评估','pending_reason_zh':f'尚未做偏倚风险评估（{t}）' if t else '尚未做偏倚风险评估'}
W(os.path.join(V,'certainty.json'),ce)
ts=L(os.path.join(X,'text_source.json')); ts.update({p:TS[p] for p in NEW}); W(os.path.join(X,'text_source.json'),ts)
# ---- topic pool + manual ranking (team decision): 27143042, then AAHA 2023, existing picks kept, then CEBM asc, newer first
tpg=L(os.path.join(V,'topics_pages.json'))
t=next(x for x in tpg['topics'] if x['id']==TOPIC)
for p in NEW:
    if p not in t['all_ids']: t['all_ids'].append(p)
t['n']=len(t['all_ids'])
W(os.path.join(V,'topics_pages.json'),tpg)
rest=sorted([p for p in NEW if p!=GUIDE],key=lambda p:(int(CE[p]['new_level']),[-int(x) for x in BIB[p][2].split('-')]))
tp=L(os.path.join(X,'top_picks.json'))
g=next(x for x in tp['topics'] if x['topic']==TOPIC)
old=[i for i in g['items'] if str(i.get('pmid')) not in BIB]
assert old and str(old[0]['pmid'])==ANCHOR, [i['pmid'] for i in old]
new=lambda p:{'pmid':p,'reason':'','title':BIB[p][0],'year':CM[p]['year'],'design':CM[p]['design_zh']}
g['items']=old[:1]+[new(GUIDE)]+old[1:]+[new(p) for p in rest]
W(os.path.join(X,'top_picks.json'),tp)
print('merged',NEW); print('order',[i['pmid'] for i in g['items']])
