"""Run after live build: 31554584 not in ckd/nephrology; 23078651 not in mmvd; both keep their correct topics."""
import os, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'))
T=lambda t: open(f'dist/topics/{t}/index.html',encoding='utf-8').read()
for t in ('ckd','nephrology'): assert 'pmid-31554584/' not in T(t), t
assert 'pmid-23078651/' not in T('mmvd')
for t in ('hyperadrenocorticism','endocrinology','saim'): assert 'pmid-31554584/' in T(t), t
for t in ('cardiomyopathy','cardiology'): assert 'pmid-23078651/' in T(t), t
h=open('dist/index.html',encoding='utf-8').read(); m=re.search(r'<a href="topics/mmvd/">.*?</section>',h,re.S).group(0); assert 'pmid-23078651/' not in m
print('topic membership fix tests OK')
