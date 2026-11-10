"""Deep speed-read card (batch1 ACP Journal Club shape); only explicitly approved PMIDs render; stale-fact fixes."""
import os, sys, re, glob, json, hashlib
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

APPROVED={'18638016','23078651','26776588','27678080','30548336','32441826','34180084','38952053','42805756'}
# later batch1 additions — present in extracts but not approved, must not render
UNREVIEWED={'11991408','15954557','20005753','21704901','23422366','23522175','23647231','24112317','25883356','25896026','26260508','26265631','26581469','27143042','28965673','29314873','30353952','30451613','30543707','30797439','30974015','31554584','31998612','32139728','32243654','34758043','36002137','37167252','37766254','40470278','41224734','42014100','42043241','42693626','x-international-renal-interest-society-2026-iris-staging-of-ckd-modified-2026'}
assert B.DS_APPROVED==APPROVED
assert set(B.DS)==APPROVED
assert not hasattr(B,'DS_HOLD') or not B.DS_HOLD

H=lambda pm: open(f'dist/papers/pmid-{pm}/index.html',encoding='utf-8').read()
LEAK=('clinical_bottom_line','clinical_question_pico','design_and_subjects','scope_and_methods','main_results','main_recommendations','authors_conclusion','section_order','certainty_ref','source_md','quotes_file','现版卡片','R-down-indirectness-surrogate','deep extract','Vibe')
for f in glob.glob('dist/**/*.html',recursive=True)+['dist/papers.json']:
    if not os.path.exists(f): continue
    s=open(f,encoding='utf-8').read()
    for b in LEAK: assert b not in s, (f,b)

def parts(pm):
    h=H(pm); top,fold=h.split('id="evidence"',1); return h,top,fold

for pm in sorted(APPROVED):
    h,top,fold=parts(pm)
    assert 'class="dsbl"' in top and '>临床结论<' in top, pm
    assert 'class="blk ds"' in top and '一句话结论' not in top, pm
    rec=B.DS[pm]
    assert rec['title_zh'] in h
    heads=[]
    for k in rec['section_order']:
        if k in B.DS_SKIP or not rec['sections'].get(k,{}).get('markdown','').strip(): continue
        hd=rec['sections'][k]['heading']
        heads.append(hd)
        assert hd in top, (pm,hd)
    assert heads[0].startswith('临床结论') or '临床结论' in top

assert 'NNT ≈ 3' in parts('34180084')[1] and '对象（P）' in parts('34180084')[1]
assert '主要推荐（原文逐字，附 SOR）' in parts('42805756')[1] and '本卡未读' in parts('42805756')[1]

# unreviewed speed-reads must not appear, even if they exist in batch1.json
for pm in UNREVIEWED:
    if pm.startswith('x-'):
        # IRIS 2026 uses a non-PMID id; skip page check if no reader page
        path=f'dist/papers/pmid-{pm}/index.html'
        if not os.path.exists(path):
            assert pm not in B.DS
            continue
    h,top,fold=parts(pm)
    assert 'class="dsbl"' not in h and 'class="blk ds"' not in h, pm
    assert '一句话结论' in top, pm
    assert pm not in B.DS

# 38952053: approved corrected speed-read (no NNT, no 血钙更稳); certainty 中; no 稳定
h,top,fold=parts('38952053')
FGF='两组 FGF23 变化率差异不显著（全分析集 P=.17，符合方案集 P=.25）'
assert FGF in top and '证据确定性：中' in top and '证据确定性：高' not in top
assert '稳定' not in top
assert '血钙更稳' not in h
assert 'NNT' not in top and 'NNT' not in fold.split('id="translation"',1)[0] if 'id="translation"' in fold else 'NNT' not in fold
assert '间接性 降一级' in fold and 'R-down-indirectness-surrogate' not in h
assert B.CERT['38952053']['certainty']=='中' and 'R-down-indirectness-surrogate' in B.CERT['38952053']['rules_applied']

# 26776588: speed-read is approved, but certainty stays 暂未评级（仅有摘要）
h,top,fold=parts('26776588')
assert 'class="dsbl"' in top
assert '暂未评级（仅有摘要）' in top and 'class="echip na"' in top and '<th>结果</th><td>暂未评级（仅有摘要）</td>' in fold
assert 'why0' not in fold and '证据确定性待评定' not in h

# stale-fact fixes (verified against rob_round1 / text_source / certainty / full-text quotes)
h,top,fold=parts('18638016')
assert 'RoB 2 总体：一些担忧' in fold and '未完整评估' not in fold and '依据：全文' in h
h,top,fold=parts('30548336')
assert 'QUIPS 总体：高偏倚风险' in fold and '尚未评估偏倚风险' not in h and '依据：全文' in h
assert 'CEBM Level 3' in fold
h,top,fold=parts('32441826')
assert 'JBI 病例系列清单：高' in fold and '不适用（无公认工具）' not in fold
assert len(re.findall(r'<tr><td>Q(?:10|[1-9]) ',fold))==10
h,top,fold=parts('23647231')
assert '依据：摘要' not in h and '依据：全文' in h
assert 'JBI 患病率清单（患病率）：高；QUIPS（预后）：高' in fold and '未评（仅摘要）' not in fold

# 15954557 / 27143042: main-result placeholders filled from full text; no unsourced IRIS origin claim
h,top,fold=parts('15954557')
assert '摘要未给出' not in top and '原文未报告' not in top.split('<section class="kn">',1)[-1].split('</section>',1)[0]
assert '由此而来' not in h
assert 'UPC ≥0.5' in top and 'UPC ≥0.4' in top
h,top,fold=parts('27143042')
kn=top.split('<section class="kn">',1)[-1].split('</section>',1)[0]
assert '摘要未给出' not in kn and '原文未报告' not in kn
assert '1.25–2.5 mg/猫 q12h' in kn

# 38952053 speed-read lists both hyper-Mg denominators (Vibe wording)
h,top,fold=parts('38952053')
assert '5/27' in top and '1/33' in top and '5/21' in top and '1/23' in top
assert '间接性降一级' in h or '间接性 降一级' in h
assert '起始高' in parts('38952053')[0] or '起始高' in fold or '证据确定性中（起始高' in h

# certainty explanation sentences regenerated from certainty.json
h,top,fold=parts('18638016')
assert 'D4 影响主要结局' in h and '起始高' in h and '证据确定性中' in h
h,top,fold=parts('30548336')
assert '起始高' in h and 'QUIPS 总体高偏倚风险' in h and '证据确定性中' in h
h,top,fold=parts('32441826')
assert '起始低' in h and '证据确定性极低' in h and 'JBI 病例系列清单总体高' in h

# 30543707: body denominator (16/24, 15 improved); no unsourced FDA claim; ROBINS-I
h,top,fold=parts('30543707')
assert 'class="dsbl"' not in h  # speed-read not yet approved
assert '引发 FDA 调查' not in h and 'FDA 调查' not in h
assert '随访超声' in top and '15' in top and '16' in top
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'ROBINS-I 总体：极严重' in fold or 'ROBINS-I 总体极严重' in h

# 30974015: full text has 4 LOE-strong items, not 3
h,top,fold=parts('30974015')
assert 'class="dsbl"' not in h
kn=top.split('<section class="kn">',1)[-1].split('</section>',1)[0] if '<section class="kn">' in top else ''
assert 'LOE strong 条目数' in kn
assert re.search(r'LOE strong 条目数</b>\s*4\b', kn) or re.search(r'LOE strong 条目数</b>[^<]*\b4\b', kn), kn
assert not re.search(r'LOE strong 条目数</b>\s*3\b', kn)
# 32139728 / 26581469: replace outdated no-tool text with repo assessments
h,top,fold=parts('32139728')
assert 'class="dsbl"' not in h
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'JBI 患病率清单：高' in fold or 'JBI 患病率清单总体高' in h
h,top,fold=parts('26581469')
assert 'class="dsbl"' not in h
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'JBI 队列清单：高' in fold or 'JBI 队列清单总体高' in h

# papers without deep speed-read data (and not otherwise edited) keep the old first screen
ctrl='36002137'
assert '36002137' not in B.DS
h,top,fold=parts(ctrl)
assert '一句话结论' in top and '关键数字' in top and 'class="blk ds"' not in h

print('deep speed-read / fact-fix tests OK')
