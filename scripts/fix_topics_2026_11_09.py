"""Idempotent topic-membership fix (2026-11-09):
31554584 (canine hyperadrenocorticism review) is not a CKD paper -> drop ckd + nephrology; keeps hyperadrenocorticism/endocrinology (saim).
23078651 (Doberman preclinical DCM) is not an MMVD paper -> drop mmvd; keeps cardiomyopathy/cardiology.
Touches only these memberships: seed topics, data/papers topics, topics_pages core/newest/all_ids of the dropped topics."""
import json, os
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); V=os.path.join(R,'data','v5')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
ENDNL='\n' if open(os.path.join(R,'data','papers','pmid-31554584.json'),encoding='utf-8').read().endswith('\n') else ''
DROP={'31554584':{'ckd','nephrology'},'23078651':{'mmvd'}}
KEEP={'31554584':{'hyperadrenocorticism','endocrinology'},'23078651':{'cardiomyopathy','cardiology'}}
f=os.path.join(V,'seed_library_v6.json'); seed=L(f)
for r in seed:
    k=str(r.get('pmid') or '')
    if k in DROP:
        r['topics']=[t for t in r['topics'] if t not in DROP[k]]; assert KEEP[k]<=set(r['topics']), k
W(f,seed)
for k in DROP:
    f=os.path.join(R,'data','papers',f'pmid-{k}.json'); d=L(f)
    d['topics']=[t for t in d['topics'] if t not in DROP[k]]; assert KEEP[k]<=set(d['topics']), k
    open(f,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=2)+ENDNL)
f=os.path.join(V,'topics_pages.json'); tp=L(f)
for t in tp['topics']:
    for k,ts in DROP.items():
        if t['id'] in ts:
            if t.get('all_ids'): t['all_ids']=[i for i in t['all_ids'] if str(i)!=k]
            if t.get('core'): t['core']=[c for c in t['core'] if str(c.get('id'))!=k]
            if t.get('newest'): t['newest']=[c for c in t['newest'] if str(c.get('id'))!=k]
        if t['id'] in KEEP[k]: assert k in json.dumps(t.get('all_ids')), (t['id'],k)
W(f,tp); print('topic memberships fixed',{k:sorted(v) for k,v in DROP.items()})
