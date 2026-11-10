"""Idempotent: add deep extract's 14 dog atopic dermatitis papers (files *_dogAD_2026-11-10.json, final) to site data.
New top-level topic 皮肤科 (PARENT_ID) with subtopic 犬特应性皮炎 (TOPIC). Touches ONLY these 14 PMIDs + the two new topics.
Team decisions: translation off for all 14; certainty 待评定 (guidelines: own strength, as other guidelines); reasons empty
except 42805756 (Vibe-approved text); supersession of 20456716/26276051 not wired (neither is in the library).
Ranking = the site's single rule (see add_hyperthyroid_2026_11_09.py): type > superseded last > 2021+ first > OpenAlex
cites/yr (today's counts, extras/openalex_cites_dogAD_2026-11-09.json). Unverified types rank in the lower type:
36940185 (label 系统评价（待核实）) and 42007020 (知识摘要（二次文献）) rank as 叙述性综述; 30115047 (core outcome set,
not clinical evidence) ranks as 叙述性综述; 20187911 (diagnostic criteria study) as 横断面研究.
Bibliographic dates: Europe PMC firstPublicationDate; first author / title: PubMed esummary (2026-11-09)."""
import json, os, re
S='/workspace/vetlit/extracts'; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); V=os.path.join(R,'data','v5'); X=os.path.join(V,'extras')
TAG='dogAD_2026-11-10'
PARENT_ID='dermatology'; PARENT_ZH='皮肤科'; PARENT_EN='Dermatology'      # Vibe 2026-11-09: new top-level parent
TOPIC='canine_atopic_dermatitis'; TOPIC_ZH='犬特应性皮炎'; TOPIC_EN='Canine atopic dermatitis'
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
SR={r['pmid']:r for r in L(os.path.join(S,f'speedread_fields_v5_{TAG}.json'))}
CM=L(os.path.join(S,f'card_meta_{TAG}.json'))['papers']; CE=L(os.path.join(S,f'cebm_{TAG}.json'))['records']
PR=L(os.path.join(S,f'pick_reason_{TAG}.json')); TS=L(os.path.join(S,f'text_source_{TAG}.json')); TD=L(os.path.join(S,f'text_source_detail_{TAG}.json'))
OA=L(os.path.join(X,'openalex_cites_dogAD_2026-11-09.json'))
# pmid: (title, first_author, pub_date, rank type)
BIB={
 '42805756':('Treatment of Canine Atopic Dermatitis: Updated Guidelines From the International Committee on Allergic Diseases of Animals (ICADA).','Mueller RS','2026-09-28','指南/共识'),
 '26260508':('Canine atopic dermatitis: detailed guidelines for diagnosis and allergen identification.','Hensel P','2015-08-11','指南/共识'),
 '20187910':('Interventions for atopic dermatitis in dogs: a systematic review of randomized controlled trials.','Olivry T','2010-02-01','系统综述/Meta分析'),
 '16412115':('A systematic review and meta-analysis of the efficacy and safety of cyclosporin for the treatment of atopic dermatitis in dogs.','Steffan J','2006-02-01','系统综述/Meta分析'),
 '36940185':('A systematic review of allergen immunotherapy, a successful therapy for canine atopic dermatitis and feline atopic skin syndrome.','Mueller RS','2023-03-24','叙述性综述'),
 '40470278':('Efficacy of diagnostic testing for allergen sensitization in canine atopic dermatitis: a systematic review.','Morales-Romero R','2025-05-21','系统综述/Meta分析'),
 '42007020':('In dogs with atopic skin disease, is lokivetmab more effective than oclacitinib in reducing the score of a recognised scoring system?','Cheung BYT','2022-04-01','叙述性综述'),
 '24581322':('A blinded, randomized, placebo-controlled trial of the efficacy and safety of the Janus kinase inhibitor oclacitinib (Apoquel®) in client-owned dogs with atopic dermatitis.','Cosgrove SB','2013-12-01','随机对照试验'),
 '25496303':('A blinded, randomized clinical trial comparing the efficacy and safety of oclacitinib and ciclosporin for the control of atopic dermatitis in client-owned dogs.','Little PR','2014-12-12','随机对照试验'),
 '27647569':('A blinded, randomized, placebo-controlled, dose determination trial of lokivetmab (ZTS-00103289), a caninized, anti-canine IL-31 monoclonal antibody in client owned dogs with atopic dermatitis.','Michels GM','2016-09-19','随机对照试验'),
 '28906040':('A blinded, randomized clinical trial evaluating the efficacy and safety of lokivetmab compared to ciclosporin in client-owned dogs with atopic dermatitis.','Moyaert H','2017-09-14','随机对照试验'),
 '34180084':('A masked, randomised clinical trial evaluating the efficacy and safety of lokivetmab compared to saline control in client-owned dogs with allergic dermatitis.','Van Brussel L','2021-06-27','随机对照试验'),
 '20187911':('A prospective study on the clinical features of chronic canine atopic dermatitis and its diagnosis.','Favrot C','2010-02-01','横断面研究'),
 '30115047':("Development of a core outcome set for therapeutic clinical trials enrolling dogs with atopic dermatitis (COSCAD'18).",'Olivry T','2018-08-16','叙述性综述'),
}
NEW=list(BIB); assert set(NEW)==set(SR)==set(CM)==set(CE)==set(TS)==set(TD)==set(OA)-{'_meta'}, 'source files disagree on the 14 PMIDs'
GUIDES={'42805756','26260508'}; REASON_PM='42805756'; REASON='取代 2010 版和 2015 版 ICADA 犬特应性皮炎治疗指南。'
# pre-merge checks (team list, 2026-11-09)
assert PR[REASON_PM]['pick_reason_zh']==REASON
assert all(not (PR[p] or {}).get('pick_reason_zh') for p in NEW if p!=REASON_PM)
assert CE['40470278']['level']=='3' and CE['30115047']['level']=='不适用（核心结局集）'
assert CE['16412115']['level']=='待全文核实' and CE['20187911']['level']=='待全文核实'
assert CM['42007020']['design_zh']=='知识摘要（二次文献）'
# 36940185 (deep extract update): label 系统评价（待核实）, CEBM 待全文核实; enforce if the file still says otherwise
OVR={}
if CM['36940185']['design_zh']!='系统评价（待核实）': OVR['design_zh']=(CM['36940185']['design_zh'],'系统评价（待核实）'); CM['36940185']['design_zh']='系统评价（待核实）'
if CE['36940185']['level']!='待全文核实': OVR['level']=(CE['36940185']['level'],'待全文核实'); CE['36940185']['level']='待全文核实'
if OVR: print('OVERRIDE 36940185',OVR)
seed=L(os.path.join(V,'seed_library_v6.json'))
assert not any(r.get('pmid') in ('20456716','26276051') for r in seed)   # superseded guidelines not in library -> no wiring
byp={r.get('pmid'):i for i,r in enumerate(seed)}
DC={'指南/共识':'指南/共识','系统综述/Meta分析':'系统综述/Meta分析','随机对照试验':'随机对照试验','横断面研究':'横断面研究'}
LABEL_DC={'36940185':'系统评价（待核实）','42007020':'知识摘要（二次文献）','30115047':'核心结局集共识'}
def rob_tool(pm,cs):
    for t in ('RoB 2','AMSTAR 2','ROBIS','QUADAS-2'):
        if t in cs: return t
    return 'AGREE II' if pm in GUIDES else ''
def lvl(pm):
    l=CE[pm]['level']
    return '不适用（指南/共识，OCEBM 不分级）' if pm in GUIDES else l
for pm in NEW:
    s=SR[pm]; m=CM[pm]; c=CE[pm]; d=TD[pm]; ti,fa,pd,rt=BIB[pm]; g=pm in GUIDES; absonly=TS[pm]=='abstract'
    sp=m.get('species_zh') or '犬'; both=sp in ('犬和猫','猫和犬')
    rec={'id':pm,'specialty':'皮肤','species':'cat+dog' if both else 'dog','title':ti,'first_author':fa,'year':m['year'],'journal':m['journal'],
      'doi':s['doi'],'pmid':pm,'pmcid':d.get('pmcid') or '','source':'deep extract 速读（'+('仅摘要' if absonly else '全文')+'，2026-11-10）；PMID 经 Vibe 在 PubMed 核实',
      'oa':{'Y':'是','N':'否'}.get(str(d.get('is_open_access') or '')[:1],'未核'),'doc_type':m['design_zh'],'recommendation_basis':'不适用','sample_size_analysed':'未核',
      'multicenter':'不适用' if g else '未核','funding':s['funding_coi_zh'],'errata':'','internal_inconsistency':'',
      'one_line_conclusion_zh':s['one_line_conclusion_zh'],'clinical_utility':'','verified':'partial','japan_source':'否',
      'cebm_question':'—' if g or not c.get('question') else c['question'],'cebm_level':lvl(pm),'cebm_basis':'',
      'rob_tool':rob_tool(pm,s.get('confidence_sentence') or ''),'rob_judgement':('未做 AGREE II 正式评分' if g else ('未评（仅摘要）' if absonly else '未评')),'rob_rationale':'',
      'guideline_recommendation':('SORT（逐条推荐强度见原文）' if pm=='42805756' else '该指南未分级') if g else '不适用','reporting_checklist':'AGREE 报告清单 / RIGHT' if g else '','grade_certainty_topic':'',
      'species_zh':'猫/犬' if both else '犬','topics':[TOPIC],
      'n_enrolled':m['n_label_zh'] if m.get('n_label_zh') else ('不适用' if g else '未核'),'n_analysed':'未核',
      'license':d.get('license') or '未核','license_source':d.get('license_source') or '','fulltext_translation_allowed':False,'results':'',
      'design_category':LABEL_DC[pm] if pm in LABEL_DC else DC[rt],'design_detail':m['design_zh'],'pub_date':pd,'pub_date_source':'Europe PMC firstPublicationDate',
      'importance_sort_key':None,'importance_rank':None,
      'population_type':'na' if (g or rt in ('系统综述/Meta分析','叙述性综述')) else 'natural','population_type_note':'',
      'rob_tool_note':'指南' if g else '','text_source_force':'摘要' if absonly else '全文'}
    if absonly: rec['basis_label']='仅基于摘要'
    if pm in byp: seed[byp[pm]]=rec
    else: seed.append(rec)
W(os.path.join(V,'seed_library_v6.json'),seed)
sr=L(os.path.join(V,'speedread_fields_v5.json')); sr=[r for r in sr if r.get('pmid') not in BIB]+[dict(SR[p]) for p in NEW]; W(os.path.join(V,'speedread_fields_v5.json'),sr)
cm=L(os.path.join(V,'card_meta.json')); cm['papers'].update({p:CM[p] for p in NEW}); W(os.path.join(V,'card_meta.json'),cm)
ce=L(os.path.join(V,'certainty.json'))
for pm in NEW:
    if pm in GUIDES:
        ce['papers'][pm]={'rules_applied':['R-guideline-own-strength'],'question_type':None,'question_basis':None,'start':None,'start_basis':'指南/共识：按团队规则不套用 GRADE','downgrades':[],'provisional':None,'certainty':None,
          'notes_zh':'指南/共识不评证据确定性，首屏显示指南自身推荐强度','guideline_strength':'SORT（逐条推荐强度见原文）' if pm=='42805756' else '该指南未分级','guideline_strength_source':f'extracts/speedread_fields_v5_{TAG}.json（confidence_sentence）'}
    else:
        t=rob_tool(pm,SR[pm].get('confidence_sentence') or '')
        ce['papers'][pm]={'rules_applied':['R-no-RoB-pending'],'question_type':CE[pm].get('question'),'question_basis':f'extracts/cebm_{TAG}.json','start':None,'start_basis':'','downgrades':[],'provisional':None,
          'certainty':'待评定','notes_zh':'未做偏倚风险评估','pending_reason_zh':f'尚未做偏倚风险评估（{t}）' if t else '尚未做偏倚风险评估'}
W(os.path.join(V,'certainty.json'),ce)
ts=L(os.path.join(X,'text_source.json')); ts.update({p:TS[p] for p in NEW}); W(os.path.join(X,'text_source.json'),ts)
# ranking (single site rule)
TYPES=['指南/共识','系统综述/Meta分析','随机对照试验','非随机对照试验','队列研究','病例对照研究','横断面研究','病例系列（无对照）','叙述性综述','实验/基础研究']
cpy=lambda p: OA[p]/(2026-int(CM[p]['year'])+1)
key=lambda p:(TYPES.index(BIB[p][3]),False,int(CM[p]['year'])<2021,-round(cpy(p),2),[-int(x) for x in BIB[p][2].split('-')])
ORDER=sorted(NEW,key=key)
tpg=L(os.path.join(V,'topics_pages.json'))
T=[t for t in tpg['topics'] if t['id'] not in (PARENT_ID,TOPIC)]
T.append({'id':PARENT_ID,'name_zh':PARENT_ZH,'name_en':PARENT_EN,'parent':None,'n':0,'bottom_line':'','bottom_line_source':'','core':[],'newest':[],'all_ids':[],'bottom_line_clinical':False})
T.append({'id':TOPIC,'name_zh':TOPIC_ZH,'name_en':TOPIC_EN,'parent':PARENT_ID,'n':len(ORDER),'bottom_line':'','bottom_line_source':'','core':[],'newest':[],'all_ids':ORDER,'bottom_line_clinical':False})
tpg['topics']=T; W(os.path.join(V,'topics_pages.json'),tpg)
tp=L(os.path.join(X,'top_picks.json'))
tp['topics']=[g for g in tp['topics'] if g['topic']!=TOPIC]+[{'topic':TOPIC,'topic_zh':TOPIC_ZH,'items':[{'pmid':p,'reason':'','title':BIB[p][0],'year':CM[p]['year'],'design':BIB[p][3]} for p in ORDER]}]
W(os.path.join(X,'top_picks.json'),tp)
# 42805756 reason (Vibe-approved exact text) for both lists, topic + parent
pr=L(os.path.join(X,'pick_reason.json'))
pr[REASON_PM]=[{'topic':t,'list':l,'backfill':False,'pick_reason_zh':REASON,'approved':True,'approved_by':'Vibe','basis':PR[REASON_PM]['basis']} for t in (TOPIC,PARENT_ID) for l in ('最重要','最新')]
W(os.path.join(X,'pick_reason.json'),pr)
print('merged',NEW); print('order',ORDER)
