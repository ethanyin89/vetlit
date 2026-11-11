"""本期新增 homepage block + weekly PubMed queue (candidates never shown to readers)."""
import os, sys, json, glob, datetime
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
os.environ['WEEKLY_PULL']='0'
import build_preview as B
import scripts.weekly_pubmed_pull as W

# config exists and reuses Daily ingest queries
Q=json.load(open('data/v5/topic_queries.json',encoding='utf-8'))
assert any(t.get('pubmed_query') and t['id']=='ckd' for t in Q['topics'])
assert any(t['id']=='canine_atopic_dermatitis' and t.get('pubmed_query') for t in Q['topics'])
topics_src={t['id']:t.get('pubmed_query') for t in json.load(open('data/topics.json',encoding='utf-8'))['topics']}
for t in Q['topics']:
    if t['id'] in topics_src and topics_src[t['id']]:
        assert t['pubmed_query']==topics_src[t['id']], t['id']

# library dedupe covers seed + data/papers (待处理 ingest too)
lib=W.library_pmids()
assert '37167252' in lib and '42805756' in lib
assert '43000584' in lib  # 2026-11-09 ingest, 待处理, not a reader paper

# merge into queue does not repeat library or already-queued ids
q={'candidates':[{'pmid':'111','status':'queued'}]}
q,n=W.merge_candidates(q,[{'pmid':'111','title':'dup'},{'pmid':'222','title':'new'}], today='2026-11-10')
assert n==1 and [c['pmid'] for c in q['candidates']]==['111','222']
assert W.new_hits({'43000584':['infectious'],'99999999':['ckd']}, lib|W.queue_pmids(q))=={'99999999':['ckd']}

# homepage: 本期新增 at the top, 最重要 stays below as the stable list
h=open('dist/index.html',encoding='utf-8').read()
assert 'id="weekly-new"' in h and '本期新增' in h
assert h.find('id="weekly-new"') < h.find('最重要')
block=h.split('id="weekly-new"',1)[1].split('最重要',1)[0]
assert '犬特应性皮炎' in block and '甲状腺功能亢进' in block
assert '2026-11-10' in block and '2026-11-09' in block
assert 'papers/pmid-42805756/' in block and 'papers/pmid-37167252/' in block
assert '其余专题本周无新增' in block
# compact: not a full card in the issue block
assert 'class="card"' not in block
# unscreened ingest / queue never appear as 本期新增 (or as 最新抓取)
assert '最新抓取' not in h
assert '43000584' not in h
assert 'ingest_queue' not in h and 'weekly_new_approved' not in h
# topic pages also dropped 最新抓取
for f in glob.glob('dist/topics/*/index.html'):
    assert '最新抓取' not in open(f,encoding='utf-8').read(), f
# a library paper added before this issue is omitted
assert 'pmid-42693626/' not in block

# a date after this issue falls into the next Mon–Sun window with no approved additions
st,en,_=B.issue_bounds(datetime.date(2026,11,16))
assert st=='2026-11-16' and en=='2026-11-22'
assert B.weekly_new_entries(datetime.date(2026,11,16))==[]

print('weekly new / queue tests OK')
