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
# pick_reason: off unless Vibe-approved entries exist
import json
PR=json.load(open('data/v5/extras/pick_reason.json',encoding='utf-8'))
appr=[e for k,v in PR.items() if k!='_meta' for e in v if e.get('approved') is True or str(e.get('approved_by','')).lower()=='vibe']
allhtml=''.join(open(f,encoding='utf-8').read() for f in ['dist/index.html']+glob.glob('dist/topics/*/index.html'))
if not appr:
    assert 'class="why"' not in allhtml
    for k,v in PR.items():
        if k!='_meta':
            for e in v: assert not e.get('pick_reason_zh') or e['pick_reason_zh'] not in allhtml, k
print('empty/short 最新 + pick_reason gating tests OK')
