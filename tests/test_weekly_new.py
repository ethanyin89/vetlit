"""本期新增 homepage block + weekly PubMed queue (candidates never shown to readers)."""
import os, sys, json, glob, datetime, re
from pathlib import Path
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
os.environ['WEEKLY_PULL']='0'
import build_preview as B
import scripts.weekly_pubmed_pull as W

# config exists and reuses Daily ingest queries for named topics; general is the live ingest-v2 query, unwrapped
Q=json.load(open('data/v5/topic_queries.json',encoding='utf-8'))
assert any(t.get('pubmed_query') and t['id']=='ckd' for t in Q['topics'])
assert any(t['id']=='canine_atopic_dermatitis' and t.get('pubmed_query') for t in Q['topics'])
topics_src={t['id']:t.get('pubmed_query') for t in json.load(open('data/topics.json',encoding='utf-8'))['topics']}
for t in Q['topics']:
    if t['id'] in topics_src and topics_src[t['id']]:
        assert t['pubmed_query']==topics_src[t['id']], t['id']
assert Q.get('general',{}).get('pubmed_query')
assert 'Dogs' in Q['general']['pubmed_query']
assert W.general_query()==Q['general']['pubmed_query'].strip()

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
# stored day precision is kept even when the calendar day is the 1st; month-only stays month-only
disp,prec,ear=B.parse_pub_date({'pub_date':'2026-11-01','pub_date_precision':'day'})
assert prec=='day' and disp=='2026年11月1日'
disp,prec,ear=B.parse_pub_date({'pub_date':'2026-11-01','pub_date_precision':'month'})
assert prec=='month' and disp=='2026年11月'

# this issue: no approved 本期新增 papers (42977701 is in the infectious library, not this list)
today=datetime.date(2026,11,10)
assert B.weekly_new_entries(today)==[]
assert [t['id'] for t in B.new_topics_this_issue(today)]==['canine_atopic_dermatitis']

# homepage: 本期新增 at the top shows 本周无新增; keep 本周新增专题：犬特应性皮炎; 最重要 stays below
h=open('dist/index.html',encoding='utf-8').read()
assert 'id="weekly-new"' in h and '本期新增' in h
assert h.find('id="weekly-new"') < h.find('最重要')
block=h.split('id="weekly-new"',1)[1].split('</section>',1)[0]
assert '本周新增专题' in block and '犬特应性皮炎' in block
assert 'topics/canine_atopic_dermatitis/' in block
assert '本周无新增' in block
assert '42977701' not in block and 'papers/pmid-42977701/' not in block
# never ingest auto-tags or example data on the homepage block
assert '肥胖' not in block and '猫传染性腹膜炎' not in block
assert 'h3' not in block
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

# 42977701 belongs on the infectious topic library page, not obesity
inf=open('dist/topics/infectious/index.html',encoding='utf-8').read()
assert '42977701' in inf
assert 'obesity' not in open('dist/topics/obesity/index.html',encoding='utf-8').read() or '42977701' not in open('dist/topics/obesity/index.html',encoding='utf-8').read()

# 待处理 ingest papers do not exist under dist/papers; 42977701 is a library paper (已收录)
pending=set()
for fp in Path('data/papers').glob('pmid-*.json'):
    rec=json.load(open(fp,encoding='utf-8'))
    if rec.get('status')=='待处理':
        pending.add(str(rec['pmid']))
        d=Path('dist/papers')/f'pmid-{rec["pmid"]}'
        assert not d.exists(), rec['pmid']
assert '42977701' not in pending
assert (Path('dist/papers')/'pmid-42977701'/'index.html').exists()
# papers.json has no 待处理 rows or the two known mis-tagged ingest ids
if Path('dist/papers.json').exists():
    rows=json.load(open('dist/papers.json',encoding='utf-8'))
    for r in rows:
        assert r.get('status')!='待处理', r.get('pmid')
        if str(r.get('pmid')) in ('43000584','42983423'):
            raise AssertionError('mis-tagged ingest paper in papers.json: '+str(r.get('pmid')))
        # no _internal keys on reader data
        assert not any(str(k).startswith('_internal') for k in r), r.get('pmid')

# 42977701 reader page: rated 低 with speed-read; no 待处理; no obesity auto-tag; no 起评 / rule ids
ph=open('dist/papers/pmid-42977701/index.html',encoding='utf-8').read()
assert '证据确定性：低' in ph
assert '暂未评级' not in ph
assert '待处理' not in ph
assert '肥胖与体况' not in ph and 'topics/obesity/' not in ph
assert 'topics/infectious/' in ph or '感染性疾病' in ph
assert '数据来源 ingest' not in ph and 'provisional' not in ph and '暂定' not in ph
assert '起评' not in ph and '起点为' not in ph
assert 'R-start-prognosis' not in ph and 'R-rob-assessed' not in ph
assert '_internal' not in ph and 'weekly_new_note' not in ph
assert 'pick_reason' not in ph
assert '从‘高’起评' not in ph and '从“高”起评' not in ph
# speed-read body is present (clinical conclusion / results), not the gated 起评 certainty narrative
assert '8.8%' in ph and ('手术部位感染' in ph or '乳腺切除' in ph)

# a date after this issue falls into the next Mon–Sun window with no approved additions
st,en,_=B.issue_bounds(datetime.date(2026,11,16))
assert st=='2026-11-16' and en=='2026-11-22'
assert B.weekly_new_entries(datetime.date(2026,11,16))==[]
assert B.new_topics_this_issue(datetime.date(2026,11,16))==[]

# PubMed PubDate / ArticleDate parsing at ingest (day kept only when PubMed has a day)
import scripts.ingest as IN
iso,prec,src=IN.parse_esummary_pub_date({'pubdate':'2026 Nov 15','epubdate':'','sortpubdate':'2026/11/15 00:00'})
assert iso=='2026-11-15' and prec=='day' and 'PubDate' in src
iso,prec,src=IN.parse_esummary_pub_date({'pubdate':'2026 Nov','epubdate':'','sortpubdate':'2026/11/01 00:00'})
assert iso=='2026-11-01' and prec=='month' and 'PubDate' in src  # month-only stays month-only
iso,prec,src=IN.parse_esummary_pub_date({'pubdate':'2026 Nov','epubdate':'2026 Nov 03','sortpubdate':'2026/11/01 00:00'})
assert iso=='2026-11-03' and prec=='day' and 'ArticleDate' in src
iso,prec,src=IN.parse_esummary_pub_date({'pubdate':'','epubdate':'','sortpubdate':'2026/11/01 00:00'})
assert iso=='2026-11-01' and prec=='month'

# 42977701 as stored: title_zh == one_line_conclusion_zh, no clinical_meaning → overlap, skip
libp=B.get('pmid-42977701') or B.get('42977701')
assert libp.get('title_zh') and libp.get('one_line_conclusion_zh')
assert libp.get('title_zh')==libp.get('one_line_conclusion_zh')
assert not libp.get('clinical_meaning')
assert B.weekly_title_overlaps_conclusion(libp['title_zh'], B.summ(libp))
assert not B.weekly_zh_ready(libp)
# 42977701 PubDate is month-only
disp,prec,ear=B.parse_pub_date(libp)
assert prec=='month' and disp=='2026年11月'

# overlap helpers
assert B.weekly_title_overlaps_conclusion('犬猫乳腺切除术后 8.8% 感染','犬猫乳腺切除术后 8.8% 感染')
assert B.weekly_title_overlaps_conclusion('犬猫乳腺切除术后 8.8% 感染','犬猫乳腺切除术后 8.8% 感染：手术时间长、术中低体温')
assert B.weekly_title_overlaps_conclusion('控制手术时长、防止术中低体温','控制手术时长，防止术中低体温。')  # high similarity
assert not B.weekly_title_overlaps_conclusion('犬猫乳腺切除术后 8.8% 感染','控制手术时长、防止术中低体温；感染后先培养再选药。')

# 本期新增 cards: title_zh + summ() (clinical_meaning when conclusion would duplicate the title)
import io, contextlib, copy
good_p=copy.deepcopy(libp)
good_p['clinical_meaning']='控制手术时长、防止术中低体温；感染后先培养再选药。'
assert B.weekly_zh_ready(good_p)
assert B.summ(good_p)==good_p['clinical_meaning']
html=B.weekly_card(good_p,'2026年11月','感染性疾病','topics/infectious/','')
assert '<article class="card">' in html
assert '<h3 class="ct">' in html and '犬猫乳腺切除术后' in html
assert '<p class="en" lang="en">' in html and good_p['title'][:40] in html
assert '<p class="bl">' in html and '控制手术时长、防止术中低体温' in html
assert good_p['title_zh'] not in html.split('<p class="bl">',1)[1]  # conclusion is not the title
# meta reuses 最重要 cmeta: journal · study type · n · species, plus topic and certainty
assert 'Vet Med Sci' in html and '队列研究' in html and '615 只' in html and '犬/猫' in html
assert '感染性疾病' in html and 'topics/infectious/' in html
assert '证据确定性：低' in html
assert '2026年11月' in html
assert '速读 →' in html
assert 'class="why"' not in html and 'pick_reason' not in html

bare={'pmid':'000111','sid':'pmid-000111','title':'English-only weekly paper','pub_date':'2026-10-01'}
assert not B.weekly_zh_ready(bare)
item=('2026-10-01','2026年10月1日',bare,'','其他','')
overlap=('2026-11-01','2026年11月',libp,'infectious','感染性疾病','topics/infectious/')
good=('2026-11-01','2026年11月',good_p,'infectious','感染性疾病','topics/infectious/')
err=io.StringIO()
with contextlib.redirect_stderr(err):
    vis=B.weekly_visible_entries([good,item,overlap])
assert vis==[good]
assert '000111' in err.getvalue() and 'missing Chinese title or one-line conclusion' in err.getvalue()
assert '42977701' in err.getvalue() and 'conclusion overlaps title' in err.getvalue()
old_entries=B.weekly_new_entries
try:
    B.weekly_new_entries=lambda today=None: [overlap]
    err=io.StringIO()
    with contextlib.redirect_stderr(err):
        block=B.weekly_new_block()
    assert '本周无新增' in block
    assert '<article class="card">' not in block
    assert 'conclusion overlaps title' in err.getvalue()
    B.weekly_new_entries=lambda today=None: [good]
    block=B.weekly_new_block()
    assert '本周无新增' not in block
    assert '<article class="card">' in block
    assert '控制手术时长、防止术中低体温' in block
    assert 'Vet Med Sci' in block and '615 只' in block and '证据确定性：低' in block
    assert '速读 →' in block
finally:
    B.weekly_new_entries=old_entries

print('weekly new / queue tests OK')
