"""Preview build (redesign, cindy.app tokens): data/v5 + data/papers + content -> dist/preview/. Root site untouched."""
import json, os, glob, re, html, datetime, shutil
import build as B
import preview_extras as X
ROOT=B.ROOT; LIVE=os.environ.get('VETLIT_LIVE')=='1'; OUT=B.DIST if LIVE else os.path.join(B.DIST,'preview'); E_=html.escape
def clean(s):
    s=str(s or '')
    s=re.sub(r'[。；，]?\s*(数据)?来源[:：]\s*(deep extract|Vibe Feline|vibe-feline)[^。；|\n]*','',s,flags=re.I)
    s=re.sub(r'[（(]\s*(?:Vibe|deep extract)[^（）()]*[）)]','',s,flags=re.I)
    s=re.sub(r'[，,；]?\s*(?:Vibe Feline|deep extract|Vibe)\s*(?:\d{4}-\d{2}-\d{2}\s*)?(?:裁定|更正|决定)','',s,flags=re.I)
    s=re.sub(r'(deep extract|Vibe Feline|vibe-feline-v\d)','AI 速读',s,flags=re.I)
    s=re.sub(r'(?:按\s*)?Vibe\s*(?:\d{4}-\d{2}-\d{2}\s*)?(?:裁定|更正|决定)?(?:\s*\d{4}-\d{2}-\d{2})?','',s)
    s=re.sub(r'原按[^。]*?属归类错误[^。]*。','',s)   # curation-history notes are not reader content
    s=re.sub(r'([。，；：！？、])\1+',r'\1',s)
    return s.replace('。）','）').strip()
EMPTY={'','未核','不适用','—','-','None'}
def has(v): return v not in (None,[],{}) and str(v).strip() not in EMPTY
STAMP=os.path.join(ROOT,'data','v5','home_stamp.json')
def home_stamp(picks):
    """Date shown on the home hero. Changes ONLY when the home pick lists (topic -> ids) change: hash differs -> today (America/New_York), saved to data/v5/home_stamp.json."""
    import hashlib, zoneinfo
    h=hashlib.sha256(json.dumps(picks,ensure_ascii=False,sort_keys=True).encode()).hexdigest()
    st=json.load(open(STAMP,encoding='utf-8')) if os.path.exists(STAMP) else {}
    if st.get('hash')!=h:
        st={'hash':h,'date':datetime.datetime.now(zoneinfo.ZoneInfo('America/New_York')).date().isoformat()}
        json.dump(st,open(STAMP,'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    return st['date']
# ---------- data ----------
v5=json.load(open(os.path.join(ROOT,'data','v5','seed_library_v6.json'),encoding='utf-8'))
TP=json.load(open(os.path.join(ROOT,'data','v5','topics_pages.json'),encoding='utf-8'))['topics']
cur={}
for f in glob.glob(os.path.join(ROOT,'data','papers','*.json')):
    c=json.load(open(f,encoding='utf-8')); cur[c['id']]=c
bypmid={c.get('pmid'):c for c in cur.values() if c.get('pmid')}
P={}; FRESH=[]
for r in v5:
    base=bypmid.get(r.get('pmid')) or cur.get(r['id']) or cur.get('pmid-'+r['id']) or {}
    p=dict(base); p.update({k:v for k,v in r.items() if v not in (None,)})
    p['sid']=base.get('id') or ('pmid-'+r['pmid'] if r.get('pmid') else r['id'])
    p['v5id']=r['id']; P[r['id']]=p
for c in cur.values():
    if 'ingest' in (c.get('provenance') or []) and c['id'] not in {p['sid'] for p in P.values()}:
        c=dict(c); c['sid']=c['id']; c['fresh']=True; FRESH.append(c)
SID={p['sid']:p for p in P.values()}
def ndoi(d): return re.sub(r'^(https?://(dx\.)?doi\.org/|doi:)','',str(d or '').strip().lower())
def idx(recs):
    out=[]
    for r in recs: out.append(r)
    return out
def matcher(r):
    for p in P.values():
        if r.get('pmid') and str(p.get('pmid') or '')==str(r['pmid']): return p
    for p in P.values():
        if r.get('doi') and ndoi(p.get('doi'))==ndoi(r['doi']): return p
    return P.get(r.get('id')) or SID.get(r.get('id'))
STRIP=lambda x: re.sub(r'\*\*','',x) if isinstance(x,str) else x
MERGE={'sr':0,'sr_un':[],'ap':0,'ap_un':[]}
for r in json.load(open(os.path.join(ROOT,'data','v5','speedread_fields_v5.json'),encoding='utf-8')):
    p=matcher(r)
    if not p: MERGE['sr_un'].append(r.get('pmid') or r.get('id')); continue
    MERGE['sr']+=1
    for k in ('title_zh','one_line_conclusion_zh','confidence_sentence','why_it_matters'):
        p[k]=STRIP(r.get(k) or '')
    p['key_results']=r.get('key_results') or []
    if has(r.get('clinical_meaning')): p['clinical_meaning']=STRIP(r['clinical_meaning'])
    if isinstance(r.get('key_results_top3'),list): p['key_results_top3']=r['key_results_top3']
DS={}
_apf=os.path.join(ROOT,'data','v5','deep_speedread_approved.json')
DS_APPROVED=set(str(x) for x in json.load(open(_apf,encoding='utf-8'))['approved']) if os.path.exists(_apf) else set()
# Rendering is driven only by DS_APPROVED, never by mere presence in batch1.json / deep_speedread.json.
_dsf=os.path.join(ROOT,'data','v5','deep_speedread.json')
if os.path.exists(_dsf):
    _raw=json.load(open(_dsf,encoding='utf-8'))
    for _r in (_raw.get('papers') if isinstance(_raw,dict) else _raw) or []:
        if isinstance(_r,dict) and _r.get('pmid') and str(_r['pmid']) in DS_APPROVED:
            DS[str(_r['pmid'])]=_r
def ds_of(p):
    """Reader-facing deep speed-read record, or None if not on the explicit approved list."""
    k=str(p.get('pmid') or '')
    if k not in DS_APPROVED: return None
    r=DS.get(k)
    if not r or not (r.get('sections') and r.get('section_order')): return None
    return r
for r in json.load(open(os.path.join(ROOT,'data','v5','appraisal_papers.json'),encoding='utf-8')):
    p=matcher(r)
    if not p: MERGE['ap_un'].append(r.get('pmid') or r.get('id')); continue
    MERGE['ap']+=1
    p['v6_tool']=p.get('rob_tool') or ''; p['v6_judg']=p.get('rob_judgement') or ''; p['rob_tool']=r.get('appraisal_tool') or p.get('rob_tool') or ''; p['appraisal_items']=r.get('appraisal_items') or []
    p['appraisal_note']=r.get('appraisal_note') or ''
    for k in ('funder','study_card','cebm_basis'):
        if r.get(k) and not p.get(k): p[k]=r[k]
    if r.get('cebm_basis') and 'cebm_fill' in str(r['cebm_basis']) and str(r.get('cebm_level'))!=str(p.get('cebm_level')): p['cebm_level']=r['cebm_level']; p['cebm_basis']=r['cebm_basis']  # source corrected by Vibe
    for k in ('rob_judgement','rob_rationale'): p.pop(k,None)
MERGE['pg']=0; MERGE['pg_un']=[]
for k,r in json.load(open(os.path.join(ROOT,'data','v5','pages38_fields.json'),encoding='utf-8')).items():
    r.setdefault('pmid',k); p=matcher(r)
    if not p: MERGE['pg_un'].append(k); continue
    MERGE['pg']+=1
    p['can_say']=[STRIP(x) for x in r.get('can_say') or []]; p['cannot_say']=[STRIP(x) for x in r.get('cannot_say') or []]
    f='extracts38/'+os.path.basename(r.get('page_file') or k+'.md')
    if os.path.exists(os.path.join(ROOT,'content',f)):
        p['detail']=f; p['p38']=True
        m=re.search(r'`已读(全文|摘要)`',open(os.path.join(ROOT,'content',f),encoding='utf-8').read())
        if m: p['reading_depth']=m.group(1)
    if not p.get('reading_depth'): p['reading_depth']='摘要'
ADJ={}
for r in json.load(open(os.path.join(ROOT,'data','v5','adjudicated_rob_rct.json'),encoding='utf-8')): ADJ.setdefault(r['pmid'],[]).append(r)
JM={'L':'低','S':'有一定担忧','H':'高'}
DN={'D1':'D1 随机化过程','D2':'D2 偏离既定干预','D3':'D3 结局数据缺失','D4':'D4 结局测量','D5':'D5 结果选择性报告'}
MERGE['adj']=0; MERGE['adj_un']=[]
for pm,rs in ADJ.items():
    p=matcher({'pmid':pm})
    if not p: MERGE['adj_un'].append(pm); continue
    MERGE['adj']+=1; p['rob_tool']='RoB 2'; p['adj']=True; p['adj_dual']=True; p['appraisal_note']=''
    items=[]
    for r in sorted(rs,key=lambda r:(r['domain']=='overall',r['domain'])):
        if r['domain']=='overall': p['adj_overall']=JM.get(r['final'],r['final']); p['adj_overall_reason']=r.get('rationale') or ''; continue
        rea=(f'原文位置：{r["location"]}' if r.get('location') else '')
        if r['domain']=='D5': rea='未检索到预先注册的方案。'+rea
        items.append({'item':DN.get(r['domain'],r['domain']),'judgment':JM.get(r['final'],r['final']),'reason':rea,'evidence_quote':r.get('quote') or ''})
    p['appraisal_items']=items
CERT=json.load(open(os.path.join(ROOT,'data','v5','certainty.json'),encoding='utf-8')).get('papers',{}) if os.path.exists(os.path.join(ROOT,'data','v5','certainty.json')) else {}
for r in json.load(open(os.path.join(ROOT,'data','v5','selfcheck_adjudication.json'),encoding='utf-8'))['rulings']:
    if r['ruling']!='accept' or r['source_type']!='abstract' or r['pmid'] in ADJ: continue
    _ov=str((CERT.get(str(r['pmid'])) or {}).get('rob_overall') or '')
    if _ov and not _ov.startswith('未评'): continue  # completed full-text assessment supersedes abstract-only selfcheck
    p=matcher({'pmid':r['pmid']})
    if not p: MERGE['adj_un'].append(r['pmid']); continue
    MERGE['adj']+=1; p['rob_tool']='RoB 2'; p['adj']=True; p['appraisal_note']=''; p['adj_overall']='未完整评估（仅据摘要；D1 有一定担忧，其余领域未评）'
    p['appraisal_items']=[{'item':DN[r['domain']],'judgment':JM[r['final']],'reason':'仅据摘要。原文位置：摘要','evidence_quote':r['quote']}]
DN3={'patient_selection_rob':'患者选择 · 偏倚风险','patient_selection_applicability':'患者选择 · 适用性','index_test_rob':'待评价试验 · 偏倚风险','index_test_applicability':'待评价试验 · 适用性','reference_standard_rob':'参考标准 · 偏倚风险','reference_standard_applicability':'参考标准 · 适用性','flow_and_timing_rob':'病例流程与时间 · 偏倚风险',
 'study_participation':'研究参与','study_attrition':'研究失访','prognostic_factor_measurement':'预后因素测量','outcome_measurement':'结局测量','study_confounding':'混杂','statistical_analysis_reporting':'统计分析与报告'}
MERGE['rob3']=0
for pm,r in json.load(open(os.path.join(ROOT,'data','v5','rob_adjudicated_r3.json'),encoding='utf-8')).items():
    p=matcher({'pmid':pm})
    if not p: MERGE['adj_un'].append(pm); continue
    MERGE['rob3']+=1; p['rob_tool']=r['tool']; p['adj']=True; p['adj_dual']=True; p['rob3']=True; p['appraisal_note']=''
    p['adj_overall']=r['overall_final']; p['rob_rule']=r.get('overall_rule_zh') if r['tool']=='QUIPS' else ''
    p['appraisal_items']=[{'item':DN3.get(k,k),'judgment':v.get('final') or '','reason':(v.get('rationale_zh') or '')+(f' 原文位置：{v["location"]}' if v.get('location') else ''),'evidence_quote':v.get('quote') or ''} for k,v in r['domains'].items()]
MERGE['gs']=0; MERGE['gs_un']=[]
for r in json.load(open(os.path.join(ROOT,'data','v5','guideline_strength.json'),encoding='utf-8')):
    p=matcher({'pmid':r['pmid'],'id':r['pmid']}) if r['pmid'] else next((x for x in P.values() if 'iris' in str(x.get('sid','')).lower() and 'staging' in str(x.get('sid','')).lower()),None)
    if not p: MERGE['gs_un'].append(r['guideline']); continue
    MERGE['gs']+=1; p['gs']=r
MERGE['cebm']=0
_CF=json.load(open(os.path.join(ROOT,'data','v5','cebm_fill.json'),encoding='utf-8'))
_CFR=dict(_CF.get('records',{})); _CFR.update({k:v for k,v in _CF.items() if k.isdigit() and isinstance(v,dict) and v.get('cebm_level')})
for k,r in _CFR.items():
    p=matcher({'pmid':k,'id':k})
    if not p: continue
    MERGE['cebm']+=1; p['cebm_level']=r['cebm_level']
    p['appraisal_note']=re.sub(r'CEBM 等级未核',f'CEBM 等级 {r["cebm_level"]}',p.get('appraisal_note') or '')
MERGE['cebm_r2']=0
for k,r in json.load(open(os.path.join(ROOT,'data','v5','cebm_fill_r2.json'),encoding='utf-8'))['records'].items():
    p=matcher({'pmid':k,'id':k})
    if not p: continue
    MERGE['cebm_r2']+=1
    if r.get('cebm_level_v6'): p['cebm_level']=r['cebm_level_v6']
    if r.get('cebm_basis'): p['cebm_basis']=r['cebm_basis']
MERGE['ovr']=0
for k,r in json.load(open(os.path.join(ROOT,'data','v5','overrides.json'),encoding='utf-8')).items():
    if k.startswith('_'): continue
    p=matcher({'pmid':k,'id':k})
    if not p: continue
    MERGE['ovr']+=1; p.update(r)
MERGE['amstar']=0
AM=json.load(open(os.path.join(ROOT,'data','v5','amstar2_adjudicated.json'),encoding='utf-8'))
JA={'Yes':'是','Partial Yes':'部分是','No':'否'}; OA={'Critically low':'极低','Low':'低','Moderate':'中','High':'高'}
for k,r in AM['records'].items():
    p=matcher({'pmid':k,'id':k})
    if not p: continue
    MERGE['amstar']+=1; p['rob_tool']='AMSTAR 2'; p['amstar']=True; p['amstar_blind']=(r.get('second_assessor_blinded',AM.get('second_assessor_blinded')) is True); p['appraisal_note']=''; p['rep_inc']=r.get('reporting_inconsistencies') or []
    p['amstar_overall']=f'AMSTAR 2 总体：{OA.get(r["final_overall"],r["final_overall"])}（关键缺陷：第 {"、".join(map(str,r["critical_flaws"]))} 项）'
    p['appraisal_items']=[{'item':f'第 {n} 项'+('（关键）' if int(n) in AM['critical_items'] else ''),'judgment':JA.get(i['final'],i['final']),'reason':re.sub(r'^(核对全文后同意第一评估员：|维持 No。)','',i.get('reason') or '')+(f'（{i["location"]}）' if i.get('location') else ''),'evidence_quote':i.get('quote') or ''} for n,i in r['items'].items()]
    if r.get('search_date_inconsistency'): p['amstar_limit']='检索日期前后矛盾（表 1：2025-03-03；局限性一节：2025-04-04）'
HOLD=set(); MERGE['ckd2']=0
_se=json.load(open(os.path.join(ROOT,'data','v5','second_extractor_ckd.json'),encoding='utf-8'))
_se=_se.get('papers',_se) if isinstance(_se,dict) else _se
for r in (_se if isinstance(_se,list) else _se.values()):
    p=matcher({'pmid':r['pmid'],'id':r['pmid']}) if r.get('pmid') else next((x for x in P.values() if 'iris' in str(x.get('sid','')).lower() and 'staging' in str(x.get('sid','')).lower()),None)
    if not p: continue
    MERGE['ckd2']+=1
    if str(r.get('pmid')) not in HOLD: p['dual_x']='abs' if str(r.get('evidence_basis','')).startswith('abstract') else 'ft'
for c in json.load(open(os.path.join(ROOT,'data','v5','ckd_conclusion_checks.json'),encoding='utf-8'))['checks']:
    p=matcher({'pmid':c['pmid'],'id':c['pmid']})
    if not p: continue
    p['one_line_conclusion_zh']=c['proposed_zh']; p['confidence_sentence']=''
    if c.get('key_results_fix'):
        for kr in p.get('key_results') or []:
            if '检测 GFR 初始下降' in str(kr.get('measure','')): kr['measure']='SDMA 两种判读方法比较'; kr['groups']=c['key_results_fix']; kr['effect_ci']=''; kr['p']=''
        p['limits']=['8 只 X 连锁遗传性肾病公犬','GFR 下降<20% 为平均值','≥14 μg/dL 界值在一只健康同窝犬多次超出，改用 ≥16 μg/dL 仍平均早 3.4 周']
NOVR={'25231385':('42（CKD 21 + 健康对照 21）',None),'27103204':('39（CKD 19 + 健康对照 20）',None),'26079532':('12（患病 8 + 未患病同窝 4）',None),'26474314':('224（随机）','72/76（第 180 天）')}
for k,(e,a) in NOVR.items():
    p=matcher({'pmid':k,'id':k})
    if p: p['n_enrolled']=e; p['n_analysed']=a or ''
for k in HOLD:
    p=matcher({'pmid':k,'id':k})
    if p: p['one_line_conclusion_zh']=''; p['confidence_sentence']=''
for p in P.values():
    for kr in p.get('key_results') or []:
        if isinstance(kr,dict) and str(p.get('pmid'))=='39417648':
            for f in kr:
                if isinstance(kr[f],str): kr[f]=kr[f].replace('4/15（27%）','4/15（26%）')
MF=os.path.join(ROOT,'data','v5','methods_fields.json'); MERGE['mf']=0; MERGE['mf_un']=[]
if os.path.exists(MF):
    mf=json.load(open(MF,encoding='utf-8')); mf=list(mf.values()) if isinstance(mf,dict) else mf
    for r in mf:
        p=matcher(r)
        if not p: MERGE['mf_un'].append(r.get('pmid') or r.get('id')); continue
        MERGE['mf']+=1; p['methods']=r.get('动物来源与实验处理') or {}; p['pop']=r.get('population') or {}; p['slots']=r.get('methods_slots') or {}
MERGE['pn']=0
for k,v in json.load(open(os.path.join(ROOT,'data','v5','population_notes.json'),encoding='utf-8')).items():
    p=matcher({'pmid':k,'id':k})
    if p: p['pop_note']=v; MERGE['pn']+=1
MERGE['ur']=0
for k,v in json.load(open(os.path.join(ROOT,'data','v5','unverified_resolution.json'),encoding='utf-8')).items():
    p=matcher({'pmid':v.get('pmid'),'doi':v.get('doi'),'id':v.get('id')})
    if not p: continue
    MERGE['ur']+=1; res={}
    for f,x in (v.get('resolution') or {}).items():
        if x.get('value'): res[f]=(x['value'],x.get('evidence_quote') or '')
        elif str(x.get('status','')).startswith('未解决'): res[f]=('摘要未提及','')
        else: res[f]=('原文未报告','')
    p['res']=res
# hidden pending verification
HIDE_KR=set()
for p in P.values():
    for k in p.get('key_results') or []:
        if str(p.get('pmid'))=='23078651' and k.get('measure')=='到达主要终点比例': k['groups']='匹莫苯丹 19/39；安慰剂 25/37（据原文表格推算）'
    p['key_results']=[k for k in (p.get('key_results') or []) if (str(p.get('pmid')),k.get('measure')) not in HIDE_KR]
def get(i): return P.get(i) or SID.get(i) or SID.get('pmid-'+str(i))
SPEC={'肾脏':'肾脏','心脏':'心脏','感染':'感染','行为/认知':'行为与认知','营养':'营养','内分泌':'内分泌','皮肤':'皮肤'}
def specs(p): return [SPEC[x] for x in re.split(r'[/;；]',p.get('specialty') or '') if x.strip() in SPEC]
def species(p):
    s=p.get('species_zh') or p.get('species') or ''
    return {'cat':'猫','dog':'犬','cat+dog':'猫/犬'}.get(s,s)
def level(p):
    l=str(p.get('cebm_level') or '')
    if re.match(r'^[1-5]',l): return 'Level '+l[0]
    if p.get('design_category')=='指南/共识': return '指南/共识'
    return '未分级'
ROB={'Some concerns':'有一定担忧','Moderate（QUIPS 综合，非官方总分）':'中等（QUIPS）'}
DEPTH={'全文':'已读全文','摘要':'已读摘要','仅标题':'仅题录'}
def badges(p):
    b=[('k',p.get('design_category'))]
    n=p.get('n_analysed')
    if has(n) and len(str(n))<=14: b.append(('',f'n={n}'))
    if level(p).startswith('Level'): b.append(('lv','CEBM '+level(p)))
    return '<p class="bd">'+''.join(f'<span class="b {c}">{E_(str(t))}</span>' for c,t in b if t)+'</p>'
SHOW_CERTAINTY=os.environ.get('SHOW_CERTAINTY','true').lower() in ('1','true','yes')
_CJ=os.path.join(ROOT,'data','v5','certainty.json')
if 'CERT' not in globals():
    CERT=json.load(open(_CJ,encoding='utf-8')).get('papers',{}) if os.path.exists(_CJ) else {}
CVALS=('高','中','低','极低','待评定','不适用')
def review_rob_rows(r):
    """Systematic-review quality (certainty.json review_rob_tool + review_rob_overall, deep extract). Separate from
    rob_* and from certainty; shown in 证据与方法 only when both fields are present. Never on the card line or badge."""
    tool=str((r or {}).get('review_rob_tool') or '').strip(); ov=str((r or {}).get('review_rob_overall') or '').strip()
    return [(f'综述偏倚风险（{tool}）',ov)] if tool and ov else []
STEP={0:'不降级',-1:'降一级',-2:'降两级',-3:'降三级'}
def dg_label(d):
    """Downgrade row label from steps (deep extract schema); legacy strings / dicts without steps keep '降一级'. source_file is never shown."""
    if not isinstance(d,dict) or d.get('steps') not in STEP: return '降一级'
    return ((d.get('domain') or '').strip()+' ' if d.get('domain') else '')+STEP[d['steps']]
def notes_txt(r):
    """certainty notes for readers: internal field names are replaced by their values or dropped."""
    s=str(r.get('notes_zh') or '')
    own=str(r.get('own_evidence_strength') or '').strip()
    s=s.replace('原文自报证据强度见 own_evidence_strength','原文自报证据强度：'+own if own else '原文自报证据强度未报告')
    return re.sub(r'[（(]\s*见\s*[a-z_]+\s*[）)]','',s)
def grade(p):
    """Certainty from deep extract's certainty.json (no computation here). Returns (chip_text, fold_html)."""
    r=CERT.get(str(p.get('pmid') or '')) or CERT.get(str(p.get('sid') or '')) or CERT.get(str(p.get('sid') or '').replace('pmid-',''))
    if not r: return '证据确定性：待评定','<p class="note">证据确定性：待评定</p>'
    c=r.get('certainty')
    if p.get('design_category')=='指南/共识' or (c is None and r.get('guideline_strength') is not None):
        st=str(r.get('guideline_strength') or '').strip()
        t=('指南推荐强度：'+(st if len(st)<=30 else st[:30]+'…')) if st and st not in ('该指南未分级','摘要未提及') else '指南（见推荐强度）'
    else:
        c=c if c in CVALS else ('不适用' if c is None and r.get('start') is None else '待评定')
        t=PENDING_LABEL.get(str(p.get('pmid') or '')) or '证据确定性：'+c
    rows=[('起始等级',(r.get('start') or '—')+(f'（{r["start_basis"]}）' if r.get('start_basis') else ''))]+[(dg_label(d),d.get('reason_zh','') if isinstance(d,dict) else str(d)) for d in r.get('downgrades') or []]+([('说明',notes_txt(r))] if r.get('notes_zh') else [])+[('结果',t)]+([('适用范围',r['applicability_note_zh'])] if str(r.get('applicability_note_zh') or '').strip() else [])+review_rob_rows(r)
    h='<table class="kv">'+''.join(f'<tr><th>{k}</th><td>{E_(clean(v))}</td></tr>' for k,v in rows)+'</table>'
    return t,h
CHIP_HOLD=set()
PENDING_LABEL={'26776588':'暂未评级（仅有摘要）'}  # reader label for papers that cannot be rated yet
def _crec(p):
    return CERT.get(str(p.get('pmid') or '')) or CERT.get(str(p.get('sid') or '')) or CERT.get(str(p.get('sid') or '').replace('pmid-','')) or {}
def chip(p,href):
    if not SHOW_CERTAINTY or str(p.get('pmid') or '') in CHIP_HOLD: return ''
    r=_crec(p); c=r.get('certainty')
    if c in ('高','中','低','极低'): return f'<a class="echip" href="{href}">证据确定性：{c}</a>'
    if c=='不适用': return f'<a class="echip na" href="{href}" title="{E_(clean(r.get("na_reason_zh") or ""))}">不分级</a>'
    if str(p.get('pmid') or '') in PENDING_LABEL: return f'<a class="echip na" href="{href}">{PENDING_LABEL[str(p["pmid"])]}</a>'
    if c is None and r and (p.get('design_category')=='指南/共识' or r.get('guideline_strength') is not None):
        st=str(r.get('guideline_strength') or '').strip()
        if st: return f'<a class="echip" href="{href}">指南推荐强度：{E_(st if len(st)<=30 else st[:30]+"…")}</a>'
    return ''
def nochip_reason(p):
    if not SHOW_CERTAINTY: return '本页暂不显示证据确定性。'
    if str(p.get('pmid') or '') in CHIP_HOLD: return '证据确定性：评定结果复核中，暂不显示。'
    r=_crec(p)
    if str(p.get('pmid') or '') in PENDING_LABEL: return ''  # label is already on the chip
    if not r or r.get('certainty')=='待评定': return '证据确定性待评定：'+clean(r.get('pending_reason_zh') or r.get('notes_zh') or '尚未做偏倚风险评估')
    return ''
def title_html(p,tag='h3',href=None):
    main=p.get('title_zh') or p.get('one_line_conclusion_zh')
    t=E_(clean(main)) if main else f'<span lang="en">{E_(p["title"])}</span>'
    if href: t=f'<a href="{href}">{t}</a>'
    sub=f'<p class="en" lang="en">{E_(p["title"])}</p>' if main else ''
    return f'<{tag} class="ct">{t}</{tag}>'+sub
def card(p,r):
    href=f'{r}papers/{p["sid"]}/'
    bl=f'<p class="bl"><span class="eb">一句话结论</span>{E_(clean(p["one_line_conclusion_zh"]))}</p>' if p.get('title_zh') and p.get('one_line_conclusion_zh') else ''
    lab=' · '.join(x for x in [' / '.join(specs(p)),species(p)] if x)
    return f'''<article class="card"><p class="eb">{E_(lab)}</p>{title_html(p,'h3',href)}{bl}{('<p class="bd">'+chip(p,href+'#evidence')+'</p>') if SHOW_CERTAINTY else ''}<p class="ft"><span><em>{E_(p.get("journal",""))}</em> · {E_(str(p.get("year","")))}</span><a class="go" href="{href}">阅读速读 →</a></p></article>'''
def row(p,r):
    t=clean(p.get('title_zh') or p.get('one_line_conclusion_zh') or p['title'])
    return f'<li><a href="{r}papers/{p["sid"]}/">{E_(t)}</a><span class="m">{E_(p.get("first_author",""))} {E_(str(p.get("year","")))} · {E_(p.get("design_category") or "")}</span></li>'
def fresh_list(fs,r):
    if not fs: return ''
    li=''.join(f'<li><a href="https://pubmed.ncbi.nlm.nih.gov/{f["pmid"]}/" lang="en">{E_(f["title"])}</a><span class="m">{E_(f.get("first_author",""))} · <em>{E_(f.get("journal",""))}</em> · {E_(f.get("date",""))} · 未评</span></li>' for f in sorted(fs,key=lambda x:x.get('date',''),reverse=True))
    return f'<section><h2 class="sec"><span>//</span> 最新抓取（未评）</h2><p class="note">每日从 PubMed 按专题检索式自动抓取，尚未速读与分级，链接到 PubMed。</p><ul class="rows">{li}</ul></section>'
FONTS='<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Anton&family=Geist:wght@400;500;600;700&family=Geist+Mono:wght@400;500&display=swap" rel="stylesheet">'
def page(title,body,depth,cur_nav=''):
    r='../'*depth
    nav=''.join(f'<a href="{r}{h}"{" aria-current=page" if k==cur_nav else ""}>{t}</a>' for k,h,t in [('home','','首页'),('topics','topics/','专题'),('lib','library/','文献库'),('about',('about/index.html' if LIVE else '../about/index.html'),'方法')])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">{"" if LIVE else '<meta name="robots" content="noindex,nofollow">'}
<title>{E_(title)}{" · VetLit" if LIVE else " · VetLit 预览"}</title>{FONTS}<link rel="stylesheet" href="{r}static/v.css"></head><body>
<header class="top"><div class="in"><a class="brand" href="{r}">VETLIT<i>.</i></a><nav>{nav}</nav></div></header>
{"" if LIVE else f'<div class="pv">预览版 · 正式站点见 <a href="{r}../">原址</a></div>'}
<main class="wrap">{body}</main>
<footer class="foot"><div class="in">犬猫兽医文献速读 · 仅供专业参考，不构成诊疗建议 · 构建于 {datetime.date.today().isoformat()}</div></footer></body></html>'''
# ---------- home ----------
ALL=sorted(P.values(),key=lambda p:p.get('importance_rank') or 999)
def has_tr(p): return bool(X.can_translate(p) and X.translation(p.get('pmid'),p.get('license')))
JABBR={'Journal of veterinary internal medicine':'J Vet Intern Med','Journal of feline medicine and surgery':'J Feline Med Surg','Journal of the American Veterinary Medical Association':'J Am Vet Med Assoc','Journal of veterinary cardiology : the official journal of the European Society of Veterinary Cardiology':'J Vet Cardiol','Veterinary journal (London, England : 1997)':'Vet J','Science (New York, N.Y.)':'Science','Preventive veterinary medicine':'Prev Vet Med','PloS one':'PLoS One','Scientific reports':'Sci Rep','Pathogens (Basel, Switzerland)':'Pathogens','The Journal of small animal practice':'J Small Anim Pract','Human molecular genetics':'Hum Mol Genet','The Veterinary clinics of North America. Small animal practice':'Vet Clin North Am Small Anim Pract','Behavioural processes':'Behav Processes','Journal of comparative pathology':'J Comp Pathol','Journal of the American Animal Hospital Association':'J Am Anim Hosp Assoc','Frontiers in psychology':'Front Psychol','The Journal of heredity':'J Hered','Veterinary microbiology':'Vet Microbiol','Animal cognition':'Anim Cogn','Current biology : CB':'Curr Biol','The Veterinary record':'Vet Rec','Veterinary research communications':'Vet Res Commun','Animals (Basel)':'Animals'}
DSHORT={'指南/共识':'指南','随机对照试验':'RCT','队列研究':'队列','病例系列（无对照）':'病例系列','实验/基础研究':'实验研究','系统综述/Meta分析':'系统综述','横断面研究':'横断面','叙述性综述':'综述','病例对照研究':'病例对照','非随机对照试验':'非随机对照试验'}
def _ctext(p):
    r=_crec(p); c=r.get('certainty')
    if c in ('高','中','低','极低'): return '证据确定性：'+c
    if c=='不适用': return '不分级'
    if str(p.get('pmid') or '') in PENDING_LABEL: return PENDING_LABEL[str(p['pmid'])]
    if c is None and r and r.get('guideline_strength') and r['guideline_strength'] not in ('该指南未分级','摘要未提及'): return '推荐强度：'+str(r['guideline_strength'])[:20]
    return ''
def _n(p):
    n=str(p.get('n_analysed') or '').strip()
    m_=re.match(r'\s*([\d,]+)\+?',n) if has(n) else None
    if not m_: return ''
    d=m_.group(1).replace(',','')
    return 'n='+(f'{int(d):,}' if d.isdigit() else d)+('+' if m_.group(0).strip().endswith('+') else '')
_CM=os.path.join(ROOT,'data','v5','card_meta.json')
CMETA=(lambda d: d.get('papers',d))(json.load(open(_CM,encoding='utf-8'))) if os.path.exists(_CM) else {}
def cmeta(p):
    m=CMETA.get(str(p.get('pmid') or '')) or CMETA.get(str(p.get('sid') or '')) or {}
    j=p.get('journal') or ''
    seg=[str(m.get('year') or p.get('year') or ''),m.get('journal') or JABBR.get(j,j),m.get('design_zh') or DSHORT.get(p.get('design_category') or '',''),_ctext(p) if SHOW_CERTAINTY else '',m.get('n_label_zh') or '',m.get('species_zh') or '']
    return ' · '.join(str(x) for x in seg if x and x not in ('待评定','不适用','None'))
def _short(t,m=30):
    t=clean(str(t or '')).strip()
    if len(t)<=m: return t
    for i in range(m,10,-1):
        if t[i-1] in '，。；;,、）)': return t[:i-1]+'…' if t[i-1] not in '）)' else t[:i]+'…'
    return t[:m]+'…'
def _norm(t): return re.sub(r'[\W_]+','',clean(t or ''))
def summ(p):
    cl=p.get('one_line_conclusion_zh') or ''; ti=p.get('title_zh') or ''
    import difflib
    dup=ti and (_norm(cl).startswith(_norm(ti)[:12]) or difflib.SequenceMatcher(None,_norm(cl),_norm(ti)).ratio()>0.5)
    if p.get('design_category')=='指南/共识' or dup:
        if has(p.get('clinical_meaning')): return p['clinical_meaning']
        krs=p.get('key_results') or []; t3=p.get('key_results_top3') or [0]
        if krs and isinstance(t3[0],int) and t3[0]<len(krs):
            k=krs[t3[0]]
            if isinstance(k,dict): return '：'.join(x for x in [clean(str(k.get('outcome') or '')),clean(str(k.get('groups') or ''))] if x)
            return str(k)
    return cl
def reason(p,tid):
    pid=str(p.get('pmid') or p.get('sid'))
    for g in (X.TOP.get('topics') or []):
        if g.get('topic')==tid:
            for i in (g.get('items') or []):
                if isinstance(i,dict) and str(i.get('pmid') or i.get('id'))==pid and i.get('reason'): return i['reason']
    t=TBY.get(tid) or {}
    for c in (t.get('core') or []):
        if str(c.get('id')).replace('pmid-','')==pid.replace('pmid-','') and c.get('reason'): return c['reason']
    return ''
def trim_reason(t,p):
    seg=[x.strip() for x in re.split(r'[；;]',clean(t or '')) if x.strip()]
    seg=[re.sub(r'，?年均[^，；]*','',x) for x in seg if x not in (p.get('design_category'),) and not re.fullmatch(r'\d{4} 年发表',x)]
    return '，'.join(x for x in seg if x)
# Supersession (deep extract fields in top_picks.json): items[*] and top-level `supersessions`.
def _sup_rec(i):
    if not isinstance(i,dict) or not i.get('superseded_by'): return None
    sc=i.get('supersession_scope') or i.get('scope') or 'full'
    return {'by':str(i['superseded_by']),'scope':sc,'text':i.get('link_text_zh')}
SUPER={}
for _k,_v in (X.TOP.get('supersessions') or {}).items():
    r=_sup_rec(_v)
    if r: SUPER[str(_k)]=r
for _g in (X.TOP.get('topics') or []):
    for _i in (_g.get('items') or []):
        r=_sup_rec(_i)
        if r:
            k=str(_i.get('pmid') or _i.get('id')); base=SUPER.get(k,{})
            SUPER[k]={**base,**{a:b for a,b in r.items() if b}}
def sup_info(p):
    r=_sup_rec(p)
    return r or SUPER.get(str(p.get('pmid') or ''))
def is_full(i): return bool(i) and (i.get('scope') or 'full')=='full'
def superlink(p,r):
    i=sup_info(p)
    if not i: return ''
    sb=i['by']; q=get(sb)
    h=f'{r}papers/{E_(q["sid"])}/' if q else f'https://pubmed.ncbi.nlm.nih.gov/{E_(sb)}/'
    lab=i.get('text') or ('已有更新版' if is_full(i) else {'treatment_only':'治疗','treatment':'治疗','diagnosis_only':'诊断','cats_only':'猫'}.get(i['scope'],'')+'部分已有更新版')
    lab=lab.rstrip(' →')+' →'
    return f'<p class="note"><a class="tag2" href="{h}">{E_(lab)}</a></p>'
# Errata: data/v5/extras/errata.json {corrected_pmid: {erratum_pmid|null, note_zh, quote, source, display: first_screen|collapsed, affects_clinical}}
try: ERRATA=json.load(open(os.path.join(ROOT,'data','v5','extras','errata.json'),encoding='utf-8'))
except Exception: ERRATA={}
def erratum(p):
    e=ERRATA.get(str(p.get('pmid') or ''))
    return e if isinstance(e,dict) else None
def er_first(e): return bool(e) and (e.get('affects_clinical') is True or e.get('display')=='first_screen')
def er_href(e): return f'https://pubmed.ncbi.nlm.nih.gov/{e["erratum_pmid"]}/' if e.get('erratum_pmid') else (e.get('source') or '')
def er_label(e): return f'勘误 PMID {e["erratum_pmid"]}' if e.get('erratum_pmid') else '出版方更正'
def er_notice(e):
    h=er_href(e); a=f' <a href="{E_(h)}">{E_(er_label(e))} →</a>' if h else ''
    return f'<p class="note er">⚠ 更正（影响临床使用）：{E_(e.get("note_zh") or "")}{a}</p>'
def er_fold(e):
    h=er_href(e); lab=E_(er_label(e))
    return f'<p class="note er">{"<a href="+chr(34)+E_(h)+chr(34)+">"+lab+" →</a>" if h else lab}：{E_(e.get("note_zh") or "")}</p>'
def sup_note(p):  # page-level note for scoped supersession + source quote
    i=sup_info(p); r=(X.TOP.get('supersessions') or {}).get(str(p.get('pmid') or '')) or {}
    if not i: return ''
    q=r.get('supersession_quote'); loc=r.get('supersession_quote_location')
    extra='<p class="note">本指南的猫部分已由新版取代；犬部分仍为现行，继续列入榜单。</p>' if i.get('scope')=='cats_only' else ''
    return extra+(f'<details class="sub"><summary>版本关系原文</summary><blockquote lang="en">{E_(q)}</blockquote>'+(f'<p class="note">出处：{E_(clean(loc))}</p>' if loc else '')+'</details>' if q else '')
def hcard(p,r,tid=None,lst=None):
    href=f'{r}papers/{p["sid"]}/'
    m=cmeta(p); sm=summ(p); rs=pick_reason(p,tid,lst)
    lk=f'<a class="go" href="{href}">速读 →</a>'+(f' <a class="go" href="{href}bilingual/">中英对照 →</a>' if has_tr(p) else '')
    return (f'<article class="card">{title_html(p,"h3",href)}'+(f'<p class="cmeta">{E_(m)}</p>' if m else '')
      +(f'<p class="bl">{E_(clean(sm))}</p>' if sm else '')+(f'<p class="why">{E_(rs)}</p>' if rs else '')+superlink(p,r)+f'<p class="ft">{lk}</p></article>')
def is_super(p):
    return is_full(sup_info(p))
def has_contra(p):  # display-only now; ranking uses affects_conclusion()
    return bool(p.get('rep_inc') or has(p.get('internal_inconsistency')) or p.get('amstar_limit') or sec_get(sections(p),'原文报告不一致'))
# reporting_inconsistency: read from paper data, else extras (top_picks.json top-level map,
# or data/v5/extras/reporting_inconsistency.json {pmid:{severity,note_zh}}). Only severity
# "affects_conclusion" excludes from 最重要/最新; "minor" or absent ranks normally.
try: _RI_FILE=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data/v5/extras/reporting_inconsistency.json'),encoding='utf-8'))
except Exception: _RI_FILE={}
def rep_inc(p):
    k=str(p.get('pmid') or '')
    if isinstance(_RI_FILE.get(k),dict): return _RI_FILE[k]   # source of truth (Vibe-adjudicated)
    v=p.get('reporting_inconsistency')
    if isinstance(v,dict): return v
    v=(X.TOP.get('reporting_inconsistency') or {}).get(k)
    return v if isinstance(v,dict) else {}
def affects_conclusion(p): return rep_inc(p).get('severity')=='affects_conclusion'
def ri_notice(p):
    n=rep_inc(p).get('note_zh')
    return f'<p class="note">⚠ {E_(" ".join(str(n).split()))}</p>' if n else ''
def cohort(p):  # same_cohort_as (card_meta, deep extract): partner PMIDs reporting the same cohort
    m=CMETA.get(str(p.get('pmid') or '')) or {}
    return {str(x) for x in (m.get('same_cohort_as') or [])}
def _fill(cands,k=3,taken=()):
    """Walk cands in order; skip superseded / conclusion-affecting / duplicates, and any paper whose
    same_cohort_as partner is already listed (in this list or in `taken`, the topic's other list)."""
    out,seen=[],set(); pm={str(q.get('pmid') or '') for q in taken if q}
    for p in cands:
        if p and not is_super(p) and not affects_conclusion(p) and p['sid'] not in seen and not (cohort(p)&pm):
            seen.add(p['sid']); out.append(p); pm.add(str(p.get('pmid') or ''))
        if len(out)==k: break
    return out
def tops(tid):
    c=[]
    for g in (X.TOP.get('topics') or []):
        if g.get('topic')==tid: c+=[get(str(i.get('pmid') or i.get('id') if isinstance(i,dict) else i)) for i in (g.get('items') or g.get('picks') or [])]
    t=TBY.get(tid)
    if not c: return []
    if t:
        c+=[get(x['id']) for x in (t.get('core') or [])]
        c+=sorted(tpapers(t),key=lambda p:p.get('importance_rank') or 999)
    return _fill(c)
NEWEST_5Y=False  # 5-year 最新 window: built but OFF — hides 7 topics' 最新 on current data; awaiting decision
def newest_cutoff(today=None):  # rolling 5 years from build date (as PubMed's '5 years' filter)
    d=today or datetime.date.today()
    try: c=d.replace(year=d.year-5)
    except ValueError: c=d.replace(year=d.year-5,day=28)
    return c.isoformat()
def newest3(ps,skip=(),today=None):  # 最新: within 5 years; skips anything already in this topic's 最重要, then fills to 3
    sk={q['sid'] for q in skip if q}; cut=newest_cutoff(today)
    return _fill([p for p in sorted(ps,key=lambda p:p.get('pub_date') or '',reverse=True) if p['sid'] not in sk and (not NEWEST_5Y or (p.get('pub_date') or '')[:10]>=cut)],taken=skip)
# Card reason = pick_reason_zh from data/v5/extras/pick_reason.json (deep extract; synced from extracts/).
# Shape: {pmid: [{topic, list: 最重要|最新, pick_reason_zh, ...}]}. Only entries Vibe marked approved render
# (entry "approved": true, or "approved_by": "Vibe"). Flag PICK_REASON_ON is off unless the file carries any
# approval marker; VETLIT_PICK_REASON=0 forces it off. Absent/unapproved -> nothing shown.
try: _PR=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data/v5/extras/pick_reason.json'),encoding='utf-8'))
except Exception: _PR={}
# Vibe's approval lives beside it (pick_reason_approval.json) so deep extract's file stays untouched.
try: _PRA=json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'data/v5/extras/pick_reason_approval.json'),encoding='utf-8'))
except Exception: _PRA={}
_PR_ALL=str(_PRA.get('approved_by') or '').strip().lower()=='vibe'
def _pr_ok(e): return isinstance(e,dict) and (_PR_ALL or e.get('approved') is True or str(e.get('approved_by') or '').strip().lower()=='vibe')
def _pr_txt(k,t):
    for c in (_PRA.get('strip') or {}).get(k) or []: t=t.replace('，'+c,'').replace(c,'')
    return ' '.join(t.split())
PICK_REASON_ON=os.environ.get('VETLIT_PICK_REASON')!='0' and any(_pr_ok(e) for k,v in _PR.items() if k!='_meta' and isinstance(v,list) for e in v)
def pick_reason(p,tid=None,lst=None):
    if not PICK_REASON_ON: return ''
    k=str(p.get('pmid') or '')
    if k not in _PR: k=str(p.get('sid') or '')   # non-PubMed items (e.g. IRIS 2026) are keyed by sid
    for e in _PR.get(k) or []:
        if _pr_ok(e) and e.get('pick_reason_zh') and (tid is None or e.get('topic')==tid) and (lst is None or e.get('list')==lst):
            return _pr_txt(k,str(e['pick_reason_zh']))
    return ''
def duo(imp,new,r,tid=None):  # an empty 最新 is hidden entirely; fewer than 3 shows just those cards
    return (f'<h4 class="tb">最重要</h4>'+''.join(hcard(p,r,tid,'最重要') for p in imp) if imp else '')+(f'<h4 class="tb">最新</h4>'+''.join(hcard(p,r,tid,'最新') for p in new) if new else '')
def home():
    picks=ALL[:8]
    new=sorted(P.values(),key=lambda p:p.get('pub_date') or '',reverse=True)[:10]
    groups={}
    for p in new: groups.setdefault((p.get('pub_date') or '')[:7],[]).append(p)
    gl=''.join(f'<h3 class="dg">{E_(k[:4])} 年 {int(k[5:7])} 月</h3>'+''.join(card(p,'') for p in v) for k,v in groups.items() if k)
    chips=topic_chips('')
    blocks=''; picks=[]
    for g in (X.TOP.get('topics') or []):
        t=TBY.get(g.get('topic')); imp=tops(g.get('topic')); new=newest3(tpapers(t),imp) if t else []
        picks.append([g.get('topic'),[q.get('pmid') or q.get('sid') for q in imp],[q.get('pmid') or q.get('sid') for q in new]])
        if imp or new: blocks+=f'<section class="tp"><h3 class="dg">'+(f'<a href="topics/{t["id"]}/">' if t else '')+E_(g.get('topic_zh') or '')+('</a>' if t else '')+f'</h3>{duo(imp,new,"",g.get("topic"))}</section>'
    body=f'''<section class="hero"><p class="eb red">// 更新于 {home_stamp(picks)}</p><h1>精选</h1><p class="lede">犬猫兽医文献，结论先行。</p></section>
{blocks}<section><h2 class="sec"><span>//</span> 按专题浏览</h2>{chips}</section>
<p class="more"><a class="btn" href="library/">进入文献库（{len(P)} 篇）→</a></p>{fresh_list(FRESH,'')}'''
    return page('精选',body,0,'home')
# ---------- topics ----------
TBY={t['id']:t for t in TP}
def kids(tid): return [t for t in TP if t.get('parent')==tid]
def tids(t):
    ids=list(t.get('all_ids') or [])
    if not ids:
        for k in kids(t['id']):
            for i in tids(k):
                if i not in ids: ids.append(i)
    return ids
def tpapers(t): return [x for x in (get(i) for i in tids(t)) if x]
VIS=[t for t in TP if tpapers(t)]
def topic_chips(r):
    out=''
    for t in [t for t in VIS if not t.get('parent')]:
        ks=[k for k in VIS if k.get('parent')==t['id']]
        out+=f'<div class="tg"><a class="chip main" href="{r}topics/{t["id"]}/">{E_(t["name_zh"])} <b>{len(tpapers(t))}</b></a>'+''.join(f'<a class="chip" href="{r}topics/{k["id"]}/">{E_(k["name_zh"])} <b>{len(tpapers(k))}</b></a>' for k in ks)+'</div>'
    return out
REAL=lambda t: bool(t.get('bottom_line')) and t.get('bottom_line_clinical') is True
def topic_page(t):
    ps=tpapers(t); r='../../'
    crumb=f'<p class="crumb"><a href="{r}topics/">专题</a>'+(f' › <a href="{r}topics/{t["parent"]}/">{E_(TBY[t["parent"]]["name_zh"])}</a>' if t.get('parent') else '')+'</p>'
    bl=f'<section class="bottom"><p class="eb red">一句话结论</p><p>{E_(clean(t["bottom_line"]))}</p></section>' if REAL(t) else ''
    core=[(get(c['id']),c.get('reason')) for c in (t.get('core') or [])]
    if not t.get('core') and not t.get('all_ids'):
        core=[(p,None) for p in sorted(ps,key=lambda p:p.get('importance_rank') or 999)[:8]]
    core=[(p,why) for p,why in core if p]
    cs=''.join(card(p,r).replace('<p class="ft">',f'<p class="why">入选：{E_(clean(why))}</p><p class="ft">',1) if why else card(p,r) for p,why in core)
    newest=[get(i['id'] if isinstance(i,dict) else i) for i in (t.get('newest') or [])] or sorted(ps,key=lambda p:p.get('pub_date') or '',reverse=True)[:5]
    ks=[k for k in VIS if k.get('parent')==t['id']]
    sub=f'<section><h2 class="sec"><span>//</span> 子专题</h2>'+''.join(f'<a class="chip" href="{r}topics/{k["id"]}/">{E_(k["name_zh"])} <b>{len(tpapers(k))}</b></a>' for k in ks)+'</section>' if ks else ''
    fr=[f for f in FRESH if t['id'] in (f.get('topics') or [])]
    body=f'''{crumb}<section class="hero"><p class="eb">{E_(t.get("name_en",""))}</p><h1>{E_(t["name_zh"])}</h1><p class="lede">{len(ps)} 篇已速读文献</p></section>{bl}{sub}
<section>{duo((_imp:=(tops(t['id']) or _fill([p for p,_ in core]))),newest3(ps,_imp),r,t['id'])}</section>
<section><h2 class="sec"><span>03</span> 全部 {len(ps)} 篇</h2><ul class="rows">{''.join(row(p,r) for p in sorted(ps,key=lambda p:p.get('pub_date') or '',reverse=True))}</ul></section>{fresh_list(fr,r)}'''
    return page(t['name_zh'],body,2,'topics')
def topics_index():
    body=f'<section class="hero"><p class="eb red">// 专题</p><h1>按专科与疾病浏览</h1></section>'+topic_chips('../')
    return page('专题',body,1,'topics')
# ---------- library ----------
def library():
    data=[{'id':p['sid'],'t':clean(p.get('title_zh') or p.get('one_line_conclusion_zh') or p['title']),'en':p['title'],'a':p.get('first_author',''),'y':str(p.get('year','')),'d':p.get('pub_date') or '','j':p.get('journal',''),'sp':species(p),'spec':specs(p),'lv':level(p),'dc':p.get('design_category') or '','r':p.get('importance_rank') or 999} for p in P.values()]
    sp=sorted({s for p in P.values() for s in specs(p)}); lv=['指南/共识']+[f'Level {i}' for i in range(1,6) if any(level(p)==f'Level {i}' for p in P.values())]+['未分级']
    o=lambda xs:''.join(f'<option>{E_(x)}</option>' for x in xs)
    body=f'''<section class="hero"><p class="eb red">// 文献库</p><h1>全部文献</h1></section>
<form class="flt" onsubmit="return false"><label>物种<select id="fs"><option value="">全部</option>{o(['猫','犬'])}</select></label><label>专科<select id="fp"><option value="">全部</option>{o(sp)}</select></label><label>证据等级<select id="fl"><option value="">全部</option>{o(lv)}</select></label><label>排序<select id="fo"><option value="d">最新</option><option value="r">重要</option></select></label></form>
<p class="note" id="cnt"></p><ul class="rows" id="lst"></ul>
<script>const D={json.dumps(data,ensure_ascii=False)};
const $=i=>document.getElementById(i),esc=s=>String(s).replace(/[&<>"]/g,c=>({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
function go(){{const s=$('fs').value,p=$('fp').value,l=$('fl').value,o=$('fo').value;
let x=D.filter(d=>(!s||d.sp.includes(s))&&(!p||d.spec.includes(p))&&(!l||d.lv===l));
x.sort((a,b)=>o==='r'?a.r-b.r:b.d.localeCompare(a.d));$('cnt').textContent='显示 '+x.length+' / '+D.length+' 篇';
$('lst').innerHTML=x.map(d=>`<li><a href="../papers/${{d.id}}/">${{esc(d.t)}}</a><span class="m" lang="en">${{esc(d.en)}}</span><span class="m">${{esc(d.a)}} ${{esc(d.y)}} · <em>${{esc(d.j)}}</em> · ${{esc(d.sp)}} · ${{esc(d.dc)}} · ${{esc(d.lv)}}</span></li>`).join('')}}
['fs','fp','fl','fo'].forEach(i=>$(i).onchange=go);go();</script>'''
    return page('文献库',body,1,'lib')
# ---------- paper ----------
def sections(p):
    f=p.get('detail'); out={}
    if not f or not os.path.exists(os.path.join(ROOT,'content',f)): return out
    t=B.strip_legacy_grades(open(os.path.join(ROOT,'content',f),encoding='utf-8').read())
    for m in re.finditer(r'^## (?:\d+\.\s*)?(.+?)\n(.*?)(?=^## |\Z)',t,re.S|re.M): out[m.group(1).strip()]=m.group(2).strip()
    return out
def sec_get(S,key):
    for k,v in S.items():
        if k.startswith(key): return v
    return ''
def mdc(s): return B.md(clean(s))
UNK=('信息不足','不清楚','未检到','本次未读到','无法判断')
def appraisal(p):
    it=p.get('appraisal_items') or []
    if not it: return ''
    def cls(j):
        j=j or ''
        if any(u in j for u in UNK) or j in ('不适用','—',''): return 'j0'
        return {'低':'jl','是':'jl','充分':'jl','高':'jh','严重':'jh','否':'jh'}.get(j,'jm')
    def qt(i):
        q=i.get('evidence_quote') or ''
        return f'<blockquote lang="en">{E_(q)}</blockquote>' if q and q not in (i.get('reason') or '') else ''
    rows=''.join(f'<tr><td>{E_(i.get("item",""))}</td><td><span class="j {cls(i.get("judgment"))}">{E_(i.get("judgment",""))}</span></td><td>{E_(clean(i.get("reason","")))}{qt(i)}</td></tr>' for i in it)
    tbl=f'<div class="tw"><table><thead><tr><th>条目</th><th>判断</th><th>理由与原文</th></tr></thead><tbody>{rows}</tbody></table></div>'
    unk=sum(1 for i in it if cls(i.get('judgment'))=='j0')
    tool=E_(p.get('rob_tool') or '')
    if unk*2>=len(it):
        return f'<p class="muted">{"仅读摘要，" if p.get("reading_depth")!="全文" else ""}偏倚风险多数领域无法判断（{tool}，{unk}/{len(it)} 项“信息不足/不清楚/不适用”，不等于高风险）。</p><details class="sub"><summary>展开逐项判断</summary>{tbl}</details>'
    return f'<p class="note">“信息不足/不清楚”表示所读材料未报告，不等于高风险。</p>'+tbl
def _bg(t): t=re.sub(r'[\s，。、；：:（）()“”"\'·,.;-]','',t); return {t[i:i+2] for i in range(len(t)-1)}
def near_dup(a,b):
    A,Bs=_bg(a),_bg(b)
    return bool(A) and len(A&Bs)/len(A)>=0.4
# ---------- deep speed-read (ACP Journal Club format; data/v5/deep_speedread.json) ----------
DS_TITLES={'clinical_bottom_line':'临床结论','clinical_question_pico':'临床问题','design_and_subjects':'研究设计与对象','scope_and_methods':'范围与方法','main_results':'主要结果','main_recommendations':'主要推荐','authors_conclusion':'结论（作者原话）','commentary':'评论'}
DS_SKIP={'certainty','funding_coi'}  # shown from certainty/funding data in 证据与方法, never twice
def _ds_pm(h):
    def rep(m):
        q=get(m.group(1)); href=f'../{q["sid"]}/' if q else f'https://pubmed.ncbi.nlm.nih.gov/{m.group(1)}/'
        return f'<a href="{href}">PMID {m.group(1)}</a>'
    return re.sub(r'PMID (\d{5,9})',rep,h)
def _dsi(t): return _ds_pm(B.inline(clean(t)))
def _ds_item(l): return re.match(r'^(\s*)([-*]|\d+\.)\s+(.*)$',l)
def _ds_list(L,i):
    m=_ds_item(L[i]); ind=len(m.group(1)); tag='ol' if m.group(2)[-1]=='.' else 'ul'; items=[]
    while i<len(L):
        l=L[i]
        if not l.strip():
            j=i+1
            while j<len(L) and not L[j].strip(): j+=1
            if j<len(L) and (len(L[j])-len(L[j].lstrip(' ')))>ind: i=j; continue
            m2=_ds_item(L[j]) if j<len(L) else None
            if m2 and len(m2.group(1))==ind: i=j; continue
            break
        m2=_ds_item(l)
        if m2 and len(m2.group(1))==ind: items.append([_dsi(m2.group(3)),'']); i+=1; continue
        if m2 and len(m2.group(1))>ind and items:
            h,i=_ds_list(L,i); items[-1][1]+=h; continue
        if items and (len(l)-len(l.lstrip(' ')))>ind and not m2:
            items[-1][1]+=f'<p>{_dsi(l.strip())}</p>'; i+=1; continue
        break
    return f'<{tag}>'+''.join(f'<li>{a}{b}</li>' for a,b in items)+f'</{tag}>',i
def _ds_table(rows):
    C=[[c.strip() for c in re.split(r'(?<!\\)\|',r.strip().strip('|'))] for r in rows]
    head,body=C[0],[c for c in C[1:] if not all(re.match(r'^:?-+:?$',x) for x in c if x)]
    if len(head)==2 and not any(head):
        return '<table class="kv">'+''.join(f'<tr><th>{_dsi(r[0])}</th><td>{_dsi(r[1] if len(r)>1 else "")}</td></tr>' for r in body)+'</table>'
    return '<div class="tw"><table><thead><tr>'+''.join(f'<th>{_dsi(c)}</th>' for c in head)+'</tr></thead><tbody>'+''.join('<tr>'+''.join(f'<td>{_dsi(c)}</td>' for c in r)+'</tr>' for r in body)+'</tbody></table></div>'
_DS_LEAD=re.compile(r'^\*\*([^*]+?[。：:])\*\*\s*(.*)$')
def ds_md(t):
    """Markdown used by deep speed-reads: bold lead paragraphs -> h3, nested lists, PICO key/value tables. HTML comments are internal and dropped."""
    L=re.sub(r'<!--.*?-->','',t or '',flags=re.S).split('\n'); i=0; out=[]
    para=lambda l: l.strip() and not _ds_item(l) and not l.lstrip().startswith(('|','>')) and not _DS_LEAD.match(l.strip()) and not re.match(r'^-{3,}$',l.strip())
    while i<len(L):
        l=L[i]
        if not l.strip() or re.match(r'^-{3,}$',l.strip()): i+=1; continue
        if l.lstrip().startswith('|'):
            rows=[]
            while i<len(L) and L[i].lstrip().startswith('|'): rows.append(L[i]); i+=1
            out.append(_ds_table(rows)); continue
        if _ds_item(l): h,i=_ds_list(L,i); out.append(h); continue
        if l.startswith('>'):
            buf=[]
            while i<len(L) and L[i].startswith('>'): buf.append(L[i][1:].strip()); i+=1
            out.append(f'<blockquote>{_dsi(" ".join(buf))}</blockquote>'); continue
        m=_DS_LEAD.match(l.strip())
        if m:
            out.append(f'<h3>{_dsi(m.group(1))}</h3>'); i+=1; buf=[m.group(2)] if m.group(2).strip() else []
            while buf and i<len(L) and para(L[i]): buf.append(L[i].strip()); i+=1
            if buf: out.append(f'<p>{_dsi(" ".join(buf))}</p>')
            continue
        buf=[]
        while i<len(L) and para(L[i]): buf.append(L[i].strip()); i+=1
        if buf: out.append(f'<p>{_dsi(" ".join(buf))}</p>')
        else: i+=1
    return ''.join(out)
def ds_sections(r):
    """[(key, heading, html)] in the record's own order; certainty/funding are rendered elsewhere."""
    out=[]
    for k in r.get('section_order') or []:
        sec=(r.get('sections') or {}).get(k) or {}
        if k in DS_SKIP or not str(sec.get('markdown') or '').strip(): continue
        h=re.sub(r'\s+',' ',clean(sec.get('heading') or DS_TITLES.get(k,''))).strip()
        out.append((k,h,ds_md(sec['markdown'])))
    return out
def paper(p):
    r='../../'; S=sections(p); ds=ds_of(p)
    if ds and ds.get('title_zh'): p=dict(p); p['title_zh']=ds['title_zh']
    head=f'''<p class="crumb"><a href="{r}library/">文献库</a>{"".join(f' › <a href="{r}topics/{t}/">{E_(TBY[t]["name_zh"])}</a>' for t in (p.get("topics") or [])[:1] if t in TBY and t in [v["id"] for v in VIS])}</p>
<p class="eb">{E_(" / ".join(specs(p)))} · {E_(species(p))}</p>{title_html(p,'h1')}<p class="cmeta">{E_(cmeta(p))}</p>{superlink(p,'../../')}{sup_note(p)}
<p class="meta">{E_(p.get("first_author",""))} 等 · <em>{E_(p.get("journal",""))}</em> · {E_(p.get("pub_date") or str(p.get("year","")))}{f' · <a href="https://doi.org/{E_(p["doi"])}">DOI</a>' if p.get('doi') else ''}{f' · <a href="https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/">PubMed</a>' if p.get('pmid') else ''}{f' · <a href="https://europepmc.org/article/PMC/{p["pmcid"]}">全文</a>' if p.get('pmcid') else ''}</p>
<p>{"".join(f'<a class="chip" href="{r}topics/{t}/">{E_(TBY[t]["name_zh"])}</a>' for t in (p.get("topics") or []) if t in TBY and TBY[t] in VIS)}</p>'''
    blk=lambda n,t,c: f'<section class="blk"><h2 class="sec"><span>{n}</span> {t}</h2>{c}</section>' if c else ''
    exp=(p.get('population_type') or 'natural') in ('experimental','mixed')
    conf=f'<p class="note">{E_(clean(p["confidence_sentence"]))}</p>' if has(p.get('confidence_sentence')) else ''
    why=f'<p class="why2">{E_(clean(p["why_it_matters"]))}</p>' if has(p.get('why_it_matters')) else ''
    concl=f'<section class="bottom"><p class="eb red">一句话结论</p><p>{E_(clean(p["one_line_conclusion_zh"]))}</p></section>' if has(p.get('one_line_conclusion_zh')) else ''
    sc=p.get('study_card') or {}
    pico=sec_get(S,'PICO')
    if pico: pico=mdc(re.sub(r'^\|\s*资助.*$','',pico,flags=re.M))
    elif p.get('population_type')=='na': pico=''
    else:
        rows=[('设计',p.get('design_detail') or p.get('design')),('物种',species(p)),('纳入 n / 分析 n',' / '.join(x for x in [('纳入 '+str(p['n_enrolled'])) if has(p.get('n_enrolled')) and '未核' not in str(p['n_enrolled']) else '',('分析 '+str(p['n_analysed'])) if has(p.get('n_analysed')) and '未核' not in str(p['n_analysed']) else ''] if x)),('中心',sc.get('单/多中心'))]
        rows=''.join(f'<tr><th>{k}</th><td>{E_(clean(v))}</td></tr>' for k,v in rows if has(v))
        pico=f'<table class="kv">{rows}</table>' if rows else ''
    PH={'','—','-','–','None'}
    krs=[k for k in (p.get('key_results') or []) if any(str(k.get(f) or '').strip() not in PH for f in ('groups','effect_ci','p'))]
    cell=lambda v: '' if str(v or '').strip() in PH else E_(clean(v))
    if krs: kr='<div class="tw"><table><thead><tr><th>指标</th><th>组别/数值</th><th>效应量（95% CI）</th><th>P</th></tr></thead><tbody>'+''.join(f'<tr><td>{cell(k.get("measure"))}</td><td>{cell(k.get("groups"))}</td><td>{cell(k.get("effect_ci"))}</td><td>{cell(k.get("p"))}</td></tr>' for k in krs)+'</tbody></table></div>'
    else:
        kr=sec_get(S,'关键结果'); kr=mdc(kr) if kr and not re.fullmatch(r'[\s—\-|指标结果统计:]*',kr) else (f'<p>{E_(clean(p["results"]))}</p>' if has(p.get('results')) else '')
    _ts=X.text_source(p.get('pmid'))
    if _ts: p['reading_depth']=_ts
    if p.get('text_source_force'): p['reading_depth']=p['text_source_force']
    absonly=p.get('reading_depth')!='全文'
    if kr and absonly: kr+='<p class="note">本页数字来自摘要，未经全文核对</p>'
    m=dict(p.get('methods') or {}); RES=p.get('res') or {}
    rv=lambda f: (E_(clean(RES[f][0]))+(f'<blockquote lang="en">{E_(RES[f][1])}</blockquote>' if RES[f][1] else '')) if f in RES else ''
    POP=[('研究对象',E_(clean(p.get('pop_note') or '')))]+[(k,E_(clean(v if isinstance(v,str) else (v.get('summary_zh') or '')))) for k,v in (p.get('pop') or {}).items() if k in ('来源',) and v]
    if 'multicenter' in RES: POP.append(('单/多中心',rv('multicenter')))
    _nn=' / '.join(x for x in [('纳入 '+str(p['n_enrolled'])) if has(p.get('n_enrolled')) and '未核' not in str(p['n_enrolled']) else '',('分析 '+str(p['n_analysed'])) if has(p.get('n_analysed')) and '未核' not in str(p['n_analysed']) else ''] if x)
    if _nn and '纳入 n / 分析 n' not in (pico or ''): POP.append(('纳入 n / 分析 n',E_(_nn)))
    popt=''.join(f'<tr><th>{E_(k)}</th><td>{v}</td></tr>' for k,v in POP if v)
    if popt: pico=f'<table class="kv">{popt}</table>'+(pico or '')
    MK=[]
    mitems=[(k,m.get(k)) for k,model in MK if not (model and not m.get(k))]+[(k,v) for k,v in m.items() if k not in dict(MK)]
    mt=''.join(f'<tr><th>{E_(k)}</th><td>{E_(clean(v if v else "原文未报告"))}</td></tr>' for k,v in mitems) if m else ''
    def slot(v):
        if not isinstance(v,dict): return E_(clean(str(v)))
        if v.get('status')=='已报告' and (v.get('summary_zh') or v.get('evidence_quote')):
            return E_(clean(v.get('summary_zh') or ''))+(f'<blockquote lang="en">{E_(v["evidence_quote"])}</blockquote>' if v.get('evidence_quote') else '')
        return f'<span class="muted">{E_(v.get("status") or "原文未报告")}</span>'
    mt+=''.join(f'<tr><th>{E_(k)}</th><td>{slot(v)}</td></tr>' for k,v in (p.get('slots') or {}).items() if k not in ('纳入标准','排除标准','疾病分期'))
    meth=''
    cs=''
    if p.get('can_say') and '见页面' not in str(p['can_say']) and (p.get('p38') or not sec_get(S,'能说')):
        cs='<h3>能说</h3><ul>'+''.join(f'<li>{E_(clean(x))}</li>' for x in p['can_say'])+'</ul><h3>不能说</h3><ul>'+''.join(f'<li>{E_(clean(x))}</li>' for x in p.get('cannot_say') or [])+'</ul>'
    elif sec_get(S,'能说'):
        cs=mdc(sec_get(S,'能说')).replace('<p><strong>能说</strong></p>','<h3>能说</h3>').replace('<p><strong>不能说</strong></p>','<h3>不能说</h3>')
    if exp and cs: cs='<p class="note">实验造模结果不一定能外推到自然发病的猫狗</p>'+cs
    lv=str(p.get('cebm_level') or '')
    tool=p.get('rob_tool') or ''
    it=p.get('appraisal_items') or []
    unk=sum(1 for i in it if any(u in (i.get('judgment') or '') for u in UNK))
    hi=[i.get('item') for i in it if (i.get('judgment') or '') in ('高','严重','否')]
    v6t=p.get('v6_tool') or ''; v6j=p.get('v6_judg') or ''
    REEVAL=v6j.startswith('未评')
    NOTOOL=v6t.startswith('无') or v6j.startswith('不适用（无公认工具')
    if (REEVAL or NOTOOL) and not p.get('adj') and not p.get('amstar'): it=[]
    rc=re.search(r'仅\s*([A-Za-z\-0-9 ]+?)\s*报告规范',v6t); rcs=rc.group(1) if rc else (p.get('reporting_checklist') if has(p.get('reporting_checklist')) else '')
    if p.get('adj'): why1=f'{p.get("rob_tool") or "RoB 2"} 总体：{p.get("adj_overall","")}'
    elif p.get('amstar'): why1=p['amstar_overall']
    elif REEVAL: why1='未评（仅摘要）'
    elif NOTOOL: why1='不适用（无公认工具）'+(f'；报告规范：{rcs}' if rcs else '')
    elif p.get('appraisal_note'): why1=p['appraisal_note']
    elif not it: why1='未评'
    elif hi: why1=f'{tool}：{len(hi)}/{len(it)} 项判为高风险或不满足（{"、".join(hi[:3])}）'
    elif unk*2>=len(it): why1=f'{tool}：{unk}/{len(it)} 项信息不足，无法判断，不等于高风险'
    else: why1=f'{tool}：{len(it)} 项中 {unk} 项信息不足，其余未见高风险'
    ev=f'<table class="kv"><tr><th>Oxford CEBM 2011</th><td>{E_(clean(lv or "未分级"))}{("（"+E_(clean(p["cebm_basis"]))+"）") if has(p.get("cebm_basis")) else ""}{("<br>设计说明："+E_(p["cebm_note"])) if p.get("cebm_note") else ""}</td></tr><tr><th>偏倚风险</th><td>{E_(clean(why1))}</td></tr>'+''.join(f'<tr><th>{k}</th><td>{E_(clean(v))}</td></tr>' for k,v in [('报告规范',p.get('reporting_checklist')),('指南推荐强度（原文）',p.get('guideline_recommendation') if p.get('design_category')=='指南/共识' and not p.get('gs') else '')] if has(v))+'</table>'
    if p.get('gs'):
        g=p['gs']; segs=[x.strip() for x in re.split(r'\s*(?:\|\||…)\s*',g.get('quote') or '') if x.strip()]
        src='引自 2022 更新版' if str(p.get('pmid'))=='29314873' else (g.get('location') or '')
        gc=E_(g.get('strength') or '')+(f'<p class="note">分级体系：{E_(g["scheme"])}</p>' if g.get('scheme') and g['scheme']!=g.get('strength') else '')+''.join(f'<blockquote lang="en">{E_(x)}</blockquote>' for x in segs)+(f'<p class="note">出处：{E_(clean(src))}</p>' if clean(src) else '')
        ev=ev.replace('</table>',f'<tr><th>指南推荐强度（原文）</th><td>{gc}</td></tr></table>',1)
    ROBJ=not (REEVAL or NOTOOL or why1=='未评') or p.get('adj')
    if p.get('amstar_limit'): ev+=f'<p class="note">局限性：{p["amstar_limit"]}</p>'
    if p.get('rep_inc'):
        ev+='<div class="blk"><p><b>报告质量问题</b>（原文内部前后不一致）</p><ul>'+''.join(f'<li>{E_(i.get("issue_zh",""))}'+(f'<blockquote lang="en">{E_(i["quote_a"])}</blockquote><p class="note">{E_(i.get("loc_a",""))}</p>' if i.get('quote_a') else '')+(f'<blockquote lang="en">{E_(i["quote_b"])}</blockquote><p class="note">{E_(i.get("loc_b",""))}</p>' if i.get('quote_b') else '')+'</li>' for i in p['rep_inc'])+'</ul></div>'
    if has(p.get('rob_tool_note')) and not REEVAL: ev+=f'<p class="note">工具说明：{E_(clean(p["rob_tool_note"]))}</p>'
    if it: ev+=f'<details class="sub"><summary>展开逐项判断</summary>{appraisal(p)}</details>'
    fund=p.get('funder') or sc.get('资助') or p.get('funding')
    if 'funding' in RES and (not has(fund) or '未核' in str(fund)): fund=f'<p>{rv("funding")}</p>'
    else: fund=f'<p>{E_(clean(fund))}</p>' if has(fund) and not str(fund).startswith('未核') else '<p class="muted">原文未报告</p>'
    if 'recommendation_basis' in RES: ev+=f'<p class="note">推荐依据：{rv("recommendation_basis")}</p>'
    methods_blk=lambda: (f'<details class="fold" {"open" if exp else ""}><summary>研究方法</summary>{meth}</details>' if meth else '')
    if p.get('limits'): kr=(kr or '')+'<p class="note">局限：'+'；'.join(E_(x) for x in p['limits'])+'</p>'
    TAG=''   # process labels (who assessed / extracted) are not shown on reader pages
    if TAG:
        concl=concl.replace('</section>',TAG+'</section>',1) if concl else concl
        kr=(kr+TAG) if kr else kr
        _t='<span class="note">（'+TAG[len('<p class="note tag2">'):-4]+'）</span>'
        pico=re.sub(r'(<th>纳入 n / 分析 n</th><td>.*?)(</td>)',lambda m:m.group(1)+_t+m.group(2),pico or '',count=1)
    if exp: order=[('研究对象',pico if popt else ''),('动物来源与实验处理',None),('关键数字',kr),('证据等级与偏倚风险',ev),('资助方与利益冲突',fund)]
    else: order=[('研究对象/干预/对照/结局 · 样本量',pico),('关键数字',kr),('研究方法',None),('证据等级与偏倚风险',ev),('资助方与利益冲突',fund)]
    OPEN="document.getElementById('evidence').open=true"
    _fl=re.sub(r'<blockquote.*?</blockquote>','',fund,flags=re.S); _fl=re.sub(r'<[^>]+>','',_fl).strip()
    _fl=_fl if _fl and _fl!='原文未报告' else ('原文未报告' if 'muted' in fund else '未核实')
    _fl=' '.join(_fl.split()); _fl=_fl if len(_fl)<=90 else _fl[:88]+'…'
    _fund_html=f'<p class="cmeta fund">资助/利益冲突：{E_(__import__('html').unescape(_fl))}</p>'
    head=re.sub(r'(<p class="cmeta">.*?</p>)',lambda m:m.group(1)+_fund_html,head,count=1,flags=re.S)
    # ---- above the fold: warning, conclusion, clinical meaning, key numbers, chip ----
    vis=head
    if p.get('warn_speed'): vis+=f'<p class="warn" style="background:#fff4d6;border-left:4px solid #e0a100;padding:.5em .8em;margin:.4em 0;color:#5a4300">{E_(p["warn_speed"])}</p>'
    inc_md=sec_get(S,'原文报告不一致')
    ds=ds_of(p); dss=ds_sections(ds) if ds else []
    if dss:
        _bl=next((h for k,_,h in dss if k=='clinical_bottom_line'),'')
        vis+=(f'<p class="note dsb">{E_(clean(ds["design_and_basis"]))}</p>' if has(ds.get('design_and_basis')) else '')+(f'<section class="dsbl"><p class="eb red">临床结论</p>{_bl}</section>' if _bl else concl)
    else: vis+=concl
    if not dss and has(p.get('clinical_meaning')) and not near_dup(p['clinical_meaning'],p.get('one_line_conclusion_zh') or ''): vis+=f'<p class="cm">{E_(clean(p["clinical_meaning"]))}</p>'
    kn=[]
    _all=p.get('key_results') or []; _t3=p.get('key_results_top3')
    top=[_all[i] for i in _t3 if isinstance(i,int) and 0<=i<len(_all)][:3] if isinstance(_t3,list) else krs[:3]
    for k in top:
        NR=lambda v: '' if re.search(r'^(不适用|N/?A|—)$',re.sub(r'<[^>]+>','',v).strip()) else v
        parts=[NR(cell(k.get(f))) for f in ('groups','effect_ci')]; pv=NR(cell(k.get('p')))
        kn.append(f'<li data-m="{cell(k.get("measure"))}"><b>{cell(k.get("measure"))}</b> {" · ".join(x for x in parts if x)}{(" · P "+pv) if pv and not pv.upper().startswith("P") and not pv.startswith(("原文","摘要")) else (" · "+pv if pv else "")}</li>')
    if not kn and not cs and p.get('can_say') and '见页面' not in str(p['can_say']): kn=[f'<li>{E_(clean(x))}</li>' for x in p['can_say'][:3]]
    _ri=ri_notice(p); _rin=rep_inc(p).get('note_zh') or ''
    if _ri and kn:
        # attach ⚠ to the key number it concerns (shared wording with the note), else right under the list
        hit=next((i for i,k in enumerate(top) if k.get('measure') and near_dup(str(k['measure']),_rin)),None)
        if hit is not None: kn[hit]=kn[hit][:-5]+_ri.replace('<p class="note">','<p class="note ri">',1)+'</li>'
    if dss: kn=[]; cs=''
    if kn: vis+=f'<section class="kn"><p class="eb">关键数字</p><ul>{"".join(kn)}</ul>{_ri.replace(chr(60)+"p class="+chr(34)+"note"+chr(34),chr(60)+"p class="+chr(34)+"note ri"+chr(34),1) if _ri and not any("note ri" in x for x in kn) else ""}</section>'
    elif _ri: vis+=_ri.replace('<p class="note">','<p class="note ri">',1)
    _er=erratum(p)
    if er_first(_er):
        vis=vis[:-len('</section>')]+er_notice(_er)+'</section>' if kn else vis+er_notice(_er)
    if cs: vis+=f'<section class="cs" id="cansay">{cs}</section>'
    gt,gh=grade(p)
    _c=chip(p,'#evidence')
    if _c: vis+='<p class="bd">'+_c.replace('<a ',f'<a onclick="{OPEN}" ',1)+'</p>'
    _tr=X.translation(p.get('pmid'),p.get('license')) if X.can_translate(p) else None
    if dss:
        _n=0
        for k,h,html_ in dss:
            if k=='clinical_bottom_line': continue
            _n+=1; vis+=f'<section class="blk ds"><h2 class="sec"><span>{_n:02d}</span> {E_(h)}</h2>{html_}</section>'
    if _tr: vis+='<p class="deep"><a class="btn big" href="bilingual/">中英对照深入阅读 →</a></p>'
    else:
        _o=f'https://doi.org/{p["doi"]}' if p.get('doi') else (p.get('url') or (f'https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/' if p.get('pmid') else ''))
        if _o: vis+=f'<p class="orig"><a href="{E_(_o)}">阅读原文 →</a></p>'
    vis+=X.related_block(p.get('pmid'),lambda q:(f"{r}papers/{get(str(q.get('pmid'))).get('sid')}/" if q.get('pmid') and get(str(q.get('pmid'))) else ('https://doi.org/'+q['doi'] if q.get('doi') else (q.get('url') or q.get('openalex') or '#'))))
    # ---- fold: 证据与方法 ----
    fb=(f'<section class="blk"><h3>证据确定性</h3>{gh}</section>' if SHOW_CERTAINTY else '')+badges(p)+conf+why
    n=0
    for t,c in order:
        if c is None:
            if meth: n+=1; fb+=blk(f'{n:02d}',t,meth)
            continue
        if c: n+=1; fb+=blk(f'{n:02d}',t,c)
    if inc_md: fb+=f'<section class="blk" id="inconsistency"><h2 class="sec"><span>!</span> 原文报告不一致</h2>{mdc(inc_md)}</section>'
    er=p.get('errata'); er=', '.join(er) if isinstance(er,list) else er
    if erratum(p): er=''; fb+=er_fold(erratum(p)) if not er_first(erratum(p)) else ''
    fb+=''.join(f'<p class="note"{" id=inconsistency" if k=="论文内部不一致" and not inc_md else ""}>{k}：{E_(clean(v))}</p>' for k,v in [('勘误',f'PMID {er}' if has(er) else ''),('论文内部不一致',p.get('internal_inconsistency'))] if has(v))
    if p.get('rep_inc') and not inc_md and not has(p.get('internal_inconsistency')): fb=fb.replace('<div class="blk"><p><b>报告质量问题</b>','<div class="blk" id="inconsistency"><p><b>报告质量问题</b>',1)
    elif p.get('amstar_limit') and 'id="inconsistency"' not in fb and 'id=inconsistency' not in fb: fb=fb.replace('<p class="note">局限性：','<p class="note" id="inconsistency">局限性：',1)
    if _tr:
        orig=f'<p>许可 {E_(str(p.get("license","")).upper())}。<a class="btn" href="bilingual/">阅读中英对照全文 →</a></p><p class="note">如有出入，以英文原文为准。</p>'
    elif X.can_translate(p):
        orig=f'<p>许可 {E_(str(p.get("license","")).upper())} 允许翻译，中英对照尚未生成。{f'<a href="https://doi.org/{E_(p["doi"])}">阅读原文 →</a>' if p.get('doi') else ''}</p>'
    else:
        orig=f'<p>许可{("（"+E_(str(p["license"]))+"）") if has(p.get("license")) else ""}不允许全文翻译转载，本站只提供速读与术语对照。{f'<a href="https://doi.org/{E_(p["doi"])}">阅读原文 →</a>' if p.get('doi') else ''}</p>'
    fb+=f'<details class="sub"><summary>原文与许可</summary>{orig}</details>'
    fb+=f'<p class="note sig">依据：{p.get("basis_label") or ("仅题录，无摘要" if p.get("reading_depth")=="题录" else "摘要" if absonly else "全文")}</p>'
    body=vis+f'<details class="fold evf" id="evidence"><summary>证据与方法</summary>{('<p class="why0">'+E_(nochip_reason(p))+'</p>') if nochip_reason(p) else ''}{fb}</details>'
    terms=sec_get(S,'关键术语')
    if terms: body+=f'<details class="fold"><summary>关键术语中英对照</summary>{mdc(terms)}</details>'
    bib=B.bibtex(B.view({**p,'id':p['sid']})); ris=B.ris(B.view({**p,'id':p['sid']}))
    body+=f'<details class="fold"><summary>引用（BibTeX / RIS）</summary><pre>{E_(bib)}</pre><pre>{E_(ris)}</pre></details>'
    body+='<script>if(location.hash&&location.hash!=="#evidence"){var e=document.querySelector(location.hash);if(e&&e.closest("#evidence"))document.getElementById("evidence").open=true}else if(location.hash==="#evidence")document.getElementById("evidence").open=true</script>'
    return page(clean(p.get('title_zh') or p.get('first_author','')+' '+str(p.get('year',''))),body,2)
def w(rel,s):
    f=os.path.join(OUT,rel); os.makedirs(os.path.dirname(f),exist_ok=True); open(f,'w',encoding='utf-8').write(B.unproc(s))
def main():
    if not LIVE: shutil.rmtree(OUT,ignore_errors=True)
    w('index.html',home()); w('library/index.html',library()); w('topics/index.html',topics_index())
    for t in VIS: w(f'topics/{t["id"]}/index.html',topic_page(t))
    R2=json.load(open(os.path.join(ROOT,'data','v5','unverified_resolution_r2.json'),encoding='utf-8'))['records']; MERGE['ur2']=0
    for k,v in R2.items():
        q=matcher({'pmid':k,'id':k})
        if q: q['r2']=v; MERGE['ur2']+=1
    print('ur2',MERGE['ur2'])
    for p in P.values():
        h=paper(p)
        for x in p.get('r2') or []:
            f=re.sub(r'（续）$','',x['field']); base='中心' if f.startswith('中心') else f
            if x.get('value')=='见上': continue
            val=x['value'] or ('摘要未提及' if str(x['status']).startswith('摘要未提及') else x['status'])
            cell=E_(val)+(f'<blockquote lang="en">{E_(x["evidence_quote"])}</blockquote>' if x.get('evidence_quote') and x['value'] else '')
            if base=='许可':
                h=re.sub(r'(<summary>原文与许可</summary>)',r'\1'+f'<p>许可：{cell}</p>'.replace('\\','\\\\'),h,count=1); continue
            h=re.sub(r'(<tr><th>[^<]*'+base+r'[^<]*</th><td>)[^<]*未核[^<]*(</td></tr>)',lambda m:m.group(1)+cell+m.group(2),h)
            if base=='样本量' and x['value']: h=re.sub(r'n=[^<]*未核[^<]*','n='+E_(x['value']),h)
        if p.get('cebm_level'): h=h.replace('CEBM 等级未核','CEBM 等级 '+str(p['cebm_level']))
        rep='摘要未提及' if p.get('reading_depth')!='全文' else '原文未报告'
        _kn=re.search(r'<section class="kn">.*?</section>',h,re.S); _knh=_kn.group(0) if _kn else ''
        if _knh: h=h.replace(_knh,'\x00KN\x00',1)  # first-screen key numbers keep source wording verbatim
        h=h.replace('原文未给出',rep).replace('摘要未给出',rep)
        def coll(m):
            t=m.group(0); gone=[]
            def rr(x):
                if re.sub(r'<[^>]+>','',x.group(2)).strip() in ('原文未报告','摘要未提及'): gone.append(re.sub(r'<[^>]+>','',x.group(1))); return ''
                return x.group(0)
            t=re.sub(r'<tr><th>(.*?)</th><td>(.*?)</td></tr>',rr,t)
            if not gone: return t
            if '<tr>' not in t: t=''
            return t+(f'<p class="note">仅据摘要，其余细节见原文（{"、".join(gone)}）</p>' if rep=='摘要未提及' else f'<p class="note">以下项目原文未报告：{"、".join(gone)}</p>')
        h=re.sub(r'<table class="kv">.*?</table>',coll,h,flags=re.S)
        def coll2(m):
            t=m.group(0); n=len(re.findall(r'<td>(?:原文未报告|摘要未提及)</td>',t))
            if not n: return t
            t=re.sub(r'<td>(?:原文未报告|摘要未提及)</td>','<td></td>',t)
            return t+('<p class="note">空白处仅据摘要，其余细节见原文</p>' if rep=='摘要未提及' else '<p class="note">空白处原文未报告</p>')
        h=re.sub(r'<table(?! class="kv")[^>]*>.*?</table>',coll2,h,flags=re.S)
        if _knh: h=h.replace('\x00KN\x00',_knh,1)
        w(f'papers/{p["sid"]}/index.html',h)
        _tr=X.translation(p.get('pmid'),p.get('license')) if X.can_translate(p) else None
        if _tr: w(f'papers/{p["sid"]}/bilingual/index.html',X.bilingual_page(p,_tr,page)); MERGE.setdefault('bi',0); MERGE['bi']+=1
    os.makedirs(os.path.join(OUT,'static'),exist_ok=True); shutil.copy(os.path.join(ROOT,'static','preview','v.css'),os.path.join(OUT,'static','v.css'))
    import collections; print('templates',collections.Counter((p.get('population_type') or 'natural') for p in P.values()))
    print('merge',{k:(v if isinstance(v,int) else len(v)) for k,v in MERGE.items()},MERGE['sr_un'],MERGE['ap_un'])
    print(f'preview: {len(P)} papers, {len(VIS)} topics, {len(FRESH)} fresh -> {OUT}')
if __name__=='__main__': main()
