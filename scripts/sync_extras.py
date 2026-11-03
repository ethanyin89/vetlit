"""Copy teammates' optional files from /workspace/vetlit/extracts into data/v5/extras (run before commit)."""
import os, shutil, glob
S='/workspace/vetlit/extracts'; D=os.path.join(os.path.dirname(__file__),'..','data','v5','extras')
os.makedirs(os.path.join(D,'translations'),exist_ok=True)
for n in ('top_picks.json','related_reading.json','text_source.json','licence_audit.json'):
    if os.path.exists(os.path.join(S,n)): shutil.copy(os.path.join(S,n),D); print('synced',n)
for f in glob.glob(os.path.join(S,'translations','*.json')): shutil.copy(f,os.path.join(D,'translations')); print('synced',f)
