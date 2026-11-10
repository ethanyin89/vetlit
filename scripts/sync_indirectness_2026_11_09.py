"""Idempotent: deep extract's indirectness rulings (2026-11-09). Takes from extracts/certainty.json ONLY the paper entries that
differ from live (23 incl. 24217707, ruled 低) -- whole-entry replacement of those entries; _meta and every other entry untouched.
Also applies extracts/card_wording_override_2026-11-09.json to speedread_fields_v5.json (only its entries/fields)."""
import json, os
S='/workspace/vetlit/extracts'; V=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..','data','v5')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
IDS=['11991408','16734085','24217707','25673019','26079532','26776583','27103204','28901812','30543707','30755068','3616607','36297266',
     '37548535','37632022','37732386','39066306','39858209','40941356','41527203','41701235','41781382','42004674','42949438']
src=L(os.path.join(S,'certainty.json')); ce=L(os.path.join(V,'certainty.json'))
assert len(src['papers'])==112
for k in IDS:
    r=src['papers'][k]
    assert 'R-VF-' not in json.dumps(r) and not any(x in str(r.get('rob_tool') or '') for x in ('AMSTAR','ROBIS')), k
    ce['papers'][k]=r
W(os.path.join(V,'certainty.json'),ce)
O=L(os.path.join(S,'card_wording_override_2026-11-09.json'))
sr=L(os.path.join(V,'speedread_fields_v5.json')); n=0
for r in sr:
    k=str(r.get('pmid') or '')
    if k in O and not k.startswith('_'):
        for f,v in O[k].items():
            if not f.startswith('_'): r[f]=v; n+=1
W(os.path.join(V,'speedread_fields_v5.json'),sr); print('indirectness entries',len(IDS),'; card wording fields',n)
