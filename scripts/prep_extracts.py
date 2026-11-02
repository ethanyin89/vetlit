"""Convert deep extract delivery (papers.json + <file>.md) into a merge_import-ready JSON list.
Usage: python3 scripts/prep_extracts.py /workspace/vetlit/extracts out.json
Drops v2_legacy (A–D) and pre-rendered bibtex/ris; maps fields onto SCHEMA.md names; never invents values."""
import json, os, re, sys
src, out = sys.argv[1], sys.argv[2]
SP={'两者':'猫/犬','猫':'猫','犬':'犬'}
NEUTRAL_LEGACY=re.compile(r'.*Stage 1 曾给"证据等级 [A-D]".*\n?')
def depth(s):
    s=s or ''
    return '全文' if s.startswith('全文') else '摘要' if '摘要' in s else '仅标题' if '题录' in s or '标题' in s else s
recs=[]
for p in json.load(open(os.path.join(src,'papers.json'),encoding='utf-8')):
    p=dict(p)
    for k in ('v2_legacy','bibtex','ris','funder','clinical_usability','species_v2','url'): p.pop(k,None)
    p['species']=SP.get(p.get('species'),p.get('species'))
    p['reading_depth']=depth(p.get('source')); p['reading_source']=p.pop('source',None)
    items=p.get('appraisal_items') or []
    p['rob_tool']=p.pop('appraisal_tool',None)
    ov=[i for i in items if i.get('item','').startswith('总体')]
    if ov: p['rob_judgement']=ov[0]['judgment']; p['rob_rationale']=ov[0].get('reason','')
    else: p['rob_judgement']='见逐项判断（该工具不设总体判断）'; p['rob_rationale']=''
    rc=p.pop('reporting_check',None) or {}
    if rc: p['reporting_checklist']=rc.get('guideline',''); p['reporting_notes']=rc.get('notes','')
    gs=p.pop('guideline_strengths_verbatim',None)
    if gs: p['guideline_recommendation']='；'.join(gs)
    p['extract_id']=p.pop('id')
    p['id']=p['extract_id'] if not (p.get('pmid') or p.get('doi')) else None
    f=p.pop('file',None)
    if f and os.path.exists(os.path.join(src,f)):
        p['detail_md']=NEUTRAL_LEGACY.sub('',open(os.path.join(src,f),encoding='utf-8').read())
    else: print('WARNING no md for',p['extract_id'],file=sys.stderr)
    p['cebm_basis']=p.get('cebm_basis') or ''
    recs.append({k:v for k,v in p.items() if v is not None})
json.dump(recs,open(out,'w'),ensure_ascii=False,indent=1); print(len(recs),'records prepared')
