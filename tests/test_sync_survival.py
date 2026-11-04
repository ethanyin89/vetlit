"""Regression: after scripts/sync_extras.py, the 2026-11-04 guideline batch must survive.
Runs sync in a temp copy of the repo (repo itself untouched).
SKIP if the extracts dir is absent (CI)."""
import json, os, shutil, subprocess, sys, tempfile
R=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
if not os.path.isdir('/workspace/vetlit/extracts'): print('SKIP test_sync_survival: no extracts dir'); sys.exit(0)
T=tempfile.mkdtemp(); C=os.path.join(T,'r')
shutil.copytree(R,C,ignore=shutil.ignore_patterns('.git','node_modules','dist','__pycache__'))
subprocess.run([sys.executable,os.path.join(C,'scripts','sync_extras.py')],check=True,stdout=subprocess.DEVNULL)
L=lambda *p: json.load(open(os.path.join(C,'data','v5',*p),encoding='utf-8'))
tp=L('extras','top_picks.json'); # build_preview drops items whose supersession scope is 'full' from displayed lists
listed={str(i.get('pmid')) for g in tp['topics'] for i in g['items'] if not (i.get('superseded_by') and (i.get('supersession_scope') or 'full')=='full')}
NEW=('42693626','41224734','42014100'); fails=[]
for p in NEW:
    if p not in listed: fails.append(f'{p} not on lists')
    if p not in L('card_meta.json')['papers']: fails.append(f'{p} missing card_meta')
    if p not in L('certainty.json')['papers']: fails.append(f'{p} missing certainty')
    if p not in {str(r.get('pmid')) for r in L('speedread_fields_v5.json')}: fails.append(f'{p} missing speedread')
for p in ('26936494','25701862'):
    if p in listed: fails.append(f'superseded {p} still on lists')
if '29314873' not in listed: fails.append('29314873 dropped from lists')
sup=tp.get('supersessions',{})
if sup.get('29314873',{}).get('supersession_scope')!='cats_only': fails.append('29314873 cats_only supersession lost')
for p in ('26936494','25701862'):
    if p not in sup: fails.append(f'{p} supersession lost')
try: er=L('extras','errata.json')
except Exception: er={}
for p in ('42014100','36002137'):
    if p not in er: fails.append(f'errata {p} lost')
shutil.rmtree(T)
if fails:
    print('FAIL test_sync_survival:'); [print('  -',f) for f in fails]; sys.exit(1)
print('test_sync_survival OK')
