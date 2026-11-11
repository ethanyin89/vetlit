"""Copy reader fields from deep-speed-read extract files into data/v5/deep_speedread.json.

Only PMIDs listed in data/v5/deep_speedread_approved.json are written.
Presence in an extract file is not sufficient for rendering or for inclusion here.
Internal keys (check, source paths, certainty_ref, _meta) are dropped — they must not reach reader pages.

Sources: extracts/deep_speedread/batch1.json and later library/weekly extract files
(e.g. library_infectious_2026-11-10.json). To release a gated speed-read, add its PMID
to data/v5/deep_speedread_approved.json and re-run this script.
"""
import json, os, glob
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
SRC_DIR='/workspace/vetlit/extracts/deep_speedread'
OUT=os.path.join(ROOT,'data','v5','deep_speedread.json')
AP=json.load(open(os.path.join(ROOT,'data','v5','deep_speedread_approved.json'),encoding='utf-8'))
APPROVED=set(str(x) for x in AP['approved'])
KEEP=('pmid','title_zh','citation','design_and_basis','text_basis','section_order')
SKEEP=('heading','markdown')
SOURCES=['batch1.json','library_infectious_2026-11-10.json','weekly_2026-11-10.json']

def load_src_papers():
    by={}
    for name in SOURCES:
        fp=os.path.join(SRC_DIR,name)
        if not os.path.isfile(fp): continue
        src=json.load(open(fp,encoding='utf-8'))
        for r in src.get('papers') or []:
            pmid=str(r.get('pmid') or '')
            if pmid: by[pmid]=r
    return by

src_by=load_src_papers()
papers=[]
skipped=[]
for pmid,r in src_by.items():
    if pmid not in APPROVED:
        skipped.append(pmid)
        continue
    rec={k:r[k] for k in KEEP if k in r}
    rec['sections']={k:{sk:sv for sk,sv in (sec or {}).items() if sk in SKEEP} for k,sec in (r.get('sections') or {}).items()}
    papers.append(rec)
    print('OK', pmid, r.get('title_zh',''), list(rec['sections']))
missing=sorted(APPROVED - {str(r['pmid']) for r in papers})
if missing:
    raise SystemExit('approved PMIDs missing from extract sources: '+', '.join(missing))
json.dump({'papers':papers},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('wrote',OUT,'n=',len(papers),'skipped_unapproved=',len(skipped))
print('skipped:', ', '.join(skipped))
