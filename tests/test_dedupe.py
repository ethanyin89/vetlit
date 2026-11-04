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
