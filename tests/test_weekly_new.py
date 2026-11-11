"""本期新增 homepage block + weekly PubMed queue (candidates never shown to readers)."""
import os, sys, json, glob, datetime, re
from pathlib import Path
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
assert '42977701' in lib

# merge into queue does not repeat library or already-queued ids
q={'candidates':[{'pmid':'111','status':'queued'}]}
q,n=W.merge_candidates(q,[{'pmid':'111','title':'dup'},{'pmid':'222','title':'new'}], today='2026-11-10')
assert n==1 and [c['pmid'] for c in q['candidates']]==['111','222']
assert W.new_hits({'43000584':['infectious'],'99999999':['ckd']}, lib|W.queue_pmids(q))=={'99999999':['ckd']}

# publication-date window: rolling 3 months; YYYY-MM-01 treated as month precision (conservative)
assert B.pub_window_start(datetime.date(2026,11,10))==datetime.date(2026,8,10)
disp,prec,ear=B.parse_pub_date({'pub_date':'2026-09-28'})
assert prec=='day' and ear=='2026-09-28' and disp=='2026年9月28日'
disp,prec,ear=B.parse_pub_date({'date':'2026-11-01'})
assert prec=='month' and ear=='2026-11-01' and disp=='2026年11月'
assert B.parse_pub_date({})==(None,None,None)

# this issue: only 42977701 is approved; pub date 2026-11 is within 3 months; screening topic is 其他 (not ingest obesity/infectious)
today=datetime.date(2026,11,10)
ents=B.weekly_new_entries(today)
assert [p['pmid'] for *_,p,tid,label,href in [(e[0],e[1],e[2],e[3],e[4],e[5]) for e in ents]]==['42977701'] or [e[2]['pmid'] for e in ents]==['42977701']
assert ents[0][1]=='2026年11月' and ents[0][4]=='其他' and ents[0][5]==''
assert [t['id'] for t in B.new_topics_this_issue(today)]==['canine_atopic_dermatitis']

# homepage: 本期新增 at the top, flat list (not grouped by topic), 最重要 stays below
h=open('dist/index.html',encoding='utf-8').read()
assert 'id="weekly-new"' in h and '本期新增' in h
assert h.find('id="weekly-new"') < h.find('最重要')
block=h.split('id="weekly-new"',1)[1].split('</section>',1)[0]
assert '本周新增专题' in block and '犬特应性皮炎' in block
assert 'topics/canine_atopic_dermatitis/' in block
assert 'papers/pmid-42977701/' in block
assert '2026年11月' in block and '其他' in block
# never ingest auto-tags on the homepage block
assert '肥胖' not in block and '猫传染性腹膜炎' not in block
assert 'h3' not in block  # flat list, not per-topic groups
assert '本周无新增' not in block
assert 'class="card"' not in block
# unapproved / other-issue papers stay out
assert '42800045' not in block and '42805756' not in block and '37167252' not in block
assert '2026-11-09' not in block and '2026-11-10' not in block
# unscreened ingest / queue never appear
assert '最新抓取' not in h
assert '43000584' not in h and '42983423' not in h
assert 'ingest_queue' not in h and 'weekly_new_approved' not in h
for f in glob.glob('dist/topics/*/index.html'):
    s=open(f,encoding='utf-8').read()
    assert '最新抓取' not in s, f
    assert '43000584' not in s and '42983423' not in s, f
    # approved 42977701 is 其他 — not listed on infectious/obesity topic pages
    if f.endswith('/infectious/index.html') or f.endswith('/obesity/index.html'):
        assert '42977701' not in s, f

# 待处理 ingest papers (except the approved 42977701 reader page we write) do not exist under dist/papers
pending=set()
for fp in Path('data/papers').glob('pmid-*.json'):
    rec=json.load(open(fp,encoding='utf-8'))
    if rec.get('status')=='待处理':
        pending.add(str(rec['pmid']))
for pm in pending:
    d=Path('dist/papers')/f'pmid-{pm}'
    if pm=='42977701':
        assert d.exists() and (d/'index.html').exists()
        continue
    assert not d.exists(), pm
# papers.json has no 待处理 rows or the two known mis-tagged ingest ids (except 42977701 if present without ingest tags)
if Path('dist/papers.json').exists():
    rows=json.load(open('dist/papers.json',encoding='utf-8'))
    for r in rows:
        assert r.get('status')!='待处理', r.get('pmid')
        if str(r.get('pmid')) in ('43000584','42983423'):
            raise AssertionError('mis-tagged ingest paper in papers.json: '+str(r.get('pmid')))

# 42977701 reader page: 暂未评级; no 待处理; no ingest auto-tags
ph=open('dist/papers/pmid-42977701/index.html',encoding='utf-8').read()
assert '暂未评级' in ph
assert '待处理' not in ph
assert '肥胖与体况' not in ph and '猫传染性腹膜炎' not in ph
assert 'topics/obesity/' not in ph and 'topics/infectious/' not in ph
assert '数据来源 ingest' not in ph and 'provisional' not in ph and '暂定' not in ph

# a date after this issue falls into the next Mon–Sun window with no approved additions
st,en,_=B.issue_bounds(datetime.date(2026,11,16))
assert st=='2026-11-16' and en=='2026-11-22'
assert B.weekly_new_entries(datetime.date(2026,11,16))==[]
assert B.new_topics_this_issue(datetime.date(2026,11,16))==[]

print('weekly new / queue tests OK')
