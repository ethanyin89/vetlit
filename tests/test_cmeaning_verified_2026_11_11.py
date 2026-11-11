"""Verified clinical_meaning overlay (2026-11-11) for the six previously held papers."""
import os, sys, html
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

expected={
    '42800045':'放射碘后持续未治疗的甲减与死亡风险升高相关（HR 2.24），补左甲状腺素的猫无显著差异。',
    '39831449':'放射碘后无氮质血症的甲减猫，补 LT4 与更长中位生存相关（补 1037 天、未补 768 天）；氮质血症猫无差异。',
    '26581469':'日本参保猫中消化系统疾病理赔发病率最高（1172/万猫年），其次是泌尿和皮肤疾病。',
    '41701235':'CKD 犬 UPC 高于健康犬（SMD 0.85），但异质性大、有发表偏倚，尚不足以改变做法。',
    '41781382':'瑞德西韦对 GS-441524 达非劣效：16 周缓解瑞德西韦 9/10、GS 7/10，差异不显著，每组 10 只。',
    '38884190':'维格列净对胰岛素达非劣效：45 天成功率维格列净 54%、胰岛素 42%；维格列净 4/61 发生 DKA。',
}
for pmid, cm in expected.items():
    assert B.CARD_FIELDS[pmid]=={'clinical_meaning':cm}, pmid
    assert len(cm)<=60, (pmid,len(cm))
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    assert p and B.summ(p)==cm, (pmid, B.summ(p), cm)
    ti=p.get('title_zh') or ''
    assert ti, pmid
    assert not B.weekly_title_overlaps_conclusion(ti, cm), (pmid,ti,cm)

# 15954557 unchanged
assert '15954557' not in B.CARD_FIELDS
p=B.matcher({'pmid':'15954557','id':'15954557'}) or B.get('15954557')
assert B.summ(p)=='持续肾性蛋白尿应评估来源和程度，具体阈值以 IRIS 现行版为准。'

home=open('dist/index.html',encoding='utf-8').read()
assert '本周无新增' in home and '最新抓取' not in home
# at least some of the six appear with new text on live pages
n_on_home=sum(1 for cm in expected.values() if cm in home or html.escape(cm) in home)
assert n_on_home>=2, n_on_home
assert B.top_titles_over_limit()==[]
print('clinical_meaning verified 2026-11-11 tests OK')
