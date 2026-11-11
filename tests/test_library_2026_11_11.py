"""Library additions 2026-11-11: 23078651 card_fields clinical_meaning; 43003998 cognition library; 43004944 infectious library."""
import os, sys, re, json
REPO=os.path.join(os.path.dirname(os.path.abspath(__file__)),'..'); sys.path.insert(0,REPO); os.chdir(REPO)
os.environ.setdefault('VETLIT_LIVE','1')
import build_preview as B

CM230='筛查出隐匿期 DCM 的杜宾犬，可开始用匹莫苯丹；出现心衰或猝死的中位时间从 441 天推迟到 718 天。'
CM944='犬猫肠道可携带产 ESBL 的肠杆菌（犬 8%、猫 3%）；犬猫肠杆菌感染应先做培养和药敏再选药。'
OLD230='延缓发病'
TITLE944='留尼汪岛犬 8%、猫 3% 携带 ESBL 肠杆菌'

assert B.CARD_FIELDS['23078651']['clinical_meaning']==CM230
assert B.CARD_FIELDS['43004944']['clinical_meaning']==CM944
assert B.CARD_FIELDS['43004944']['title_zh']==TITLE944
assert len(TITLE944)<=B.TITLE_ZH_MAX
assert not B.weekly_title_overlaps_conclusion(TITLE944, B.CARD_FIELDS['43004944']['one_line_conclusion_zh'])
assert not B.weekly_title_overlaps_conclusion(TITLE944, CM944)

# card_fields clinical_meaning only for the Vibe-approved set (20 papers)
cm_keys={k for k,v in B.CARD_FIELDS.items() if (v or {}).get('clinical_meaning')}
approved_cm={
    '23078651','43004944','30974015','32441826','32139728','20005753',
    '37167252','27143042','42043241','28965673','26265631','42977701',
    'x-international-renal-interest-society-2026-iris-staging-of-ckd-modified-2026',
    '43003998',
    '42800045','39831449','26581469','41701235','41781382','38884190',
}
assert cm_keys==approved_cm, cm_keys
# 15954557 stays as previously live text; not overlaid
assert '15954557' not in B.CARD_FIELDS or not (B.CARD_FIELDS.get('15954557') or {}).get('clinical_meaning')
p230=B.get('23078651') or B.get('pmid-23078651')
assert B.summ(p230)==CM230
assert CM230 in B.hcard(p230,'')
assert OLD230 not in B.summ(p230) and '匡莫苯丹' not in B.summ(p230)

home=open('dist/index.html',encoding='utf-8').read()
assert '本周无新增' in home and '最新抓取' not in home
# 23078651 最重要 card shows the new clinical meaning, not 延缓发病
assert CM230 in home
arts=re.findall(r'<article class="card">.*?</article>', home, re.S)
card230=next(a for a in arts if 'pmid-23078651' in a)
assert CM230 in card230 and OLD230 not in card230
ph230=open('dist/papers/pmid-23078651/index.html',encoding='utf-8').read()
assert OLD230 not in ph230
# no 延缓发病 on any 23078651 reader path (paper + bilingual if any)
for root,ds,fs in os.walk('dist/papers/pmid-23078651'):
    for f in fs:
        if f.endswith(('.html','.json','.xml')):
            s=open(os.path.join(root,f),encoding='utf-8').read()
            assert OLD230 not in s, (root,f)

# 43003998: cognition library only, not 本期新增, certainty 不适用
assert '43003998' not in B.DS_APPROVED
p398=B.get('43003998') or B.get('pmid-43003998')
assert p398 and p398.get('design_category')=='实验/基础研究'
assert p398.get('topics')==['cognition']
assert (B.CERT.get('43003998') or {}).get('certainty')=='不适用'
assert (B.CERT.get('43003998') or {}).get('weekly_new') is False
cog=open('dist/topics/cognition/index.html',encoding='utf-8').read()
assert '43003998' in cog
# not a 最重要 heading requirement; must appear in the topic library
assert 'pmid-43003998' in cog
inf=open('dist/topics/infectious/index.html',encoding='utf-8').read()
assert '43003998' not in inf
beh=open('dist/topics/behavior/index.html',encoding='utf-8').read()
# parent topic page may list children, but 43003998 must not be in behavior.all_ids library list as an auto-tag dump
# It should not appear on the behavior topic page because it was not added to behavior.all_ids
assert 'pmid-43003998' not in beh
# not in 本期新增
wn=re.search(r'id="weekly-new".*?</section>', home, re.S).group(0)
assert '43003998' not in wn and '43004944' not in wn
assert '本周无新增' in wn
ph398=open('dist/papers/pmid-43003998/index.html',encoding='utf-8').read()
assert '待处理' not in ph398
assert '起评' not in ph398 and '起点为' not in ph398
assert 'R-na-nonclinical' not in ph398 and '_internal' not in ph398
assert '不适用' in ph398
assert '<h1 class="ct">犬自我控制时额部出现类似人的 θ 波</h1>' in ph398
assert 'A human-like EEG signature of cognitive control in the domestic dog' in ph398
assert '目前没有直接的临床用途' in ph398
# ingest auto-tags must not appear
assert 'epidemiology' not in ph398

# 43004944: infectious library, rated 低, approved speed-read, Vibe clinical meaning + limitations
assert '43004944' in B.DS_APPROVED
p944=B.get('43004944') or B.get('pmid-43004944')
assert p944 and p944.get('topics')==['infectious']
assert p944.get('title_zh')==TITLE944
assert B.summ(p944)==CM944
assert (B.CERT.get('43004944') or {}).get('certainty')=='低'
assert (B.CERT.get('43004944') or {}).get('weekly_new') is False
assert '43004944' in inf and TITLE944 in inf
assert 'pmid-43004944' in inf
# topic / homepage 最新 cards show the card_fields clinical meaning
assert CM944 in inf and CM944 in home
ph944=open('dist/papers/pmid-43004944/index.html',encoding='utf-8').read()
assert f'<h1 class="ct">{TITLE944}</h1>' in ph944
assert '犬猫发生肠杆菌感染时，应先做细菌培养和药敏再选药' in ph944
assert '证据确定性：低' in ph944
assert '待处理' not in ph944
assert 'epidemiology' not in ph944 and '肥胖' not in ph944
assert '_internal' not in ph944 and 'R-start-prevalence' not in ph944 and 'R-rob-assessed' not in ph944
# rated paper may contain 起评 in the GRADE narrative
assert '从“高”起评' in ph944 or '从"高"起评' in ph944
# required limitations in the speed-read
assert '过拟合' in ph944
assert '绝育手术' in ph944
assert '摘要' in ph944 and ('抗生素' in ph944)
assert '0.304' in ph944 and '0.01–0.99' in ph944 or '0.01-0.99' in ph944
assert '2019–2020' in ph944 or '2019-2020' in ph944
assert '0.6%' in ph944 and '1.4%' in ph944
# homepage 最新 may list the new infectious paper, but not as 本期新增
# 43004944 should not have ingest topic chips other than 感染性疾病
assert '感染性疾病' in ph944

# neither paper is 待处理
assert p398.get('status')!='待处理' and p944.get('status')!='待处理'

print('library 2026-11-11 tests OK')
