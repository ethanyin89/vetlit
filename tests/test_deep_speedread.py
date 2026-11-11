"""Deep speed-read card (ACP Journal Club shape); only explicitly approved IDs render; stale-fact fixes."""
import os, sys, re, glob, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

APPROVED=set(json.load(open('data/v5/deep_speedread_approved.json',encoding='utf-8'))['approved'])
assert '11991408' in APPROVED and '42977701' in APPROVED and '43004944' in APPROVED and len(APPROVED)==46
assert B.DS_APPROVED==APPROVED
assert set(B.DS)==APPROVED
assert not hasattr(B,'DS_HOLD') or not B.DS_HOLD

def page_path(pm):
    for p in (f'dist/papers/pmid-{pm}/index.html', f'dist/papers/{pm}/index.html'):
        if os.path.exists(p): return p
    raise SystemExit('no reader page for '+pm)

H=lambda pm: open(page_path(pm),encoding='utf-8').read()
LEAK=('clinical_bottom_line','clinical_question_pico','design_and_subjects','scope_and_methods','main_results','main_recommendations','authors_conclusion','section_order','certainty_ref','source_md','quotes_file','现版卡片','R-down-indirectness-surrogate','deep extract','Vibe')
INTERNAL_KEY=re.compile(r'_internal(?:_[A-Za-z0-9_]+)?')
def walk_keys(o,acc=None):
    acc=[] if acc is None else acc
    if isinstance(o,dict):
        for k,v in o.items():
            acc.append(str(k)); walk_keys(v,acc)
    elif isinstance(o,list):
        for x in o: walk_keys(x,acc)
    return acc
for f in glob.glob('dist/**/*.html',recursive=True)+['dist/papers.json']:
    if not os.path.exists(f): continue
    s=open(f,encoding='utf-8').read()
    for b in LEAK: assert b not in s, (f,b)
    # (a) fields whose key starts with _internal must not appear on reader pages or in papers.json
    if f.endswith('.json'):
        bad=[k for k in walk_keys(json.loads(s)) if k.startswith('_internal')]
        assert not bad, (f,bad)
        assert '_internal' not in s, f
    else:
        m=INTERNAL_KEY.search(s)
        assert not m, (f,m.group())

def parts(pm):
    h=H(pm); top,fold=h.split('id="evidence"',1); return h,top,fold

def dsbl(top):
    m=re.search(r'<section class="dsbl">(.*?)</section>',top,re.S)
    return m.group(1) if m else ''

for pm in sorted(APPROVED):
    h,top,fold=parts(pm)
    assert 'class="dsbl"' in top and '>临床结论<' in top, pm
    assert 'class="blk ds"' in top and '<p class="eb red">一句话结论</p>' not in top, pm
    rec=B.DS[pm]
    assert rec['title_zh'] in h
    heads=[hd for _,hd,_ in B.ds_sections(rec)]
    for hd in heads:
        assert hd in top, (pm,hd)
    assert heads and (heads[0].startswith('临床结论') or '临床结论' in top)

assert 'NNT ≈ 3' in parts('34180084')[1] and '对象（P）' in parts('34180084')[1]
assert '主要推荐（原文逐字，附 SOR）' in parts('42805756')[1] and '本卡未读' in parts('42805756')[1]

# 11991408: approved speed-read; unrated chip/row; start_basis without 起评
h,top,fold=parts('11991408')
assert '11991408' in B.DS
assert 'class="dsbl"' in top and '一句话结论' not in top
assert '暂未评级（仅有摘要）' in top and 'class="echip na"' in top and '<th>结果</th><td>暂未评级（仅有摘要）</td>' in fold
assert '证据确定性：暂未评级（仅有摘要）' in top
assert '摘要未说明分组方式' in top and '配对饲喂对照试验；摘要未说明分组方式' in fold
assert 'why0' not in fold and '证据确定性待评定' not in h
assert '起评' not in h
assert B.CERT['11991408']['start_basis']=='配对饲喂对照试验；摘要未说明分组方式'
assert not any(str(k).startswith('_internal') for k in B.CERT['11991408'])

# (b) reader text of unrated papers (待评定 / 暂未评级) contains no 起评
# rated papers may use GRADE footnote style, e.g. 从“高”起评
def is_unrated(pm):
    if str(pm) in B.PENDING_LABEL: return True
    c=(B.CERT.get(str(pm)) or {}).get('certainty')
    return c=='待评定' or (isinstance(c,str) and c.startswith('暂未评级'))
unrated_seen=0
for f in glob.glob('dist/papers/*/index.html'):
    name=os.path.basename(os.path.dirname(f))
    pm=name[5:] if name.startswith('pmid-') else name
    if not is_unrated(pm): continue
    s=open(f,encoding='utf-8').read()
    unrated_seen+=1
    assert '起评' not in s, (pm,)
    assert '起点为' not in s, (pm,)
assert unrated_seen>=3
# cleaned unrated certainty narratives now render (no rating-start wording)
for pm in ('30797439','25896026','20005753','26265631','26776588'):
    h,top,fold=parts(pm)
    assert '证据确定性：暂未评级（仅有摘要）' in top, pm
    assert '起评' not in h and '起点为' not in h, pm
# restoration: rated speed-read keeps approved GRADE 起评 wording (was previously stripped by DS_SKIP)
assert '按 GRADE 对患病率问题的做法从“高”起评' in parts('23647231')[1]

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
# clinical conclusion must not contain 0.37%; results may, with the Bayesian/experience caveat
assert 'class="dsbl"' in top
assert '0.37%' not in dsbl(top)
assert '0.37%' in top
assert '只能作参考' in top or '贝叶斯' in top

# 15954557 / 27143042: main-result placeholders filled from full text; no unsourced IRIS origin claim
h,top,fold=parts('15954557')
assert '摘要未给出' not in top and '原文未报告' not in top
assert '由此而来' not in h
assert 'UPC ≥0.5' in top and 'UPC ≥0.4' in top
h,top,fold=parts('27143042')
assert '摘要未给出' not in top and '原文未报告' not in top
assert '1.25–2.5 mg' in top and ('每日两次' in top or 'q12' in top)

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

# 30543707: body denominator (16/24, 15 improved); no unsourced FDA claim; ROBINS-I; now a deep speed-read
h,top,fold=parts('30543707')
assert 'class="dsbl"' in top
assert 'class="warn"' in top
assert '证据确定性极低；仅 16/24 只犬做了复查超声' in top
# warning sits above the clinical-conclusion block
assert top.find('class="warn"') < top.find('class="dsbl"')
assert '引发 FDA 调查' not in h and 'FDA 调查' not in h
assert '随访超声' in top and '16' in top
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'ROBINS-I 总体：极严重' in fold or 'ROBINS-I 总体极严重' in h
assert '间接性' in fold and '已到底' in h

# 30974015: full text has 4 LOE-strong items, not 3 (now in the speed-read body)
h,top,fold=parts('30974015')
assert 'class="dsbl"' in top
assert '全文标为 strong 的有 4 处' in top
assert '全文标为 strong 的有 3 处' not in h

# 32139728 / 26581469: repo assessments; 26581469 certainty 中, no surrogate downgrade
h,top,fold=parts('32139728')
assert 'class="dsbl"' in top
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'JBI 患病率清单：高' in fold or 'JBI 患病率清单总体高' in h
h,top,fold=parts('26581469')
assert 'class="dsbl"' in top
assert '无对应偏倚工具' not in h and '不适用（无公认工具）' not in fold
assert 'JBI 队列清单：高' in fold or 'JBI 队列清单总体高' in h
assert '证据确定性：中' in top
assert B.CERT['26581469']['certainty']=='中'
assert '间接性 降' not in fold and '间接性降' not in fold
assert not any('surrogate' in str(x).lower() or '间接' in str(x) for x in (B.CERT['26581469'].get('rules_applied') or []))

# 29314873 guideline chip; 31998612 certainty 极低 / ROBINS-I 严重
h,top,fold=parts('29314873')
assert '摘要未提及分级' in h
h,top,fold=parts('31998612')
assert '证据确定性：极低' in top
assert 'ROBINS-I 总体：严重' in fold or 'ROBINS-I 总体严重' in h
assert B.CERT['31998612']['certainty']=='极低'

# papers without deep speed-read data (and not otherwise edited) keep the old first screen
ctrl='24217707'
assert ctrl not in B.DS and ctrl not in APPROVED
h,top,fold=parts(ctrl)
assert '一句话结论' in top and '关键数字' in top and 'class="blk ds"' not in h

print('deep speed-read / fact-fix tests OK')
