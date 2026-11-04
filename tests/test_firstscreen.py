"""Paper first screen: conclusion (no near-dup), key numbers, 能说/不能说 outside fold, funding line under meta."""
import os,sys,glob,re
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); os.chdir(REPO)
s=open('dist/papers/pmid-36002137/index.html',encoding='utf-8').read()
top,fold=s.split('id="evidence"',1)
assert '一句话结论' in top and '关键数字' in top and '<h3>能说' in top and '<h3>不能说' in top
assert 'class="cm"' not in top  # near-duplicate clinical meaning dropped
assert re.search(r'<p class="cmeta">[^<]*</p><p class="cmeta fund">资助/利益冲突：',top)
assert '<h3>能说' not in fold
assert '>PICO' not in top and '展开逐项判断' not in top
for f in glob.glob('dist/papers/*/index.html'):
    t=open(f,encoding='utf-8').read(); assert '<h3>能说' not in t.split('id="evidence"',1)[-1], f
    assert 'P 不适用' not in t, f
print('firstscreen tests OK')
