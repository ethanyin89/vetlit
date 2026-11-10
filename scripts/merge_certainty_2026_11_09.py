"""Idempotent: merge ONLY deep extract's 18638016 and 23647231 certainty entries and the _meta key
rules_v4_amend_2026-11-09 from /workspace/vetlit/extracts/certainty.json. Its rewritten _meta.rules is NOT taken,
and every other live entry (incl. the 13 hyperthyroidism 待评定 papers and 37167252) is kept. Do not copy the file."""
import json, os
S='/workspace/vetlit/extracts/certainty.json'; F=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5','certainty.json')
src=json.load(open(S,encoding='utf-8')); d=json.load(open(F,encoding='utf-8'))
for k in ('18638016','23647231'):
    assert src['papers'][k]['certainty']=='中', k
    d['papers'][k]=src['papers'][k]
d['_meta']['rules_v4_amend_2026-11-09']=src['_meta']['rules_v4_amend_2026-11-09']
json.dump(d,open(F,'w',encoding='utf-8'),ensure_ascii=False,indent=1); print('merged certainty 18638016, 23647231 + _meta rules_v4_amend_2026-11-09')
