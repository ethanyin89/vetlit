"""Weekly PubMed pull per topic for deep extract screening.

Reads search strings from data/v5/topic_queries.json (placeholders copied from
data/topics.json until deep extract writes them and Vibe reviews). Dedupes
against the reader library (data/v5/seed_library_v6.json and data/papers) and
the existing screening queue. New hits are appended to data/v5/ingest_queue.json.

Candidates are not written to data/papers and must not be shown to readers until
they are screened, written up, and listed in data/v5/weekly_new_approved.json.

Topic queries historically reused Daily ingest wrapping. The general weekly
search reads topic_queries.json "general" and uses that pubmed_query as-is
(no MeSH species wrapper). WEEKLY_GENERAL=1 WEEKLY_DRY=1 runs only that path.

Env: NCBI_API_KEY (optional), NCBI_EMAIL (optional), WEEKLY_DAYS (default 7).
Set WEEKLY_PULL=0 to skip the network call (used by tests).
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
if ROOT not in sys.path: sys.path.insert(0, ROOT)
from scripts.ingest import parse_esummary_pub_date
def _pub_date_fields(d):
    iso,prec,src=parse_esummary_pub_date(d)
    return {'year':(iso or d.get('pubdate') or '')[:4],'date':iso or '','pub_date':iso or '','pub_date_precision':prec or '','pub_date_source':src or ''}
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
        row={k:rec[k] for k in rec if k in ('pmid','title','journal','date','year','pub_date','pub_date_precision','pub_date_source','first_author','doi','topics')}
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
            rec={'pmid':str(pmid),'title':(d.get('title') or '').rstrip('.'),
                'first_author':(d.get('authors') or [{}])[0].get('name',''),
                'journal':d.get('source') or '','doi':str(doi).lower(),
                'topics':sorted(set(fresh.get(str(pmid) or pmid) or []))}
            rec.update(_pub_date_fields(d)); added_recs.append(rec)
        time.sleep(0.34 if fetch is get else 0)
    q, n=merge_candidates(load_queue(), added_recs)
    save_queue(q)
    return {'matched':len(hits),'already':len(hits)-len(fresh),'added':n,'topics':len(topics)}


def general_query():
    """Live general weekly search string from topic_queries.json, used as-is (no MeSH wrapper)."""
    d=json.load(open(QFILE,encoding='utf-8'))
    g=d.get('general') or {}
    return (g.get('pubmed_query') or '').strip()

def post(ep, **p):
    """POST to E-utilities so the long general query is not truncated by URL length."""
    p.setdefault('tool','vetlit')
    if os.environ.get('NCBI_API_KEY'): p['api_key']=os.environ['NCBI_API_KEY']
    if os.environ.get('NCBI_EMAIL'): p['email']=os.environ['NCBI_EMAIL']
    body=urllib.parse.urlencode(p).encode()
    url=BASE+ep
    for t in range(4):
        try:
            req=urllib.request.Request(url,data=body,headers={'User-Agent':'vetlit-weekly-pull','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req,timeout=120) as r:
                return json.load(r)
        except Exception:
            if t==3: raise
            time.sleep(2*(t+1))

def pull_general(days=7, dry=True, fetch=None):
    """Run the general weekly query as-is. Dry run prints counts and writes nothing to the queue."""
    days=int(days)
    term=general_query()
    if not term:
        raise SystemExit('data/v5/topic_queries.json is missing a general.pubmed_query')
    fetch=fetch or post
    r=fetch('esearch.fcgi', db='pubmed', term=term, reldate=days, datetype='edat', retmax=500, retmode='json')
    er=r.get('esearchresult') or {}
    count=int(er.get('count') or 0)
    ids=[str(i) for i in (er.get('idlist') or [])]
    have=library_pmids()|queue_pmids()
    new=[i for i in ids if i not in have]
    out={'days':days,'count':count,'returned':len(ids),'already':len(ids)-len(new),'new':len(new),'ids':ids,'new_ids':new}
    # optional titles for a short sample
    sample_ids=ids[:8]
    out['sample']=[]
    if sample_ids:
        s=fetch('esummary.fcgi', db='pubmed', id=','.join(sample_ids), retmode='json').get('result') or {}
        for pmid in s.get('uids',[]) or sample_ids:
            d=s.get(pmid) or {}
            srec={'pmid':str(pmid),'title':(d.get('title') or '').rstrip('.'),'journal':d.get('source') or ''}; srec.update(_pub_date_fields(d)); out['sample'].append(srec)
    if dry:
        print(f"weekly general dry {days}d: esearch count={count}, returned={len(ids)}, already={out['already']}, new={len(new)}")
        for s in out['sample']:
            print(f"  {s['pmid']} {s['date']} {s['journal']}: {s['title']}")
        return out
    # write only new to queue
    recs=[{'pmid':s['pmid'],'title':s['title'],'date':s['date'],'journal':s['journal'],'topics':['general']} for s in out['sample'] if s['pmid'] in new]
    # if more new than sample, fetch remaining summaries
    rest=[i for i in new if i not in {s['pmid'] for s in recs}]
    for k in range(0,len(rest),100):
        s=fetch('esummary.fcgi', db='pubmed', id=','.join(rest[k:k+100]), retmode='json').get('result') or {}
        for pmid in s.get('uids',[]):
            d=s[pmid]
            rec={'pmid':str(pmid),'title':(d.get('title') or '').rstrip('.'),'journal':d.get('source') or '','topics':['general']}; rec.update(_pub_date_fields(d)); recs.append(rec)
        time.sleep(0.34 if fetch is post else 0)
    q,n=merge_candidates(load_queue(), recs)
    save_queue(q)
    out['added']=n
    print(f"weekly general {days}d: count={count}, added {n} to ingest_queue")
    return out

def main():
    if os.environ.get('WEEKLY_PULL')=='0':
        print('weekly pull skipped (WEEKLY_PULL=0)')
        return
    if os.environ.get('WEEKLY_GENERAL')=='1':
        days=int(os.environ.get('WEEKLY_DAYS') or '7')
        dry=os.environ.get('WEEKLY_DRY','1')!='0'
        pull_general(days=days, dry=dry)
        return
    r=pull()
    print(f"weekly pull: {r['matched']} matched across {r['topics']} topic queries, {r['already']} already in library or queue, {r['added']} written to ingest_queue")

if __name__=='__main__':
    main()
