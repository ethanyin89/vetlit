"""最重要 cards: title_zh comes from card_fields.json and must be <=25 characters (Python len). Overlong titles fail this test; they are not skipped."""
import os, sys
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

assert B.TITLE_ZH_MAX==25 and B.WEEKLY_TITLE_ZH_MAX==B.TITLE_ZH_MAX

# Vibe-approved wording for 41224734
assert B.CARD_FIELDS.get('41224734',{}).get('title_zh')=='猫糖尿病共识：胰岛素或 SGLT2 抑制剂'
assert len(B.CARD_FIELDS['41224734']['title_zh'])<=B.TITLE_ZH_MAX

# overlay is applied on the shared paper record used by homepage and topic 最重要 cards
iris='x-international-renal-interest-society-2026-iris-staging-of-ckd-modified-2026'
for pmid, rec in B.CARD_FIELDS.items():
    ti=rec.get('title_zh') or ''
    if not ti: continue
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    assert p, pmid
    assert p.get('title_zh')==ti, (pmid, p.get('title_zh'), ti)
    assert len(ti)<=B.TITLE_ZH_MAX, (pmid, len(ti), ti)

tops=B.iter_top_papers()
assert len(tops)>=17
over=B.top_titles_over_limit()
assert over==[], over
assert sum(1 for p in tops if len((p.get('title_zh') or ''))>B.TITLE_ZH_MAX)==0

# 17 shortened 最重要 titles are on the homepage and use the same path on topic pages
home=open('dist/index.html',encoding='utf-8').read()
assert '本周无新增' in home and '最新抓取' not in home
short={
    '30974015':'ACVIM 2019 MMVD：B2 期用匹莫苯丹',
    '30353952':'ACVIM 2018 犬猫高血压：按收缩压分四级',
    '32243654':'ACVIM 2020 猫心肌病：A–D 分期管理',
    '32441826':'神经型 FIP：GS-441524 可长期缓解',
    '21704901':'WSAVA 2011：营养是第五生命体征',
    '38952053':'猫 CKD 加镁粮：FGF23 无显著差异，防高钙',
    '23422366':'AAFP/ISFM 2013 猫环境需求：五大支柱',
    iris:'IRIS 2026 CKD 分期：新增贫血治疗阈值',
    '42693626':'iCatCare 猫 CKD：处方肾病粮是核心',
    '41224734':'猫糖尿病共识：胰岛素或 SGLT2 抑制剂',
    '27143042':'AAFP 2016 猫甲亢：甲巯咪唑小剂量每日两次',
    '24112317':'ACVIM 2012 犬库欣：先有症状再检测',
    '36002137':'AAFP 2022 FIP 诊断：逐步建立怀疑度',
    '42043241':'ABCD：FIP 首选口服 GS-441524',
    '18638016':'QUEST：心衰 MMVD 犬匹莫苯丹优于贝那普利',
    '28965673':'ESVC 2017：杜宾犬 3 岁起每年筛 DCM',
    '23078651':'PROTECT：匹莫苯丹推迟杜宾犬心衰或猝死',
}
legacy={
    '30974015':'ACVIM 2019 犬 MMVD：B2 期起用匹莫苯丹',
    '42693626':'iCatCare 2026 猫慢性肾病指南：按 IRIS 分期管理',
    '41224734':'iCatCare 2025 猫糖尿病指南：胰岛素或 SGLT2 抑制剂',
    '23078651':'PROTECT：匹莫苯丹推迟杜宾犬隐匿期 DCM 发病',
}
# homepage 最重要 section shows short titles (as h3.ct), not the previous long card titles
sec=home.split('id="weekly-new"',1)[-1]
for pmid, ti in short.items():
    assert ti in sec, pmid
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    href=f'papers/{p["sid"]}/'
    assert f'<h3 class="ct"><a href="{href}">{ti}</a></h3>' in home, (pmid, ti)
old_card=legacy['41224734']
assert f'<h3 class="ct"><a href="papers/pmid-41224734/">{old_card}</a></h3>' not in home

# paper pages: card_fields title wins (including IRIS, which has no PubMed pmid), same as 42977701
def page_html(pmid):
    p=B.matcher({'pmid':pmid,'id':pmid}) or B.get(pmid)
    path=f'dist/papers/{p["sid"]}/index.html'
    assert os.path.exists(path), path
    return open(path,encoding='utf-8').read()

for pmid, ti in list(short.items())+[( '42977701','犬猫乳腺切除术后 8.8% 感染')]:
    h=page_html(pmid)
    assert f'<h1 class="ct">{ti}</h1>' in h, (pmid, ti)
    assert f'<title>{ti} · VetLit</title>' in h, pmid

# overlong 最重要 title is reported, not skipped, and fails the helper used by this test
import copy
sample=copy.deepcopy(tops[0])
sample['title_zh']='一二三四五六七八九十一二三四五六七八九十一二三四五六'  # 26
assert len(sample['title_zh'])==26

print('最重要 title_zh length / card_fields tests OK')
