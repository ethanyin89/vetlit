# 最重要 and 最新 never overlap (home blocks + every topic page); no weak 'why' line without pick_reason_zh
import re,glob,os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
ids=lambda x:re.findall(r'papers/pmid-(\d+)/"',x)
def chk(body,where):
    if '<h4 class="tb">最新</h4>' not in body: return 0
    a,b=body.split('<h4 class="tb">最新</h4>',1); b=b.split('<h2',1)[0]
    a=a.split('<h4 class="tb">最重要</h4>')[-1]
    assert not set(ids(a))&set(ids(b)), (where,set(ids(a))&set(ids(b)))
    assert len(set(ids(b)))<=3; return 1
s=open('dist/index.html',encoding='utf-8').read(); n=0
for m in re.finditer(r'<section class="tp">(.*?)</section>',s,re.S): n+=chk(m.group(1),'home')
for f in glob.glob('dist/topics/*/index.html'): n+=chk(open(f,encoding='utf-8').read(),f)
assert n>10, n
for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'):
    assert '近 5 年' not in open(f,encoding='utf-8').read(), f
print(f'dedupe tests OK ({n} blocks)')
# empty 最新 hidden entirely; short lists show only real cards
for tid in ('cognitive_dysfunction','hyperadrenocorticism','hypertension','neurology'):
    t=open(f'dist/topics/{tid}/index.html',encoding='utf-8').read()
    assert '最重要' in t and '<h4 class="tb">最新</h4>' not in t, tid
for tid in ('diet_dcm','mmvd','epidemiology','obesity'):
    b=open(f'dist/topics/{tid}/index.html',encoding='utf-8').read().split('<h4 class="tb">最新</h4>',1)[1].split('<h2',1)[0]
    n=b.count('<article class="card">'); assert 1<=n<3, (tid,n)
    assert n==len(set(ids(b))) and '暂无' not in b, tid
# pick_reason: rendered for Vibe-approved entries (approval file), per topic+list; stripped clause for 30548336
import json
PR=json.load(open('data/v5/extras/pick_reason.json',encoding='utf-8'))
A=json.load(open('data/v5/extras/pick_reason_approval.json',encoding='utf-8'))
allhtml=''.join(open(f,encoding='utf-8').read() for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'))
# 30548336: full approved reason in obesity (最重要), sample-size-only reason in nutrition (最新)
ob=open('dist/topics/obesity/index.html',encoding='utf-8').read()
c=[c for c in re.findall(r'<article class="card">.*?</article>',ob,re.S) if 'pmid-30548336/' in c][0]
assert '<p class="why">' not in c, c
assert '回顾性队列' in c and '原文自称' not in c, c
if A.get('approved_by')=='Vibe':
    ob=open('dist/topics/obesity/index.html',encoding='utf-8').read()
    # every shown 'why' text is a (possibly stripped) approved reason
    ok={e['pick_reason_zh'] for k,v in PR.items() if k!='_meta' for e in v if e.get('pick_reason_zh')}
    shown=set(re.findall(r'<p class="why">([^<]*)</p>',allhtml)); assert shown, 'nothing rendered'
    assert all(any(x==o or x in o for o in ok) for x in shown), shown-ok
    assert 'pmid-' in allhtml and 'class="why"></p>' not in allhtml
else:
    assert 'class="why"' not in allhtml
print('empty/short 最新 + pick_reason tests OK')

# 最新 = within rolling 5 years of build date only; rules/ranking pages and links gone
import datetime,sys; sys.path.insert(0,'.')
import build_preview as BP
assert BP.newest_cutoff(datetime.date(2026,11,4))=='2021-11-04'
assert BP.newest_cutoff(datetime.date(2028,2,29))=='2023-02-28'
cut=BP.newest_cutoff()
for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'):
    s=open(f,encoding='utf-8').read()
    for blk in s.split('<h4 class="tb">最新</h4>')[1:]:
        if not BP.NEWEST_5Y: break
        for pid in ids(blk.split('<h4 class="tb">最重要</h4>')[0].split('<h2',1)[0]):
            assert pid not in ('3616607','18289298'), (f,pid)
assert not os.path.exists('dist/rules') and not os.path.exists('dist/about/ranking')
for f in glob.glob('dist/**/*.html',recursive=True):
    if f.startswith('dist/preview'): continue
    s=open(f,encoding='utf-8').read()
    assert 'rules/index.html' not in s and 'about/ranking' not in s and '规则说明' not in s, f
c=open('dist/papers/pmid-30548336/index.html',encoding='utf-8').read().split('id="evidence"',1)[1]
assert '原文自称病例对照' in c
print('newest-5y / rules-off tests OK')
for f in glob.glob('dist/**/*.html',recursive=True):
    if not f.startswith('dist/preview'): assert '本库同主题' not in open(f,encoding='utf-8').read(), f
print('no 本库同主题 OK')
