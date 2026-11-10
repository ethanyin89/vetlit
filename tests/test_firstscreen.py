"""Paper first screen: conclusion (no near-dup), key numbers, 能说/不能说 outside fold, funding line under meta."""
import os,sys,glob,re
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); os.chdir(REPO)
s=open('dist/papers/pmid-29660848/index.html',encoding='utf-8').read()
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
# (a) top3 order + verbatim "摘要未给出"
import json
d=open('dist/papers/pmid-22269057/index.html',encoding='utf-8').read().split('id="evidence"',1)[0]
kn=re.search(r'<section class="kn">(.*?)</section>',d,re.S).group(1)
ms=re.findall(r'<li data-m="([^"]*)"',kn)
assert ms==['1 年内进展','1 年内进展的预测因素（全部猫）','2 期→4 期'], ms
assert kn.count('摘要未给出')>=3, kn
for li in re.findall(r'<li.*?</li>',kn,re.S): assert '摘要未给出' in li
# (b) ⚠ notices on first screen inside key-number block, not in fold
R=json.load(open('data/v5/extras/reporting_inconsistency.json',encoding='utf-8'))
for k in ('41781382','38952053'):
    t=open(f'dist/papers/pmid-{k}/index.html',encoding='utf-8').read(); top,fold=t.split('id="evidence"',1)
    assert '⚠' in top and R[k]['note_zh'] in top, k
    kn=re.search(r'<section class="kn">(.*?)</section>',top,re.S)
    if k=='38952053':
        # deep speed-read replaces the first-screen key-number block; the notice stays above the fold
        assert kn is None
    else:
        assert kn and '⚠' in kn.group(1) and R[k]['note_zh'] in kn.group(1), k
    assert R[k]['note_zh'] not in fold, k
print('key-number order / verbatim / notice tests OK')
