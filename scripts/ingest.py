"""Daily ingestion via NCBI E-utilities (esearch + esummary).

Query source: data/v5/pubmed_queries.json (installed from
extracts/pubmed_queries_2026-11-10.json). Each pubmed_query already includes
species, study-type, and exclusion terms — do not wrap it with the old
Cats/Dogs MeSH filter, hasabstract, or publication-type excludes.

New papers are written to data/papers/pmid-<PMID>.json with status '待处理'.
Existing files are never touched. Child-topic hits are also tagged with
parents that list them in inherits_children.

Env: NCBI_API_KEY (optional), NCBI_EMAIL (optional), INGEST_DAYS (default 2).
INGEST_DRY=1 prints per-query counts and writes nothing.
"""
import json, os, sys, time, urllib.parse, urllib.request

ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); OUT=os.path.join(ROOT,'data','papers')
QFILE=os.path.join(ROOT,'data','v5','pubmed_queries.json')
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
EXCLUDE_TYPES={'Comment','Editorial','Letter','News','Published Erratum','Retraction of Publication','Retracted Publication'}

_MONTH={'jan':1,'january':1,'feb':2,'february':2,'mar':3,'march':3,'apr':4,'april':4,
        'may':5,'jun':6,'june':6,'jul':7,'july':7,'aug':8,'august':8,'sep':9,'sept':9,
        'september':9,'oct':10,'october':10,'nov':11,'november':11,'dec':12,'december':12}

def _parse_pubmed_date_str(s):
    """Parse an esummary pubdate/epubdate string. Returns (iso, precision) or (None, None).
    Day is recorded only when the string itself includes a day."""
    s=(s or '').strip()
    if not s: return None, None
    iso=s.replace('/','-')
    if len(iso)>=10 and iso[4]=='-' and iso[7]=='-' and iso[:10].replace('-','').isdigit():
        return iso[:10], 'day'
    parts=s.replace(',', ' ').split()
    if not parts: return None, None
    y=parts[0][:4]
    if not (y.isdigit() and len(y)==4):
        return None, None
    if len(parts)==1:
        return y+'-01-01', 'year'
    mon=_MONTH.get(parts[1].lower()) or (int(parts[1]) if parts[1].isdigit() and 1<=int(parts[1])<=12 else None)
    if not mon:
        return y+'-01-01', 'year'
    if len(parts)>=3 and parts[2].isdigit():
        dd=int(parts[2])
        if 1<=dd<=31:
            return f'{y}-{mon:02d}-{dd:02d}', 'day'
    return f'{y}-{mon:02d}-01', 'month'

def parse_esummary_pub_date(d):
    """(iso, precision, source) from PubMed esummary PubDate (pubdate) and ArticleDate/EpubDate (epubdate).
    sortpubdate is only a fallback when both are missing; a first-of-month sortpubdate is not treated as a day
    when PubDate is month-only."""
    d=d or {}
    pub=_parse_pubmed_date_str(d.get('pubdate') or '')
    epub=_parse_pubmed_date_str(d.get('epubdate') or d.get('articleDate') or '')
    if pub[1]=='day':
        return pub[0], 'day', 'PubMed PubDate'
    if epub[1]=='day':
        return epub[0], 'day', 'PubMed ArticleDate/EpubDate'
    if pub[1]=='month':
        return pub[0], 'month', 'PubMed PubDate'
    if epub[1]=='month':
        return epub[0], 'month', 'PubMed ArticleDate/EpubDate'
    if pub[1]=='year':
        return pub[0], 'year', 'PubMed PubDate'
    if epub[1]=='year':
        return epub[0], 'year', 'PubMed ArticleDate/EpubDate'
    sort=(d.get('sortpubdate') or '').replace('/','-')
    if len(sort)>=10 and sort[:10].replace('-','').isdigit():
        iso=sort[:10]
        prec='month' if iso.endswith('-01') else 'day'
        return iso, prec, 'PubMed sortpubdate'
    return None, None, ''


def get(ep,**p):
    """POST to E-utilities so long pubmed_query strings are not truncated by URL length."""
    p.setdefault('tool','vetlit')
    if os.environ.get('NCBI_API_KEY'): p['api_key']=os.environ['NCBI_API_KEY']
    if os.environ.get('NCBI_EMAIL'): p['email']=os.environ['NCBI_EMAIL']
    url=BASE+ep
    body=urllib.parse.urlencode(p).encode()
    for t in range(4):
        try:
            req=urllib.request.Request(url,data=body,headers={'User-Agent':'vetlit-ingest','Content-Type':'application/x-www-form-urlencoded'})
            with urllib.request.urlopen(req,timeout=120) as r:
                return json.load(r)
        except Exception:
            if t==3: raise
            time.sleep(2*(t+1))

def load_queries():
    """Return the topics list from the live query file."""
    d=json.load(open(QFILE,encoding='utf-8'))
    return d.get('topics') or []

def query_term(t):
    """Use the stored pubmed_query as-is. Empty queries (e.g. saim) are skipped by callers."""
    return (t.get('pubmed_query') or '').strip()

def inherit_tags(topics, hits):
    """Add parent topic ids when a child listed in inherits_children is tagged."""
    child_to_parents={}
    for t in topics:
        for c in (t.get('inherits_children') or []) or []:
            child_to_parents.setdefault(str(c),[]).append(t['id'])
    out={}
    for pmid, tids in hits.items():
        extra=[]
        for tid in tids:
            extra += child_to_parents.get(str(tid)) or []
        out[pmid]=sorted(set(list(tids)+extra))
    return out

def species_of(title):
    t=title.lower(); s=[]
    if any(w in t for w in ['cat ','cats','feline','kitten']): s.append('猫')
    if any(w in t for w in ['dog','canine','puppy','puppies']): s.append('犬')
    return '/'.join(s) or '未核'

def existing_pmids():
    out=set()
    if not os.path.isdir(OUT): return out
    for f in os.listdir(OUT):
        if f.endswith('.json'):
            try: out.add(str(json.load(open(os.path.join(OUT,f),encoding='utf-8')).get('pmid') or ''))
            except Exception: pass
    return out

def search_topics(topics, days, fetch=None):
    """Run esearch for each topic with a pubmed_query. Returns (hits, counts).
    hits: pmid -> [topic ids]; counts: topic id -> esearch count (int)."""
    fetch=fetch or get
    hits={}; counts={}
    for t in topics:
        term=query_term(t)
        if not term: continue
        r=fetch('esearch.fcgi', db='pubmed', term=term, reldate=int(days), datetype='edat', retmax=500, retmode='json')
        er=r.get('esearchresult') or {}
        counts[t['id']]=int(er.get('count') or 0)
        for i in er.get('idlist') or []:
            hits.setdefault(str(i),[]).append(t['id'])
        if fetch is get: time.sleep(0.4)
    return inherit_tags(topics, hits), counts

def main(days=None, dry=None, fetch=None):
    days=int(os.environ.get('INGEST_DAYS','2') if days is None else days)
    dry=os.environ.get('INGEST_DRY')=='1' if dry is None else bool(dry)
    topics=load_queries()
    runnable=[t for t in topics if query_term(t)]
    hits, counts=search_topics(topics, days, fetch=fetch)
    have=existing_pmids()
    new=[i for i in hits if i not in have and not os.path.exists(os.path.join(OUT,f'pmid-{i}.json'))]
    for tid,n in counts.items():
        print(f'{tid}: {n} hits')
    print(f'ingest: {len(hits)} unique PMIDs across {len(runnable)} queries ({days}d edat), {len(hits)-len(new)} already present, {len(new)} new')
    if dry:
        print('ingest dry run: nothing written')
        return {'counts':counts,'unique':len(hits),'new':len(new),'already':len(hits)-len(new),'days':days,'written':0}
    added=0
    for k in range(0,len(new),100):
        s=(fetch or get)('esummary.fcgi', db='pubmed', id=','.join(new[k:k+100]), retmode='json')['result']
        for pmid in s.get('uids',[]):
            d=s[pmid]; pts=set(d.get('pubtype',[]))
            if pts & EXCLUDE_TYPES: continue
            doi=next((a['value'] for a in d.get('articleids',[]) if a.get('idtype')=='doi'),'')
            pmc=next((a['value'] for a in d.get('articleids',[]) if a.get('idtype')=='pmc'),'')
            iso,prec,src=parse_esummary_pub_date(d)
            rec={'id':f'pmid-{pmid}','pmid':str(pmid),'title':d.get('title','').rstrip('.'),'first_author':(d.get('authors') or [{}])[0].get('name',''),
                 'year':(iso or d.get('pubdate') or '')[:4],'date':iso or (d.get('sortpubdate') or '')[:10].replace('/','-'),
                 'pub_date':iso or '','pub_date_precision':prec or '','pub_date_source':src or '',
                 'journal':d.get('source',''),'doi':str(doi).lower(),
                 'pmcid':pmc,'species':species_of(d.get('title','')),'specialty':'未分类','topics':sorted(set(hits.get(str(pmid),[]))),'source':'PubMed (E-utilities)','oa':'是' if pmc else '未核',
                 'doc_type':'待定','publication_types':sorted(pts),'sample_size_analysed':'未核','multicenter':'未核','funding':'未核','verified':'partial',
                 'status':'待处理','provenance':['ingest'],'ingested_at':time.strftime('%Y-%m-%d')}
            f=os.path.join(OUT,rec['id']+'.json')
            if os.path.exists(f): continue
            json.dump(rec,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=2); added+=1
        if (fetch or get) is get: time.sleep(0.4)
    print(f'ingest: {added} new written as 待处理')
    return {'counts':counts,'unique':len(hits),'new':len(new),'already':len(hits)-len(new),'days':days,'written':added}

if __name__=='__main__':
    main()
