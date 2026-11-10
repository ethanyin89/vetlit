"""Run after live build: 适用范围 row (certainty.json applicability_note_zh) inside 证据与方法, only when non-empty; no process status."""
import os, sys, re, glob, copy
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
# fixture: empty / missing -> no row; non-empty -> one row right after 结果
PM='26776583'; p=B.get(PM); base=copy.deepcopy(B.CERT[PM])
try:
    B.CERT[PM]=dict(base,applicability_note_zh='  '); _,f0=B.grade(p); assert '适用范围' not in f0
    B.CERT[PM]={k:v for k,v in base.items() if k!='applicability_note_zh'}; _,f1=B.grade(p); assert '适用范围' not in f1
    B.CERT[PM]=dict(base,applicability_note_zh='仅测试'); _,f2=B.grade(p)
    assert re.search(r'<tr><th>结果</th><td>[^<]*</td></tr><tr><th>适用范围</th><td>仅测试</td></tr>',f2), f2
finally: B.CERT[PM]=base
HAS={k for k,r in B.CERT.items() if isinstance(r,dict) and str(r.get('applicability_note_zh') or '').strip()}
assert len(HAS)==13, len(HAS)
for f in glob.glob('dist/papers/*/index.html'):
    h=open(f,encoding='utf-8').read(); pm=f.split('/')[-2].replace('pmid-','')
    top,ev=(h.split('id="evidence"',1)+[''])[:2]
    assert '<th>适用范围</th>' not in top, f
    if pm in HAS: assert ev.count('<th>适用范围</th>')==1, f
    else: assert '<th>适用范围</th>' not in h, f
    for bad in ('own_evidence_strength','rob_items','待审阅','审阅确认','复核通过','归类错误','indirectness_rulings','source_file'): assert bad not in h, (f,bad)
assert '原文自报证据强度：Moderate' in open('dist/papers/pmid-42004674/index.html',encoding='utf-8').read() and '原文自报证据强度：Weak' in open('dist/papers/pmid-42007020/index.html',encoding='utf-8').read()
print('applicability row tests OK')
# 24217707: JBI prevalence checklist (bias row + 9 item rows with quotes)
h=open('dist/papers/pmid-24217707/index.html',encoding='utf-8').read()
assert '<tr><th>偏倚风险</th><td>JBI 患病率清单：高' in h and '不适用（无公认工具）' not in h
t=re.search(r'<table><thead><tr><th>条目</th>.*?</table>',h,re.S).group(0)
assert len(re.findall(r'<tr><td>Q[1-9] ',t))==9 and t.count('<blockquote')==9
print('24217707 JBI tests OK')
