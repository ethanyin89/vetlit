"""Copy reader fields from extracts/deep_speedread/batch1.json into data/v5/deep_speedread.json.

Only PMIDs listed in data/v5/deep_speedread_approved.json are written.
Presence in batch1.json is not sufficient for rendering or for inclusion here.
Internal keys (check, source paths, certainty_ref, _meta) are dropped — they must not reach reader pages.
"""
import json, os
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
SRC='/workspace/vetlit/extracts/deep_speedread/batch1.json'
OUT=os.path.join(ROOT,'data','v5','deep_speedread.json')
AP=json.load(open(os.path.join(ROOT,'data','v5','deep_speedread_approved.json'),encoding='utf-8'))
APPROVED=set(str(x) for x in AP['approved'])
KEEP=('pmid','title_zh','citation','design_and_basis','text_basis','section_order')
SKEEP=('heading','markdown')
src=json.load(open(SRC,encoding='utf-8'))
papers=[]
skipped=[]
for r in src['papers']:
    pmid=str(r.get('pmid') or '')
    if pmid not in APPROVED:
        skipped.append(pmid)
        continue
    rec={k:r[k] for k in KEEP if k in r}
    rec['sections']={k:{sk:sv for sk,sv in (sec or {}).items() if sk in SKEEP} for k,sec in (r.get('sections') or {}).items()}
    papers.append(rec)
    print('OK', pmid, r.get('title_zh',''), list(rec['sections']))
missing=sorted(APPROVED - {str(r['pmid']) for r in papers})
if missing:
    raise SystemExit('approved PMIDs missing from batch1.json: '+', '.join(missing))
json.dump({'papers':papers},open(OUT,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('wrote',OUT,'n=',len(papers),'skipped_unapproved=',len(skipped))
print('skipped:', ', '.join(skipped))
