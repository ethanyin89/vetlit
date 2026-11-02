"""Daily ingestion via NCBI E-utilities (esearch + esummary). Rule-based filters only; no grading.
New papers are written to data/papers/pmid-<PMID>.json with status '待处理'. Existing files are never touched.
Env: NCBI_API_KEY (optional), NCBI_EMAIL (optional), INGEST_DAYS (default 2)."""
import json, os, sys, time, urllib.parse, urllib.request
ROOT=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); OUT=os.path.join(ROOT,'data','papers')
BASE='https://eutils.ncbi.nlm.nih.gov/entrez/eutils/'
JOURNALS=['J Vet Intern Med','J Feline Med Surg','J Am Vet Med Assoc','Vet J','J Small Anim Pract','Front Vet Sci','Vet Rec','J Vet Cardiol','Am J Vet Res','Vet Clin Pathol','J Vet Emerg Crit Care (San Antonio)','Vet Radiol Ultrasound','Vet Anaesth Analg','J Vet Med Sci','Animals (Basel)','Sci Rep']
SPECIES='("Cats"[MeSH Terms] OR "Dogs"[MeSH Terms] OR feline[tiab] OR canine[tiab] OR cats[tiab] OR dogs[tiab])'
EXCLUDE_TYPES={'Comment','Editorial','Letter','News','Published Erratum','Retraction of Publication','Retracted Publication'}
def get(ep,**p):
    p.setdefault('tool','vetlit'); 
    if os.environ.get('NCBI_API_KEY'): p['api_key']=os.environ['NCBI_API_KEY']
    if os.environ.get('NCBI_EMAIL'): p['email']=os.environ['NCBI_EMAIL']
    url=BASE+ep+'?'+urllib.parse.urlencode(p)
    for t in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'vetlit-ingest'}),timeout=60) as r: return json.load(r)
        except Exception as e:
            if t==3: raise
            time.sleep(2*(t+1))
def species_of(title):
    t=title.lower(); s=[]
    if any(w in t for w in ['cat ','cats','feline','kitten']): s.append('猫')
    if any(w in t for w in ['dog','canine','puppy','puppies']): s.append('犬')
    return '/'.join(s) or '未核'
def main():
    days=int(os.environ.get('INGEST_DAYS','2'))
    jq=' OR '.join(f'"{j}"[ta]' for j in JOURNALS)
    term=f'({jq}) AND {SPECIES} AND hasabstract NOT (Comment[pt] OR Editorial[pt] OR Letter[pt] OR News[pt] OR "Published Erratum"[pt])'
    r=get('esearch.fcgi',db='pubmed',term=term,reldate=days,datetype='edat',retmax=500,retmode='json')
    ids=r['esearchresult']['idlist']; print(f'esearch: {r["esearchresult"]["count"]} hits in last {days} day(s)')
    new=[i for i in ids if not os.path.exists(os.path.join(OUT,f'pmid-{i}.json'))]
    added=0
    for k in range(0,len(new),100):
        s=get('esummary.fcgi',db='pubmed',id=','.join(new[k:k+100]),retmode='json')['result']
        for pmid in s.get('uids',[]):
            d=s[pmid]; pts=set(d.get('pubtype',[]))
            if pts & EXCLUDE_TYPES: continue
            doi=next((a['value'] for a in d.get('articleids',[]) if a['idtype']=='doi'),'')
            pmc=next((a['value'] for a in d.get('articleids',[]) if a['idtype']=='pmc'),'')
            rec={'id':f'pmid-{pmid}','pmid':pmid,'title':d.get('title','').rstrip('.'),'first_author':(d.get('authors') or [{}])[0].get('name',''),
                 'year':(d.get('pubdate') or '')[:4],'date':d.get('sortpubdate','')[:10].replace('/','-'),'journal':d.get('source',''),'doi':doi.lower(),
                 'pmcid':pmc,'species':species_of(d.get('title','')),'specialty':'未分类','source':'PubMed (E-utilities)','oa':'是' if pmc else '未核',
                 'doc_type':'待定','publication_types':sorted(pts),'sample_size_analysed':'未核','multicenter':'未核','funding':'未核','verified':'partial',
                 'status':'待处理','provenance':['ingest'],'ingested_at':time.strftime('%Y-%m-%d')}
            json.dump(rec,open(os.path.join(OUT,rec['id']+'.json'),'w'),ensure_ascii=False,indent=2); added+=1
        time.sleep(0.4)
    print(f'ingest: {len(ids)} matched, {len(ids)-len(new)} already present, {added} new written as 待处理')
if __name__=='__main__': main()
