"""Run after live build: 31554584 not in ckd/nephrology; 23078651 not in mmvd; both keep their correct topics."""
import os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
T=lambda t: open(f'dist/topics/{t}/index.html',encoding='utf-8').read()
for t in ('ckd','nephrology'): assert 'pmid-31554584/' not in T(t), t
assert 'pmid-23078651/' not in T('mmvd')
for t in ('hyperadrenocorticism','endocrinology','saim'): assert 'pmid-31554584/' in T(t), t
for t in ('cardiomyopathy','cardiology'): assert 'pmid-23078651/' in T(t), t
h=open('dist/index.html',encoding='utf-8').read(); m=re.search(r'<a href="topics/mmvd/">.*?</section>',h,re.S).group(0); assert 'pmid-23078651/' not in m
import json, glob
assert not json.load(open('data/papers/pmid-31554584.json',encoding='utf-8')).get('grade_certainty_topic')
assert 'CKD 主题' not in json.dumps(next(p for p in json.load(open('dist/papers.json',encoding='utf-8')) if str(p.get('pmid'))=='31554584'),ensure_ascii=False)
for f in glob.glob('dist/**/pmid-31554584/**/*.html',recursive=True): assert 'CKD 主题' not in open(f,encoding='utf-8').read(), f
assert 'Vibe' not in json.load(open('data/v5/certainty.json',encoding='utf-8'))['_meta']['rules_v4_amend_2026-11-09_indirectness']
print('topic membership fix tests OK')
