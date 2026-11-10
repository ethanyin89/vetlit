"""Idempotent: apply deep extract's 2026-11-09 rule-id renames to live certainty data (_meta keys/texts and paper references)."""
import json, os
F=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5','certainty.json')
REN={'R-VF-bias-toward-null':'R-nodown-bias-toward-null','R-VF-noninferiority-ITT-CI':'R-down-noninferiority-ITT-CI',
 'R-VF-knowledge-summary-own-strength':'R-na-knowledge-summary-own-strength','R-VF-ruling-30797439-design-harm':'R-design-30797439-harm',
 'R-VF-ruling-SR-included-designs-unverified':'R-start-SR-included-designs-unverified'}
s=open(F,encoding='utf-8').read()
for a,b in REN.items(): s=s.replace(a,b)
assert 'R-VF-' not in s
d=json.loads(s); json.dump(d,open(F,'w',encoding='utf-8'),ensure_ascii=False,indent=1); print('renamed',len(REN))
