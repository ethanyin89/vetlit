"""Prepare Vibe Feline seed_library_v4.json for merge_import.
Records already carrying a deep-extract reading page keep their extract values; only the v4-new fields are merged.
New records get all v4 fields (status 待速读/待评). Excluded list is checked so excluded papers never ship."""
import json, os, sys, glob
src, out = sys.argv[1], sys.argv[2]
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
NEWF=['species','species_zh','topics','n_enrolled','n_analysed','license','fulltext_translation_allowed','results','grade_certainty_topic']
cur={}
for f in glob.glob(os.path.join(ROOT,'data','papers','*.json')):
    r=json.load(open(f)); 
    for k in (r.get('pmid'),(r.get('doi') or '').lower(),r.get('id')):
        if k: cur[str(k)]=r
def existing(p):
    for k in (p.get('pmid'),(p.get('doi') or '').lower(),p.get('id')):
        if k and str(k) in cur: return cur[str(k)]
recs=[]
for p in json.load(open(os.path.join(src,'seed_library_v4.json'),encoding='utf-8')):
    p={k:v for k,v in p.items()}
    p['species_code']=p.get('species'); p['species']=p.get('species_zh') or p.get('species')
    e=existing(p)
    if e and e.get('reading_depth'):
        o={k:p[k] for k in NEWF if k in p}; o['species_code']=p['species_code']
        for k in ('pmid','doi','id'):
            if p.get(k): o[k]=p[k]
    else:
        o=p
        if not e: o['status']='待速读'; o['rob_judgement']=o.get('rob_judgement') or '待评'
    recs.append(o)
json.dump(recs,open(out,'w'),ensure_ascii=False); print(len(recs),'prepared')
ex=json.load(open(os.path.join(src,'seed_library_v4_excluded.json'),encoding='utf-8'))
ex=ex if isinstance(ex,list) else ex.get('excluded',ex.get('papers',[]))
hit=[x for x in ex if isinstance(x,dict) and existing(x)]
for x in hit: print('EXCLUDED but present:',x.get('pmid') or x.get('id'),x.get('title','')[:60])
print(len(ex),'excluded checked')
