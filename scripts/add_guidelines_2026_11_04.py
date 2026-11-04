"""Idempotent: merge deep extract's 2026-11-04 new guidelines (42693626, 41224734, 42014100), supersessions and errata
into site data. Re-run after scripts/sync_extras.py (sync overwrites top_picks/speedread/certainty/card_meta)."""
import json, os, shutil, copy
S='/workspace/vetlit/extracts'; R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); V=os.path.join(R,'data','v5'); X=os.path.join(V,'extras')
L=lambda f: json.load(open(f,encoding='utf-8'))
def W(f,d): json.dump(d,open(f,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
for n in ('errata.json','supersession_new_2026-11-04.json'): shutil.copy(os.path.join(S,n),X)
SR={r['pmid']:r for r in L(os.path.join(S,'speedread_new_2026-11-04.json'))}
CM=L(os.path.join(S,'card_meta_new_2026-11-04.json'))['papers']; CE=L(os.path.join(S,'certainty_new_2026-11-04.json'))['papers']
SUP=L(os.path.join(S,'supersession_new_2026-11-04.json'))['records']
TITLE={'42693626':('2026 iCatCare consensus guidelines on the diagnosis and management of chronic kidney disease in cats.','Taylor S','2026-09-01',['ckd','nephrology'],'肾脏'),
 '41224734':('iCatCare 2025 consensus guidelines on the diagnosis and management of diabetes mellitus in cats.','Taylor S','2025-11-01',['diabetes','endocrinology'],'内分泌'),
 '42014100':('2026 AAHA Diabetes Management Guidelines for Cats.','Bugbee A','2026-05-01',['diabetes','endocrinology'],'内分泌')}
OLD={'42693626':'26936494','41224734':'25701862','42014100':'29314873'}
seed=L(os.path.join(V,'seed_library_v6.json')); byp={r['pmid']:r for r in seed}
for pm,(ti,fa,pd,tp,spec) in TITLE.items():
    s=SR[pm]; tmpl=copy.deepcopy(byp[OLD[pm]])
    tmpl.update({'id':pm,'pmid':pm,'title':ti,'first_author':fa,'year':CM[pm]['year'],'journal':CM[pm]['journal'],'doi':s['doi'],'species':'cat','species_zh':'猫',
      'specialty':spec,'topics':tp,'source':'deep extract 速读（全文，2026-11-04）；PMID 经 Vibe 在 PubMed 核实','funding':s['funding_coi_zh'],'errata':'','internal_inconsistency':'',
      'one_line_conclusion_zh':s['one_line_conclusion_zh'],'pub_date':pd,'pub_date_source':'PubMed 发表月份（Vibe 核实）','importance_rank':None,'importance_sort_key':None,
      'license':'未核','fulltext_translation_allowed':False,'cebm_basis':'','results':'',
      'guideline_recommendation':'该指南未分级','recommendation_basis':CE[pm]['strength_quote'],'oa':'未核'})
    if pm in byp: seed[seed.index(byp[pm])]=tmpl
    else: seed.append(tmpl)
W(os.path.join(V,'seed_library_v6.json'),seed)
# licence: not audited for translation -> keep translation off
for pm in TITLE: next(r for r in seed if r['pmid']==pm)['license']='未核'
W(os.path.join(V,'seed_library_v6.json'),seed)
sr=L(os.path.join(V,'speedread_fields_v5.json')); sr=[r for r in sr if r.get('pmid') not in TITLE]+[{k:v for k,v in SR[p].items()} for p in TITLE]; W(os.path.join(V,'speedread_fields_v5.json'),sr)
for f,src in (('card_meta.json',CM),('certainty.json',CE)):
    d=L(os.path.join(V,f)); d['papers'].update(src); W(os.path.join(V,f),d)
gs=[r for r in L(os.path.join(V,'guideline_strength.json')) if r.get('pmid') not in TITLE]
for pm in TITLE: gs.append({'pmid':pm,'guideline':TITLE[pm][0],'scheme':'该指南未分级','strength':'该指南未分级','quote':CE[pm]['strength_quote'],'location':'全文（deep extract 2026-11-04）','url':SR[pm]['text_url'],'verified':True})
W(os.path.join(V,'guideline_strength.json'),gs)
ts=L(os.path.join(X,'text_source.json')); ts.update({p:'full_text' for p in TITLE}); W(os.path.join(X,'text_source.json'),ts)
# top_picks: supersessions + insert new guidelines at the head of guideline block (same type, ≥2021, newest first)
tp=L(os.path.join(X,'top_picks.json'))
for r in SUP:
    tp['supersessions'][r['pmid']]={k:v for k,v in r.items() if k!='pmid'}
INS={'ckd':['42693626'],'nephrology':['42693626'],'diabetes':['42014100','41224734'],'endocrinology':['42014100','41224734']}
for g in tp['topics']:
    ins=INS.get(g['topic'])
    if not ins: continue
    items=[i for i in g['items'] if str(i.get('pmid')) not in TITLE]
    for i in items:
        if str(i.get('pmid')) in tp['supersessions']: i.update(tp['supersessions'][str(i['pmid'])])
    new=[{'pmid':p,'reason':'','title':TITLE[p][0],'year':CM[p]['year'],'design':'指南/共识'} for p in ins]
    pos=1 if g['topic'] in ('ckd','nephrology') and str(items[0]['pmid']).startswith('x-') else 0   # IRIS 2026 staging stays first
    g['items']=items[:pos]+new+items[pos:]
W(os.path.join(X,'top_picks.json'),tp)
tpg=L(os.path.join(V,'topics_pages.json'))
for t in tpg['topics']:
    for p,(ti,_,_,tps,_) in TITLE.items():
        if t['id'] in tps and not any(str(c.get('id'))==p for c in t.get('core') or []):
            t.setdefault('core',[]).insert(0,{'id':p,'reason':''})
W(os.path.join(V,'topics_pages.json'),tpg)
print('merged',list(TITLE))
