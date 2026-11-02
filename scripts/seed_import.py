"""Import canonical paper data (Vibe Feline seed_library_v3.json, 25 fields) + site extension fields -> data/papers/<id>.json.
Canonical field names are Vibe Feline's (see schema.md). Records are keyed/merged by PMID.
Usage: python3 scripts/seed_import.py [/workspace/vetlit/seed_library_v3.json]"""
import json, os, sys, re
SRC = sys.argv[1] if len(sys.argv) > 1 else '/workspace/vetlit/seed_library_v3.json'
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'papers')
def pid(r): return 'pmid-'+r['pmid'] if r.get('pmid') else 'x-'+re.sub(r'[^a-z0-9]+','-',(r['first_author']+'-'+r['year']+'-'+r['title'][:40]).lower()).strip('-')
papers = {}
for r in json.load(open(SRC, encoding='utf-8-sig')):
    papers[pid(r)] = {'id': pid(r), **r, 'status': '已收录', 'provenance': ['vibe-feline-v3']}
def merge(pmid, **kw):
    k='pmid-'+pmid; p=papers.setdefault(k, {'id':k,'pmid':pmid,'provenance':[]})
    p.update(kw); p['provenance']=list(dict.fromkeys(p.get('provenance',[])+['site-curated']))
# ---- site extension fields for papers with detail pages ----
merge('30948740', title_zh='家猫能把自己的名字与其他词区分开', pmcid='PMC6449508', date='2019-04-04', detail='saito_2019.md', status='已处理',
      errata_detail=[{'type':'更正','doi':'10.1038/s41598-019-46257-x','date':'2019-09','note':'仅改年龄、家庭数等笔误，结论不变'}])
# Sent 2015: deep-extract extension fields
merge('26474314', clinical_utility='提示性',
      detail='sent_2015.md', status='已处理', errata_detail=[{'type':'更正','pmid':'27003463','note':'J Vet Intern Med 2016;30(2):689，补 Table 2 漏印数字，不影响结论'}],
      internal_inconsistency_detail=['Table 3 贝那普利 Day 7/30/60 P=.040/.023/.046 单看显著，但正文称各时点均不显著——仅按 Bonferroni–Holm 逐步阈值解读才成立','正文称 4 只 IRIS 4 期猫，Table 2 显示 3+2=5 只'])
merge('30353952', specialty='肾脏/心脏', detail='acierno_2018.md', status='已处理',
      recommendation_basis_detail='急症处理推荐原文自述为 anecdotal and extrapolated；测压设备无一在清醒犬猫中达到验证标准')
merge('27678080', detail='boswood_2016.md', status='已处理')
merge('29660848', detail='fox_2018.md', status='已处理', errata_detail=[{'type':'勘误','pmid':'30417429','note':'HCM 中 CHF 不伴 ATE 的 90 只猫中位发生时间为 857 天而非 57 天；心血管生存范围应为 3 天–13.1 年（原文误为 3.1 年）'}])
# ---- 6 canvas-prototype papers not in Vibe Feline's 57 (PubMed-verified bibliographic data; evidence appraisal 待评) ----
def proto(pmid, **kw): merge(pmid, source='PubMed', verified='partial', japan_source='否', errata='', internal_inconsistency='', status='待处理', **kw)
proto('41964608', title='Investigation and systematic review of temporal associations between vaccination and onset of immune-mediated hemolytic anemia or thrombocytopenia in dogs', title_zh='疫苗接种与犬 IMHA/ITP 发病时间关联：调查与系统综述', first_author='Neale V', year='2026', date='2026-03-02', journal='J Vet Intern Med', doi='10.1093/jvimsj/aalag057', pmcid='PMC13069898', species='犬', specialty='内科/免疫', oa='是', doc_type='系统综述', recommendation_basis='不适用', sample_size_analysed='未核', multicenter='未核', funding='未核', clinical_utility='提示性')
proto('41742497', title='ACVIM-endorsed statement: consensus statement and systematic review on guidelines for the diagnosis and treatment of chronic inflammatory enteropathy in dogs', title_zh='ACVIM 共识：犬慢性炎症性肠病诊疗指南（含系统综述）', first_author='Heilmann RM', year='2026', date='2026-01-21', journal='J Vet Intern Med', doi='10.1093/jvimsj/aalaf017', pmcid='PMC12881957', species='犬', specialty='消化', oa='是', doc_type='指南/共识', recommendation_basis='未核', sample_size_analysed='不适用', multicenter='不适用', funding='未核', clinical_utility='改变诊疗')
proto('40911440', title='Iron-Limited Erythropoiesis in Dogs and Cats: A Systematic Review and Meta-Analysis of Current Evidence Examining Mean Corpuscular Volume, Mean Reticulocyte Volume, and Reticulocyte Hemoglobin Content', title_zh='犬猫缺铁性红细胞生成：MCV、MCVr、CHr 的系统综述与 Meta 分析', first_author='Ahmadi-Hamedani M', year='2025', date='2025-09', journal='J Vet Intern Med', doi='10.1111/jvim.70239', pmcid='PMC12412556', species='猫/犬', specialty='血液', oa='是', doc_type='系统综述', recommendation_basis='不适用', sample_size_analysed='不适用', multicenter='不适用', funding='未核', clinical_utility='提示性')
proto('42600645', title='Medetomidine-vatinoxan (Zenalpha) results in reduction of systolic function, blood pressure, and heart rate with prolongation of electrocardiographic intervals in healthy dogs', title_zh='美托咪定-瓦替诺散（Zenalpha）降低健康犬收缩功能、血压与心率并延长心电间期', first_author='Forsyth KK', year='2026', date='2026-11-01', journal='J Am Vet Med Assoc', doi='10.2460/javma.26.03.0210', species='犬', specialty='麻醉', oa='否', doc_type='原始研究', recommendation_basis='不适用', sample_size_analysed='21（摘要）', multicenter='未核', funding='未核', clinical_utility='提示性')
proto('42908201', title='Mineral Analysis of Feline Treats: Unrecognized Sources of Phosphorus and Calcium in the Management of Chronic Kidney Disease', title_zh='猫零食矿物质分析：CKD 管理中被忽视的磷与钙来源', first_author='Harris AN', year='2026', date='2026-10-21', journal='J Feline Med Surg', doi='10.1177/1098612x261500321', species='猫', specialty='肾脏/营养', oa='未核', doc_type='产品检测', recommendation_basis='不适用', sample_size_analysed='不适用（无动物受试）', multicenter='不适用', funding='未核', clinical_utility='背景')
proto('42934851', title='Benefits of contrast-enhanced computed tomography over plain computed tomography for head trauma in 41 cats', title_zh='增强 CT 相较平扫 CT 用于 41 只猫头部外伤的价值', first_author='Mariaud V', year='2026', date='2026-10-26', journal='J Feline Med Surg', doi='10.1177/1098612x261502912', species='猫', specialty='影像/急诊', oa='未核', doc_type='原始研究', recommendation_basis='不适用', sample_size_analysed='41（题名）', multicenter='未核', funding='未核', clinical_utility='提示性')
LEG={'evidence_grade','grade_v1','grade_reason','downgrade_tags'}
for p in papers.values(): p={k:v for k,v in p.items() if k not in LEG}; p={k:v for k,v in p.items() if v is not None}; json.dump(p, open(os.path.join(OUT, p['id']+'.json'),'w'), ensure_ascii=False, indent=2)
print(len(papers), 'papers written')
