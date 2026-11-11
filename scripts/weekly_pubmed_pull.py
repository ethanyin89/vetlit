"""Weekly PubMed pull per topic for deep extract screening.

Reads search strings from data/v5/topic_queries.json (placeholders copied from
data/topics.json until deep extract writes them and Vibe reviews). Dedupes
against the reader library (data/v5/seed_library_v6.json and data/papers) and
the existing screening queue. New hits are appended to data/v5/ingest_queue.json.

Candidates are not written to data/papers and must not be shown to readers until
they are screened, written up, and listed in data/v5/weekly_new_approved.json.

Reuses the same E-utilities settings as scripts/ingest.py (species filter,
hasabstract, publication-type excludes, edat window).

Env: NCBI_API_KEY (optional), NCBI_EMAIL (optional), WEEKLY_DAYS (default 7).
Set WEEKLY_PULL=0 to skip the network call (used by tests).
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
QFILE=os.path.join(ROOT,'data','v5','topic_queries.json')
QUEUE=os.path.join(ROOT,'data','v5','ingest_queue.json')
SEED=os.path.join(ROOT,'data','v5','seed_library_v6.json')
PAPERS=os.path.join(ROOT,'data','papers')
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
EXCLUDE_TYPES={'Comment','Editorial','Letter','News','Published Erratum','Retraction of Publication','Retracted Publication'}
SPECIES='("Cats"[MeSH Terms] OR "Dogs"[MeSH Terms] OR "Cat Diseases"[MeSH Terms] OR "Dog Diseases"[MeSH Terms])'

def get(ep, **p):
    p.setdefault('tool','vetlit')
    if os.environ.get('NCBI_API_KEY'): p['api_key']=os.environ['NCBI_API_KEY']
    if os.environ.get('NCBI_EMAIL'): p['email']=os.environ['NCBI_EMAIL']
    url=BASE+ep+'?'+urllib.parse.urlencode(p)
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'vetlit-weekly-pull'}),timeout=60) as r:
                return json.load(r)
        except Exception:
            if t==3: raise
            time.sleep(2*(t+1))

def load_queries():
    d=json.load(open(QFILE,encoding='utf-8'))
    topics=[t for t in (d.get('topics') or []) if t.get('pubmed_query')]
    species=d.get('species_filter') or SPECIES
    return topics, species

def library_pmids():
    """PMIDs already in the reader library or already sitting in data/papers (including 待处理 ingest)."""
    out=set()
    if os.path.exists(SEED):
        seed=json.load(open(SEED,encoding='utf-8'))
        recs=seed if isinstance(seed,list) else (seed.get('papers') or seed.get('records') or [])
        for r in recs:
            if r.get('pmid'): out.add(str(r['pmid']))
    if os.path.isdir(PAPERS):
        for fn in os.listdir(PAPERS):
            if not fn.endswith('.json'): continue
            try:
                r=json.load(open(os.path.join(PAPERS,fn),encoding='utf-8'))
            except Exception:
                continue
            if r.get('pmid'): out.add(str(r['pmid']))
            # also from filename
            if fn.startswith('pmid-'): out.add(fn[5:-5])
    return out

def queue_pmids(q=None):
    q=q if q is not None else load_queue()
    return {str(c.get('pmid') or '') for c in (q.get('candidates') or []) if c.get('pmid')}

def load_queue():
    if not os.path.exists(QUEUE):
        return {'_note':'Screening queue for deep extract. Candidates here are not shown on reader pages.','updated':None,'candidates':[]}
    return json.load(open(QUEUE,encoding='utf-8'))

def save_queue(q):
    os.makedirs(os.path.dirname(QUEUE),exist_ok=True)
    json.dump(q, open(QUEUE,'w',encoding='utf-8'), ensure_ascii=False, indent=2)
    open(QUEUE,'a',encoding='utf-8').write('\n')

def merge_candidates(queue, new_recs, today=None):
    """Append records whose pmid is not already queued. Returns (queue, n_added)."""
    have=queue_pmids(queue)
    added=0
    today=today or time.strftime('%Y-%m-%d')
    for rec in new_recs:
        pmid=str(rec.get('pmid') or '')
        if not pmid or pmid in have: continue
        row={k:rec[k] for k in rec if k in ('pmid','title','journal','date','year','first_author','doi','topics')}
        row['pmid']=pmid
        row['found_at']=rec.get('found_at') or today
        row['status']='queued'
        queue.setdefault('candidates',[]).append(row)
        have.add(pmid); added+=1
    queue['updated']=today
    return queue, added

def new_hits(hits, have):
    """hits: pmid -> [topic ids]. Drop anything already in the library or queue."""
    return {pmid:topics for pmid,topics in hits.items() if str(pmid) not in have}

def pull(days=None, fetch=None):
    """Run the pull. `fetch` is get() or a test double with the same signature."""
    days=int(os.environ['WEEKLY_DAYS']) if days is None and os.environ.get('WEEKLY_DAYS') else (7 if days is None else int(days))
    topics, species=load_queries()
    fetch=fetch or get
    hits={}
    for t in topics:
        term=f'({t["pubmed_query"]}) AND {species} AND hasabstract NOT (Comment[pt] OR Editorial[pt] OR Letter[pt] OR News[pt] OR "Published Erratum"[pt])'
        r=fetch('esearch.fcgi', db='pubmed', term=term, reldate=days, datetype='edat', retmax=500, retmode='json')
        for i in (r.get('esearchresult') or {}).get('idlist') or []:
            hits.setdefault(str(i),[]).append(t['id'])
        time.sleep(0.34 if fetch is get else 0)
    have=library_pmids()|queue_pmids()
    fresh=new_hits(hits, have)
    added_recs=[]
    if not fresh:
        q=load_queue(); q['updated']=time.strftime('%Y-%m-%d'); save_queue(q)
        return {'matched':len(hits),'already':len(hits),'added':0,'topics':len(topics)}
    ids=list(fresh)
    for k in range(0,len(ids),100):
        s=fetch('esummary.fcgi', db='pubmed', id=','.join(ids[k:k+100]), retmode='json').get('result') or {}
        for pmid in s.get('uids',[]):
            d=s[pmid]; pts=set(d.get('pubtype') or [])
            if pts & EXCLUDE_TYPES: continue
            doi=next((a['value'] for a in d.get('articleids') or [] if a.get('idtype')=='doi'),'')
            added_recs.append({
                'pmid':str(pmid),'title':(d.get('title') or '').rstrip('.'),
                'first_author':(d.get('authors') or [{}])[0].get('name',''),
                'year':(d.get('pubdate') or '')[:4],
                'date':(d.get('sortpubdate') or '')[:10].replace('/','-'),
                'journal':d.get('source') or '','doi':str(doi).lower(),
                'topics':sorted(set(fresh.get(str(pmid) or pmid) or [])),
            })
        time.sleep(0.34 if fetch is get else 0)
    q, n=merge_candidates(load_queue(), added_recs)
    save_queue(q)
    return {'matched':len(hits),'already':len(hits)-len(fresh),'added':n,'topics':len(topics)}

def main():
    if os.environ.get('WEEKLY_PULL')=='0':
        print('weekly pull skipped (WEEKLY_PULL=0)')
        return
    r=pull()
    print(f"weekly pull: {r['matched']} matched across {r['topics']} topic queries, {r['already']} already in library or queue, {r['added']} written to ingest_queue")

if __name__=='__main__':
    main()
