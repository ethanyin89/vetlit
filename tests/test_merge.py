"""Run: python3 tests/test_merge.py — merges into a temp copy of data/, never touches the repo."""
import json, os, shutil, subprocess, sys, tempfile, glob
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..')
t=tempfile.mkdtemp(); os.makedirs(os.path.join(t,'scripts')); os.makedirs(os.path.join(t,'content'))
shutil.copy(os.path.join(REPO,'scripts','merge_import.py'),os.path.join(t,'scripts'))
shutil.copytree(os.path.join(REPO,'data'),os.path.join(t,'data'))
P=os.path.join(t,'data','papers')
def run(recs):
    f=os.path.join(t,'in.json'); json.dump(recs,open(f,'w'))
    return subprocess.run([sys.executable,os.path.join(t,'scripts','merge_import.py'),f,'--source','test'],capture_output=True,text=True)
n0=len(glob.glob(P+'/*.json'))
r=run([{'id':'iris-ckd-staging-2023','title':'IRIS Staging of CKD (2023)','year':'2023','species':'猫/犬','doc_type':'指南'},
       {'title':'no keys at all'}])
assert r.returncode==0, r.stderr
assert 'WARNING skip' in r.stderr, r.stderr
f=os.path.join(P,'iris-ckd-staging-2023.json'); assert os.path.exists(f)
assert len(glob.glob(P+'/*.json'))==n0+1
# second delivery with same id updates, not duplicates
run([{'id':'iris-ckd-staging-2023','guideline_recommendation':'verbatim text'}])
assert json.load(open(f))['guideline_recommendation']=='verbatim text' and len(glob.glob(P+'/*.json'))==n0+1
# DOI match: case-insensitive, prefix stripped
run([{'doi':'10.1234/ABC.Test','title':'doi rec','year':'2024'}])
run([{'doi':'https://doi.org/10.1234/abc.test','one_line_conclusion_zh':'x'}])
d=[json.load(open(x)) for x in glob.glob(P+'/doi-*.json')]
assert len(d)==1 and d[0]['one_line_conclusion_zh']=='x' and d[0]['doi']=='10.1234/abc.test'
# PMID takes priority over DOI/id
any_p=json.load(open(sorted(glob.glob(P+'/pmid-*.json'))[0]))
run([{'pmid':any_p['pmid'],'id':'something-else','title_zh':'T'}])
assert json.load(open(os.path.join(P,any_p['id']+'.json')))['title_zh']=='T'
shutil.rmtree(t); print('merge tests OK')
