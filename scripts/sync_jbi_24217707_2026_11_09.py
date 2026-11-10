"""Idempotent: 24217707's JBI prevalence checklist (deep extract rob_round1_2026-11-04.json, that entry only) -> live bias-assessment data
(appraisal_papers.json items/tool/note; seed_library_v6.json rob_tool/rob_judgement). Nothing else."""
import json, os
S='/workspace/vetlit/extracts/rob_round1_2026-11-04.json'; V=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
PM='24217707'; TOOL='JBI 患病率清单'
r=L(S)['papers'][PM]; assert r['tool'].startswith('JBI') and len(r['items'])==9 and r['overall_rob']=='高'
ITEMS=[{'item':i['domain'],'judgment':i['judgement'],'reason':i.get('reason_zh') or '','evidence_quote':i.get('quote') or ''} for i in r['items']]
NOTE=f'{TOOL}：{r["overall_rob"]}'
f=os.path.join(V,'appraisal_papers.json'); ap=L(f); a=next(x for x in ap if str(x.get('pmid'))==PM)
a.update({'appraisal_tool':TOOL,'appraisal_items':ITEMS,'appraisal_note':NOTE,'methods_review':NOTE}); W(f,ap)
f=os.path.join(V,'seed_library_v6.json'); sd=L(f); s=next(x for x in sd if str(x.get('pmid'))==PM)
s.update({'rob_tool':TOOL,'rob_judgement':r['overall_rob']}); W(f,sd)
print('24217707 JBI synced:',NOTE,len(ITEMS),'items')
