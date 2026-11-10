"""Idempotent, internal data only (never rendered as such):
(1) certainty _meta: append Vibe-approved rule texts (2026-11-09) under rules_v4_amend_2026-11-09_dogAD, using the rule ids
    the paper entries already reference; set the R-down-indirectness-population sentence to the approved wording;
    add deep extract's downgrades_schema.
(2) downgrades: take ONLY the `downgrades` field from deep extract's certainty.json for the papers that have downgrades
    (normalized objects {domain, steps, reason_zh, source_file}; steps -1/-2, 0 = considered, not downgraded). Nothing else."""
import json, os
S='/workspace/vetlit/extracts'; V=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
src=L(os.path.join(S,'certainty.json')); ce=L(os.path.join(V,'certainty.json'))
RULES={'R-nodown-bias-toward-null':'偏倚朝向无效不降级：只在退出原因是无效、且用药组退出明显少于对照组时适用；各组都大量缺失时照常降级。',
 'R-down-noninferiority-ITT-CI':'非劣效试验：每项结局分开判定，看组间差值（或检验值）是否落在界值内；写出界值，不算 NNT。',
 'R-SR-body-of-evidence':'系统评价：确定性按证据本身定。综述自己做过 GRADE 的，用它的结果；没做过的，按纳入研究推。综述自身的质量只写在 review_rob_* 里。'}
used={x for r in ce['papers'].values() if isinstance(r,dict) for x in (r.get('rules_applied') or [])}
assert set(RULES)<=used, set(RULES)-used
ce['_meta'].setdefault('rules_v4_amend_2026-11-09_dogAD',RULES)
assert ce['_meta']['rules_v4_amend_2026-11-09_dogAD']==RULES
IND='R-down-indirectness-population：研究人群比专题问题宽时，降一级。'   # no reviewer names in rule text
assert ce['_meta']['rules_v4_amend_2026-11-09_indirectness'].startswith('R-down-indirectness-population')
ce['_meta']['rules_v4_amend_2026-11-09_indirectness']=IND
ce['_meta']['downgrades_schema']=src['_meta']['downgrades_schema']
DG=['39858209','39417648','38884190','18638016','32139728','30548336','26581469','25231385','23647231','32441826','30543707','28152671','40941356','25496303','27647569','34180084','28906040','20187911','40470278']   # the 19 of 2026-11-09
for k in DG:
    d=src['papers'][k]['downgrades']
    assert all(isinstance(x,dict) and {'domain','steps','reason_zh'}<=set(x) and x['steps'] in (0,-1,-2,-3) for x in d), k
    ce['papers'][k]['downgrades']=d
W(os.path.join(V,'certainty.json'),ce); print('meta rules',sorted(RULES),'; downgrades merged',len(DG))
