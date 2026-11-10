"""Run after both builds: reader pages carry no process/curation content; home stamp only moves when home picks change."""
import os, sys, re, glob, json, subprocess
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); os.chdir(REPO)
BAD=('deep extract','Vibe','判定规则','标签含义','翻译流程','第二译者','每个专题取','CEBM 等级最高','排序规则','#contributors','本周','related_works')
files=[f for f in glob.glob('dist/**/*',recursive=True) if f.endswith(('.html','.xml','.json'))]
assert len(files)>300
for f in files:
    s=open(f,encoding='utf-8').read()
    for b in BAD: assert b not in s, (f,b)
a=open('dist/about/index.html',encoding='utf-8').read()
assert '<h2>参与者</h2>' not in a and '<h2 id="参与者">' not in a and '尚无第二译者审校' not in a and '内容由自动化流程整理，尚未经临床兽医审阅。' in a
assert not os.path.exists('dist/rules') and not os.path.exists('dist/preview/rules')
# home: honest update stamp from data/v5/home_stamp.json
st=json.load(open('data/v5/home_stamp.json',encoding='utf-8')); assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',st['date']) and len(st['hash'])==64
for f in ('dist/index.html','dist/preview/index.html'):
    h=open(f,encoding='utf-8').read()
    assert f'<p class="eb red">// 更新于 {st["date"]}</p><h1>精选</h1>' in h and '>首页</a>' in h and ' 周</p>' not in h, f
import importlib; sys.path.insert(0,REPO); os.environ['VETLIT_LIVE']='1'
B=importlib.import_module('build_preview')
before=open('data/v5/home_stamp.json',encoding='utf-8').read(); B.home()
assert open('data/v5/home_stamp.json',encoding='utf-8').read()==before, 'stamp must not move when picks are unchanged'
# picks change -> date=today, restored afterwards
try:
    json.dump({'hash':'0'*64,'date':'2000-01-01'},open(B.STAMP,'w',encoding='utf-8')); B.home()
    s2=json.load(open(B.STAMP,encoding='utf-8')); assert s2['hash']==st['hash'] and s2['date']!='2000-01-01'
finally: open(B.STAMP,'w',encoding='utf-8').write(before)
print('reader pages / home stamp tests OK')
