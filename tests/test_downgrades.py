"""Run after live build: downgrade rows labelled by steps (不降级/降一级/降两级); legacy strings stay 降一级; no source_file / rule ids / _meta on pages."""
import os, sys, re, glob, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B
assert B.dg_label('旧字符串')=='降一级' and B.dg_label({'reason_zh':'x'})=='降一级'
assert B.dg_label({'domain':'间接性','steps':-1})=='间接性 降一级' and B.dg_label({'domain':'偏倚风险','steps':-2})=='偏倚风险 降两级' and B.dg_label({'domain':'偏倚风险','steps':0})=='偏倚风险 不降级'
H=lambda pm: open(f'dist/papers/pmid-{pm}/index.html',encoding='utf-8').read()
th=lambda pm: re.findall(r'<tr><th>([^<]*(?:降[一两三]级|不降级))</th>',H(pm))
assert th('40470278')==['偏倚风险 降两级','间接性 降一级'], th('40470278')
assert th('34180084')==['偏倚风险 不降级','间接性 降一级'], th('34180084')
assert th('20187911')==['偏倚风险 降两级','间接性 降一级'], th('20187911')
M=json.load(open('data/v5/certainty.json',encoding='utf-8'))['_meta']
assert M['rules_v4_amend_2026-11-09_indirectness'].endswith('研究人群比专题问题宽时，降一级。') and 'downgrades_schema' in M
assert set(M['rules_v4_amend_2026-11-09_dogAD'])=={'R-nodown-bias-toward-null','R-down-noninferiority-ITT-CI','R-SR-body-of-evidence'}
for f in glob.glob('dist/**/*.html',recursive=True)+['dist/papers.json','dist/feed.xml']:
    s=open(f,encoding='utf-8').read()
    assert 'source_file' not in s and 'downgrades_schema' not in s and 'rules_v4_amend' not in s and not re.search(r'\bR-(?:down|nodown|design|VF|SR|na|start|no|guideline|rob)-',s), f
print('downgrade labels tests OK')
