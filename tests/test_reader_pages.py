"""Run after both builds: reader pages carry no process/curation content; home stamp only moves when home picks change."""
import os, sys, re, glob, json, subprocess
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); os.chdir(REPO)
BAD=('deep extract','Vibe','判定规则','标签含义','翻译流程','第二译者','每个专题取','CEBM 等级最高','排序规则','#contributors','本周','related_works','第三方裁定','第二评估者','单人','双人','双重独立','逐条核对','尚无临床兽医审阅','第二人复核')
files=[f for f in glob.glob('dist/**/*',recursive=True) if f.endswith(('.html','.xml','.json'))]
assert len(files)>300
for f in files:
    s=open(f,encoding='utf-8').read()
    for b in BAD:
        if b=='本周':
            s2=s.replace('其余专题本周无新增','').replace('本周新增专题','').replace('本周无新增','')
            assert '本周' not in s2, (f,b)
        else:
            assert b not in s, (f,b)
a=open('dist/about/index.html',encoding='utf-8').read()
assert '<h2>参与者</h2>' not in a and '<h2 id="参与者">' not in a and '尚无第二译者审校' not in a and '内容由自动化流程整理，尚未经临床兽医审阅。' in a
assert not os.path.exists('dist/rules') and not os.path.exists('dist/preview/rules')
# home: 更新于 is the actual build date (America/Los_Angeles)
import datetime, zoneinfo
today=datetime.datetime.now(zoneinfo.ZoneInfo('America/Los_Angeles')).date().isoformat()
st=json.load(open('data/v5/home_stamp.json',encoding='utf-8')); assert re.fullmatch(r'\d{4}-\d{2}-\d{2}',st['date']) and len(st['hash'])==64
assert st['date']==today
for f in ('dist/index.html','dist/preview/index.html'):
    h=open(f,encoding='utf-8').read()
    assert f'<p class="eb red">// 更新于 {today}</p><h1>精选</h1>' in h and '>首页</a>' in h and ' 周</p>' not in h, f
import importlib; sys.path.insert(0,REPO); os.environ['VETLIT_LIVE']='1'
B=importlib.import_module('build_preview')
before=json.load(open('data/v5/home_stamp.json',encoding='utf-8'))
B.home()
after=json.load(open('data/v5/home_stamp.json',encoding='utf-8'))
assert after['hash']==before['hash'], 'pick-list hash must not move when picks are unchanged'
assert after['date']==today
# stale hash -> hash restored, date=today; then restore file
try:
    json.dump({'hash':'0'*64,'date':'2000-01-01'},open(B.STAMP,'w',encoding='utf-8')); B.home()
    s2=json.load(open(B.STAMP,encoding='utf-8')); assert s2['hash']==before['hash'] and s2['date']==today
finally:
    json.dump(before,open(B.STAMP,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
print('reader pages / home stamp tests OK')
