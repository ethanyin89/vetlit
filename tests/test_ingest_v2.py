"""Ingest v2: queries come from data/v5/pubmed_queries.json and are not wrapped with the old MeSH species filter."""
import os, sys, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
import scripts.ingest as I

assert os.path.isfile(I.QFILE) and I.QFILE.endswith('data/v5/pubmed_queries.json')
topics=I.load_queries()
ids=[t['id'] for t in topics]
assert '_general' in ids and 'oncology' in ids and 'cognition' in ids
# saim is a classification layer with no query of its own
saim=next(t for t in topics if t['id']=='saim')
assert not I.query_term(saim) and 'infectious' in (saim.get('inherits_children') or [])
# queries already include species; ingest must use them as-is
onco=next(t for t in topics if t['id']=='oncology')
q=I.query_term(onco)
assert 'Dogs' in q and 'oncolog' in q.lower() or 'neoplas' in q.lower() or 'tumour' in q.lower() or 'tumor' in q.lower() or 'cancer' in q.lower()
# wrapper must not be applied
assert I.query_term(onco)==onco['pubmed_query'].strip()
# reader-visibility flag: oncology is closed until it has rated papers
assert onco.get('reader_page_enabled') is False
# inherits_children tags a parent when a child hits
hits=I.inherit_tags(topics, {'1':['infectious'], '2':['oncology']})
assert 'saim' in hits['1'] and 'infectious' in hits['1']
assert hits['2']==['oncology']
# source file itself is not wrapped by the old SPECIES constant
src=open('scripts/ingest.py',encoding='utf-8').read()
assert 'AND {SPECIES}' not in src and 'AND SPECIES' not in src

# oncology topic page is not emitted and not linked when it has no library papers
import build as B
ps=B.load()
onco_t=next(t for t in B.TOPICS if t['id']=='oncology')
assert (B._QTOPICS.get('oncology') or {}).get('reader_page_enabled') is False
assert B.topic_visible(onco_t, ps) is False
assert 'topics/oncology' not in B.topics_index(ps)
# a library topic stays visible
ckd=next(t for t in B.TOPICS if t['id']=='ckd')
assert B.topic_visible(ckd, ps) is True

# after a live build, dist must not contain an oncology reader page
if os.path.isdir('dist/topics'):
    assert not os.path.exists('dist/topics/oncology/index.html')
    for root,dirs,files in os.walk('dist'):
        for fn in files:
            if not fn.endswith('.html'): continue
            h=open(os.path.join(root,fn),encoding='utf-8').read()
            if 'topics/oncology' in h and os.path.relpath(os.path.join(root,fn),'dist')!='topics/oncology/index.html':
                # allow mentions in methods/data dumps? reader nav should not link it
                if 'href="topics/oncology' in h or "href='topics/oncology" in h or 'href="../oncology' in h or 'href="oncology/' in h:
                    raise AssertionError('oncology nav link in '+os.path.join(root,fn))

print('ingest v2 tests OK')
