"""Copy teammates' optional files from /workspace/vetlit/extracts into data/v5/extras (run before commit)."""
import os, shutil, glob
S='/workspace/vetlit/extracts'; D=os.path.join(os.path.dirname(__file__),'..','data','v5','extras')
os.makedirs(os.path.join(D,'translations'),exist_ok=True)
for n in ('speedread_fields_v5.json',) :
    if os.path.exists(os.path.join(S,n)): shutil.copy(os.path.join(S,n),os.path.join(D,'..')); print('synced',n)
for n in ('top_picks.json','related_reading.json','text_source.json','licence_audit.json'):
    if os.path.exists(os.path.join(S,n)): shutil.copy(os.path.join(S,n),D); print('synced',n)
for f in glob.glob(os.path.join(S,'translations','*.json')): shutil.copy(f,os.path.join(D,'translations')); print('synced',f)
# speed-read page markdown (e.g. deep extract's “原文报告不一致” sections) and methods fields
C=os.path.join(os.path.dirname(__file__),'..','content','extracts38')
for f in glob.glob(os.path.join(S,'*.md')):
    if os.path.exists(os.path.join(C,os.path.basename(f))): shutil.copy(f,C); print('synced',f)
if os.path.exists(os.path.join(S,'methods_fields.json')): shutil.copy(os.path.join(S,'methods_fields.json'),os.path.join(D,'..')); print('synced methods_fields.json')
# Vibe's appraisal source (papers.json) and deep extract's certainty.json
V5=os.path.join(os.path.dirname(__file__),'..','data','v5')
if os.path.exists(os.path.join(S,'papers.json')): shutil.copy(os.path.join(S,'papers.json'),os.path.join(V5,'appraisal_papers.json')); print('synced papers.json -> appraisal_papers.json')
if os.path.exists(os.path.join(S,'certainty.json')): shutil.copy(os.path.join(S,'certainty.json'),V5); print('synced certainty.json')
