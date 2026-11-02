"""Canonical field names: see SCHEMA.md. Merge external JSON deliveries into data/papers/, matched by PMID, then DOI (case-insensitive, doi.org prefix stripped), then stable `id`.
Usage: python3 scripts/merge_import.py <file.json|dir> [--source vibe-feline|deep-extract]
Accepts a list of objects, a dict {pmid: obj}, or a directory of *.json. Chinese keys (schema.md aliases) are normalised.
Rules: incoming non-empty values overwrite; lists of errata/internal_inconsistencies are unioned; never deletes fields.
Deep-extract `detail_md` (markdown string) is written to content/<id>.md and linked."""
import json, os, sys, glob, re
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
ALIAS = {'专科':'specialty','物种':'species','标题':'title','第一作者':'first_author','年份':'year','期刊':'journal','开放获取':'oa','OA':'oa',
 '文献类型':'doc_type','证据水平':'cebm_level','偏倚风险工具':'rob_tool','偏倚风险判断':'rob_judgement','报告规范':'reporting_checklist','指南推荐强度':'guideline_recommendation','推荐依据':'recommendation_basis','分析样本量':'sample_size_analysed','实际分析样本量':'sample_size_analysed','n':'sample_size_analysed',
 '多中心':'multicenter','降级标签':'downgrade_tags','资助方':'funding','funder':'funding','勘误':'errata','勘误与更正':'errata','内部矛盾':'internal_inconsistency','论文内部矛盾':'internal_inconsistency',
 '分级理由':'grade_reason','一句话结论':'one_line_conclusion_zh','one_line':'one_line_conclusion_zh','临床可用性':'clinical_utility','clinical_usability':'clinical_utility','核对':'verified','日本来源':'japan_source',
 '中文标题':'title_zh','全文状态':'fulltext_status','推荐强度':'recommendation_strength','适用范围':'scope','核心推荐':'core_recommendations','证据薄弱点':'evidence_gaps','与旧版相比的变化':'changes_vs_previous','速读页':'detail_md'}
UNION = {'errata_detail','internal_inconsistency_detail'}
def norm(o): return {ALIAS.get(k,k):v for k,v in o.items()}
def load(path):
    if os.path.isdir(path):
        out=[]; [out.extend(load(f)) for f in sorted(glob.glob(os.path.join(path,'*.json')))]; return out
    d=json.load(open(path,encoding='utf-8-sig'))
    if isinstance(d,dict) and not ({'pmid','PMID','doi','DOI','id'} & set(d)): d=[{**v,'pmid':k} if str(k).isdigit() else {**v,'id':v.get('id',k)} for k,v in d.items()]
    return d if isinstance(d,list) else [d]
def ndoi(v):
    v=str(v or '').strip().lower()
    return re.sub(r'^(https?://(dx\.)?doi\.org/|doi:\s*)','',v).strip()
def slug(v): return re.sub(r'[^a-z0-9]+','-',str(v).lower()).strip('-')
def index():
    idx={}
    for f in glob.glob(os.path.join(ROOT,'data','papers','*.json')):
        r=json.load(open(f,encoding='utf-8'))
        if r.get('pmid'): idx.setdefault(('pmid',str(r['pmid']).strip()),f)
        if r.get('doi'): idx.setdefault(('doi',ndoi(r['doi'])),f)
        idx.setdefault(('id',str(r.get('id') or os.path.basename(f)[:-5])),f)
    return idx
def keys(o):
    pmid=str(o.get('pmid') or o.get('PMID') or '').strip(); doi=ndoi(o.get('doi') or o.get('DOI')); rid=str(o.get('id') or '').strip()
    return pmid,doi,rid
def main():
    args=sys.argv[1:]; src=args[args.index('--source')+1] if '--source' in args else 'external'
    path=[a for a in args if not a.startswith('--') and a!=src][0]
    new=upd=skip=0; idx=index()
    for o in load(path):
        o=norm(o); o.pop('PMID',None); o.pop('DOI',None)
        pmid,doi,rid=keys(o)
        if not (pmid or doi or rid):
            print('WARNING skip (no pmid/doi/id):', str(o.get('title','?'))[:60], file=sys.stderr); skip+=1; continue
        f=(pmid and idx.get(('pmid',pmid))) or (doi and idx.get(('doi',doi))) or (rid and idx.get(('id',rid)))
        if f: cur=json.load(open(f,encoding='utf-8')); upd+=1
        else:
            pid='pmid-'+pmid if pmid else 'doi-'+slug(doi) if doi else slug(rid)
            f=os.path.join(ROOT,'data','papers',pid+'.json'); new+=1
            cur={'id':pid,'status':'待处理','source':src}
        pid=cur['id']; o.pop('id',None)
        if pmid: o['pmid']=pmid
        if doi: o['doi']=doi
        if rid and rid!=pid: cur.setdefault('alt_ids',[]); rid in cur['alt_ids'] or cur['alt_ids'].append(rid)
        for k in ('evidence_grade','grade_v1','grade_reason','downgrade_tags'): o.pop(k,None); cur.pop(k,None)
        md=o.pop('detail_md',None)
        if md:
            open(os.path.join(ROOT,'content',pid+'.md'),'w').write(md); cur['detail']=pid+'.md'
        for k,v in o.items():
            if v in (None,'',[]): continue
            if k in UNION and isinstance(v,list):
                old=cur.get(k) or []; cur[k]=old+[x for x in v if x not in old]
            else: cur[k]=v
        cur.setdefault('provenance',[]); cur['provenance']=[x for x in cur['provenance'] if x!=src]+[src]
        json.dump(cur,open(f,'w'),ensure_ascii=False,indent=2)
        idx[('id',pid)]=f
        if pmid: idx[('pmid',pmid)]=f
        if doi: idx[('doi',doi)]=f
    print(f'merged from {src}: {upd} updated, {new} new, {skip} skipped')
    return skip
if __name__=='__main__': main()
