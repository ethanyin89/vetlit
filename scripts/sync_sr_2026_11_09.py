"""Idempotent: (1) take deep extract's redone certainty entries for the systematic reviews 39858209 and 40941356
(40470278 comes with the dog AD batch, add_dogAD_2026_11_10.py) incl. review_rob_* (AMSTAR 2 / ROBIS stay out of rob_*);
(2) apply extracts/confidence_sentence_SR_override_2026-11-09.json to speedread_fields_v5.json for these two PMIDs only.
Never copies whole files; never deletes live entries."""
import json, os
S='/workspace/vetlit/extracts'; V=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
PMS=('39858209','40941356')
src=L(os.path.join(S,'certainty.json'))['papers']; ce=L(os.path.join(V,'certainty.json'))
for k in PMS:
    r=src[k]; assert r.get('review_rob_tool') and r.get('review_rob_overall'), k
    assert not any(x in str(r.get('rob_tool') or '') for x in ('AMSTAR','ROBIS')), k
    ce['papers'][k]=r
W(os.path.join(V,'certainty.json'),ce)
O=L(os.path.join(S,'confidence_sentence_SR_override_2026-11-09.json'))
FIELDS={'39858209':('confidence_sentence','one_line_conclusion_zh','title_zh','clinical_meaning'),'40941356':('confidence_sentence',)}
sr=L(os.path.join(V,'speedread_fields_v5.json')); n=0
for r in sr:
    k=str(r.get('pmid') or '')
    if k in FIELDS:
        for f in FIELDS[k]:
            if O.get(k,{}).get(f): r[f]=O[k][f]; n+=1
W(os.path.join(V,'speedread_fields_v5.json'),sr); print('SR sync: certainty',PMS,'; speedread fields set',n)
