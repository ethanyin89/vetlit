"""Approved clinical_meaning numbers (2026-11-11): only the Vibe allowlist is overlaid."""
import os, sys, re, html
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

IRIS='x-international-renal-interest-society-2026-iris-staging-of-ckd-modified-2026'
expected={
    '23078651':'筛查出隐匿期 DCM 的杜宾犬，可开始用匹莫苯丹；出现心衰或猝死的中位时间从 441 天推迟到 718 天。',
    '43004944':'犬猫肠道可携带产 ESBL 的肠杆菌（犬 8%、猫 3%）；犬猫肠杆菌感染应先做培养和药敏再选药。',
    '30974015':'杂音 ≥3/6、LA:Ao ≥1.6 且 LVIDDN ≥1.7（B2 期）的二尖瓣病犬，应开始用匹莫苯丹。',
    '32441826':'神经型 FIP 用 GS-441524 可能有效（4 只中 3 只停药后长期正常），但剂量可能需更高。',
    '32139728':'犬问题行为很常见：问卷中 72.5% 至少有一种高度问题行为，噪声敏感最多见（32%）。',
    '20005753':'老年犬认知障碍常被漏诊（问卷估计患病率 14.2%，兽医确诊仅 1.9%），值得主动询问。',
    '37167252':'有条件就首选放射碘（治愈率超过 95%）；用甲巯咪唑要低剂量起步并定期监测，避免甲减。',
    '27143042':'甲亢猫甲巯咪唑宜从 1.25–2.5 mg/只、每日两次起始，注意避免医源性甲减和肾功能恶化。',
    '42043241':'FIP 首选口服 GS-441524，42 天疗程可能已足够；不能口服的重症先用瑞德西韦。',
    '28965673':'杜宾犬 3 岁起每年做 Holter 和超声；24 小时室性早搏 >300 个即可诊断隐匿期 DCM。',
    '26265631':'户外活动受限和以干粮为主与 1 岁猫超重相关（主人报告超重或肥胖占 7.0%），这类猫需关注体重。',
    '42977701':'手术时长、术中低体温与乳腺切除术后感染相关；感染后先培养再选药。',
    IRIS:'CKD 犬 HCT <30% 或持续 30–35%、猫 <25% 或持续 25–28% 时考虑治疗贫血。',
    '43003998':'目前没有直接的临床用途；说明可以在清醒犬身上用脑电研究自我控制。',
}
assert len(expected['42977701'])<=60 and len(expected[IRIS])<=60
assert 'one_line_conclusion_zh' not in (B.CARD_FIELDS.get('43003998') or {})
assert B.CARD_FIELDS['43003998']['title_zh']=='犬自我控制时额部出现类似人的 θ 波'
assert len(B.CARD_FIELDS['43003998']['title_zh'])<=B.TITLE_ZH_MAX

for pmid, cm in expected.items():
    assert B.CARD_FIELDS[pmid]['clinical_meaning']==cm, pmid
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    assert p, pmid
    assert B.summ(p)==cm, (pmid, B.summ(p), cm)
    ti=p.get('title_zh') or ''
    if ti:
        assert len(ti)<=B.TITLE_ZH_MAX or pmid=='43003998' and len(ti)<=B.TITLE_ZH_MAX, (pmid,len(ti),ti)
        assert not B.weekly_title_overlaps_conclusion(ti, cm), (pmid,ti,cm)

# held papers keep their previously live card text
held={
    '42800045':'放射碘治疗的 1344 只猫中，持续未治疗的甲减与死亡风险升高相关；补充左甲状腺素的猫未见此关联。',
    '39831449':'117 只放射碘治疗猫中，无氮质血症的甲减猫补充 LT4 者生存更长；有氮质血症者未见差异。',
    '26581469':'日本约 6.5 万只参保猫中，消化系统疾病发病率最高，其次是泌尿和皮肤；多个纯种猫心血管病发病率高于混血。',
    '41701235':'CKD 犬蛋白尿更高，但研究偏倚大，尚不足以改变临床做法。',
    '41781382':'口服瑞德西韦可作为非积液型 FIP 的选择之一，但样本很小。',
    '38884190':'维格列净可替代胰岛素治疗新诊断糖尿病猫，但需筛查并监测酮症。',
    '15954557':'持续肾性蛋白尿应评估来源和程度，具体阈值以 IRIS 现行版为准。',
}
pending={
    '42800045':'放射碘治疗后的甲减猫，持续不治疗与死亡风险升高相关（HR 2.24），补左甲状腺素者未见此关联。',
    '39831449':'放射碘后无氮质血症的甲减猫，补 LT4 与更长中位生存相关（1037 天 vs 768 天）；有氮质血症者未见差异。',
    '26581469':'日本参保猫中消化系统疾病理赔发病率最高（1172/万猫年），其次是泌尿和皮肤；多个纯种猫心血管病发病率高于混血。',
    '41701235':'CKD 犬蛋白尿更高（UPC 的 SMD 0.85），但研究偏倚大，尚不足以改变临床做法。',
    '41781382':'口服瑞德西韦可作为非积液型 FIP 的选择（16 周存活并缓解 9/10 vs GS-441524 7/10），但每组仅 10 只。',
    '38884190':'维格列净可替代胰岛素治疗新诊断糖尿病猫（45 天成功率 54% vs 42%），但 4/61 发生 DKA，需筛查并监测酮症。',
}
for pmid, live in held.items():
    assert pmid not in B.CARD_FIELDS, pmid
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    assert p and B.summ(p)==live, (pmid, B.summ(p))
    if pmid in pending:
        assert pending[pmid] not in B.summ(p)

home=open('dist/index.html',encoding='utf-8').read()
assert '本周无新增' in home and '最新抓取' not in home
assert expected['23078651'] in home and '441' in home and '718' in home
assert html.escape(expected[IRIS]) in home
assert expected['42977701'] in home
assert '乳腺切除时控制手术时长、预防术中低体温' not in home
p398=open('dist/papers/pmid-43003998/index.html',encoding='utf-8').read()
assert '<h1 class="ct">犬自我控制时额部出现类似人的 θ 波</h1>' in p398
assert expected['43003998'] in p398
assert B.top_titles_over_limit()==[]

print('clinical_meaning numbers 2026-11-11 tests OK')
