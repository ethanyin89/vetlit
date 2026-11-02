"""Preview build (redesign, cindy.app tokens): data/v5 + data/papers + content -> dist/preview/. Root site untouched."""
import json, os, glob, re, html, datetime, shutil
import build as B
ROOT=B.ROOT; OUT=os.path.join(B.DIST,'preview'); E_=html.escape
def clean(s):
    s=str(s or '')
    s=re.sub(r'[。；，]?\s*(数据)?来源[:：]\s*(deep extract|Vibe Feline|vibe-feline)[^。；|\n]*','',s,flags=re.I)
    s=re.sub(r'(deep extract|Vibe Feline|vibe-feline-v\d)','AI 速读',s,flags=re.I)
    s=re.sub(r'([。，；：！？、])\1+',r'\1',s)
    return s.replace('。）','）').strip()
EMPTY={'','未核','不适用','—','-','None'}
def has(v): return v not in (None,[],{}) and str(v).strip() not in EMPTY
# ---------- data ----------
v5=json.load(open(os.path.join(ROOT,'data','v5','seed_library_v5.json'),encoding='utf-8'))
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
for r in json.load(open(os.path.join(ROOT,'data','v5','appraisal_papers.json'),encoding='utf-8')):
    p=matcher(r)
    if not p: MERGE['ap_un'].append(r.get('pmid') or r.get('id')); continue
    MERGE['ap']+=1
    p['rob_tool']=r.get('appraisal_tool') or ''; p['appraisal_items']=r.get('appraisal_items') or []
    p['appraisal_note']=r.get('appraisal_note') or ''
    for k in ('rob_judgement','rob_rationale'): p.pop(k,None)
MERGE['pg']=0; MERGE['pg_un']=[]
for k,r in json.load(open(os.path.join(ROOT,'data','v5','pages38_fields.json'),encoding='utf-8')).items():
    r.setdefault('pmid',k); p=matcher(r)
    if not p: MERGE['pg_un'].append(k); continue
    MERGE['pg']+=1
    p['can_say']=[STRIP(x) for x in r.get('can_say') or []]; p['cannot_say']=[STRIP(x) for x in r.get('cannot_say') or []]
    f='extracts38/'+os.path.basename(r.get('page_file') or k+'.md')
    if os.path.exists(os.path.join(ROOT,'content',f)): p['detail']=f; p['p38']=True
    if not p.get('reading_depth'): p['reading_depth']='摘要'
# hidden pending verification
HIDE_KR={('23078651','到达主要终点比例')}
for p in P.values():
    p['key_results']=[k for k in (p.get('key_results') or []) if (str(p.get('pmid')),k.get('measure')) not in HIDE_KR]
def get(i): return P.get(i) or SID.get(i) or SID.get('pmid-'+str(i))
SPEC={'肾脏':'肾脏','心脏':'心脏','感染':'感染','行为/认知':'行为与认知','营养':'营养','内分泌':'内分泌'}
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
DEPTH={'全文':'全文已读','摘要':'已读摘要','仅标题':'仅题录'}
def badges(p):
    b=[('k',p.get('design_category'))]
    n=p.get('n_analysed')
    if has(n) and len(str(n))<=14: b.append(('',f'n={n}'))
    if level(p).startswith('Level'): b.append(('lv','CEBM '+level(p)))
    if p.get('reading_depth'): b.append(('',DEPTH.get(p['reading_depth'],p['reading_depth'])))
    return '<p class="bd">'+''.join(f'<span class="b {c}">{E_(str(t))}</span>' for c,t in b if t)+'</p>'
def title_html(p,tag='h3',href=None):
    main=p.get('title_zh') or p.get('one_line_conclusion_zh')
    t=E_(clean(main)) if main else f'<span lang="en">{E_(p["title"])}</span>'
    if href: t=f'<a href="{href}">{t}</a>'
    sub=f'<p class="en" lang="en">{E_(p["title"])}</p>' if main else ''
    return f'<{tag} class="ct">{t}</{tag}>'+sub
def card(p,r):
    href=f'{r}papers/{p["sid"]}/'
    bl=f'<p class="bl"><span class="eb">底线</span>{E_(clean(p["one_line_conclusion_zh"]))}</p>' if p.get('title_zh') and p.get('one_line_conclusion_zh') else ''
    lab=' · '.join(x for x in [' / '.join(specs(p)),species(p)] if x)
    return f'''<article class="card"><p class="eb">{E_(lab)}</p>{title_html(p,'h3',href)}{bl}{badges(p)}<p class="ft"><span><em>{E_(p.get("journal",""))}</em> · {E_(str(p.get("year","")))}</span><a class="go" href="{href}">阅读速读 →</a></p></article>'''
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
    nav=''.join(f'<a href="{r}{h}"{" aria-current=page" if k==cur_nav else ""}>{t}</a>' for k,h,t in [('home','','本周'),('topics','topics/','专题'),('lib','library/','文献库'),('about','../about/index.html','方法')])
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="robots" content="noindex,nofollow">
<title>{E_(title)} · VetLit 预览</title>{FONTS}<link rel="stylesheet" href="{r}static/v.css"></head><body>
<header class="top"><div class="in"><a class="brand" href="{r}">VETLIT<i>.</i></a><nav>{nav}</nav></div></header>
<div class="pv">预览版 · 改版中，正式站点仍在 <a href="{r}../">原址</a></div>
<main class="wrap">{body}</main>
<footer class="foot"><div class="in">犬猫兽医文献速读 · 仅供专业参考，不构成诊疗建议 · 速读由 AI 撰写，单人评估，未双人复核 · 构建于 {datetime.date.today().isoformat()}</div></footer></body></html>'''
# ---------- home ----------
ALL=sorted(P.values(),key=lambda p:p.get('importance_rank') or 999)
def home():
    picks=ALL[:8]
    new=sorted(P.values(),key=lambda p:p.get('pub_date') or '',reverse=True)[:10]
    groups={}
    for p in new: groups.setdefault((p.get('pub_date') or '')[:7],[]).append(p)
    gl=''.join(f'<h3 class="dg">{E_(k[:4])} 年 {int(k[5:7])} 月</h3>'+''.join(card(p,'') for p in v) for k,v in groups.items() if k)
    chips=topic_chips('')
    wk=datetime.date.today().isocalendar()
    body=f'''<section class="hero"><p class="eb red">// {wk[0]} 第 {wk[1]} 周</p><h1>本周精选</h1><p class="lede">犬猫兽医文献，结论先行。每篇注明研究设计、Oxford CEBM 2011 证据等级与阅读深度。</p></section>
<section><h2 class="sec"><span>01</span> 编辑精选</h2><p class="note">按指南/共识 → 证据等级 → 发表时间排序。</p>{''.join(card(p,'') for p in picks)}</section>
<section><h2 class="sec"><span>02</span> 最新发表</h2>{gl}</section>
<section><h2 class="sec"><span>03</span> 按专题浏览</h2>{chips}</section>
<p class="more"><a class="btn" href="library/">进入文献库（{len(P)} 篇）→</a></p>{fresh_list(FRESH,'')}'''
    return page('本周精选',body,0,'home')
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
REAL=lambda t: bool(t.get('bottom_line')) and t.get('bottom_line_clinical') is not False and '自动生成' not in (t.get('bottom_line_source') or '')
def topic_page(t):
    ps=tpapers(t); r='../../'
    crumb=f'<p class="crumb"><a href="{r}topics/">专题</a>'+(f' › <a href="{r}topics/{t["parent"]}/">{E_(TBY[t["parent"]]["name_zh"])}</a>' if t.get('parent') else '')+'</p>'
    bl=f'<section class="bottom"><p class="eb red">临床底线 · 单人草稿·未经临床兽医审阅</p><p>{E_(clean(t["bottom_line"]))}</p></section>' if REAL(t) else ''
    core=[(get(c['id']),c.get('reason')) for c in (t.get('core') or [])]
    if not t.get('core') and not t.get('all_ids'):
        core=[(p,None) for p in sorted(ps,key=lambda p:p.get('importance_rank') or 999)[:8]]
    core=[(p,why) for p,why in core if p]
    cs=''.join(card(p,r).replace('<p class="bd">',f'<p class="why">入选：{E_(clean(why))}</p><p class="bd">',1) if why else card(p,r) for p,why in core)
    newest=[get(i['id'] if isinstance(i,dict) else i) for i in (t.get('newest') or [])] or sorted(ps,key=lambda p:p.get('pub_date') or '',reverse=True)[:5]
    ks=[k for k in VIS if k.get('parent')==t['id']]
    sub=f'<section><h2 class="sec"><span>//</span> 子专题</h2>'+''.join(f'<a class="chip" href="{r}topics/{k["id"]}/">{E_(k["name_zh"])} <b>{len(tpapers(k))}</b></a>' for k in ks)+'</section>' if ks else ''
    fr=[f for f in FRESH if t['id'] in (f.get('topics') or [])]
    body=f'''{crumb}<section class="hero"><p class="eb">{E_(t.get("name_en",""))}</p><h1>{E_(t["name_zh"])}</h1><p class="lede">{len(ps)} 篇已速读文献</p></section>{bl}{sub}
<section><h2 class="sec"><span>01</span> 核心文献</h2>{cs}</section>
<section><h2 class="sec"><span>02</span> 最新</h2><ul class="rows">{''.join(row(p,r) for p in newest if p)}</ul></section>
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
def paper(p):
    r='../../'; S=sections(p)
    head=f'''<p class="crumb"><a href="{r}library/">文献库</a>{"".join(f' › <a href="{r}topics/{t}/">{E_(TBY[t]["name_zh"])}</a>' for t in (p.get("topics") or [])[:1] if t in TBY and t in [v["id"] for v in VIS])}</p>
<p class="eb">{E_(" / ".join(specs(p)))} · {E_(species(p))}</p>{title_html(p,'h1')}
<p class="meta">{E_(p.get("first_author",""))} 等 · <em>{E_(p.get("journal",""))}</em> · {E_(p.get("pub_date") or str(p.get("year","")))}{f' · <a href="https://doi.org/{E_(p["doi"])}">DOI</a>' if p.get('doi') else ''}{f' · <a href="https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/">PubMed</a>' if p.get('pmid') else ''}{f' · <a href="https://europepmc.org/article/PMC/{p["pmcid"]}">全文</a>' if p.get('pmcid') else ''}</p>{badges(p)}
<p>{"".join(f'<a class="chip" href="{r}topics/{t}/">{E_(TBY[t]["name_zh"])}</a>' for t in (p.get("topics") or []) if t in TBY and TBY[t] in VIS)}</p>'''
    blk=lambda n,t,c: f'<section class="blk"><h2 class="sec"><span>{n}</span> {t}</h2>{c}</section>' if c else ''
    bl=f'<section class="bottom"><p class="eb red">底线</p><p>{E_(clean(p["one_line_conclusion_zh"]))}</p>{f'<p class="note">{E_(clean(p["confidence_sentence"]))}</p>' if has(p.get('confidence_sentence')) else ''}</section>' if p.get('one_line_conclusion_zh') and p.get('title_zh') else ''
    why=f'<p>{E_(clean(p["why_it_matters"]))}</p>' if has(p.get('why_it_matters')) else ''
    sc=p.get('study_card') or {}
    snap=[('设计',p.get('design_detail') or p.get('design')),('物种',species(p)),('入组样本量',p.get('n_enrolled')),('分析样本量',p.get('n_analysed')),('中心',sc.get('单/多中心')),('资助与利益冲突',sc.get('资助') or p.get('funding'))]
    snap=''.join(f'<tr><th>{k}</th><td>{E_(clean(v))}</td></tr>' for k,v in snap if has(v))
    snap=f'<table class="kv">{snap}</table>' if snap else ''
    PH={'','—','-','–','None'}
    krs=[k for k in (p.get('key_results') or []) if any(str(k.get(f) or '').strip() not in PH for f in ('groups','effect_ci','p'))]
    cell=lambda v: '' if str(v or '').strip() in PH else E_(clean(v))
    if krs:
        kr='<div class="tw"><table><thead><tr><th>指标</th><th>组别/数值</th><th>效应量（95% CI）</th><th>P</th></tr></thead><tbody>'+''.join(f'<tr><td>{cell(k.get("measure"))}</td><td>{cell(k.get("groups"))}</td><td>{cell(k.get("effect_ci"))}</td><td>{cell(k.get("p"))}</td></tr>' for k in krs)+'</tbody></table></div>'
    else: kr=sec_get(S,'关键结果')
    if krs: pass
    else: kr=mdc(kr) if kr and not re.fullmatch(r'[\s—\-|指标结果统计:]*',kr) else (f'<p>{E_(clean(p["results"]))}</p>' if has(p.get('results')) else '')
    cs='' if p.get('p38') else sec_get(S,'能说')
    cs=mdc(cs) if cs else ''
    if not cs and p.get('can_say') and '见页面' not in str(p['can_say']):
        cs='<h3>能说</h3><ul>'+''.join(f'<li>{E_(clean(x))}</li>' for x in p['can_say'])+'</ul><h3>不能说</h3><ul>'+''.join(f'<li>{E_(clean(x))}</li>' for x in p.get('cannot_say') or [])+'</ul>'
    cs=cs.replace('<p><strong>能说</strong></p>','<h3>能说</h3>').replace('<p><strong>不能说</strong></p>','<h3>不能说</h3>')
    lv=str(p.get('cebm_level') or '')
    ev=[('Oxford CEBM 2011',lv+(f'（{p["cebm_basis"]}）' if has(p.get('cebm_basis')) else '')),('偏倚/质量工具',p.get('rob_tool')),('偏倚风险说明',p.get('appraisal_note')),('报告规范',p.get('reporting_checklist')),('报告规范核查',p.get('reporting_notes')),('指南推荐强度（原文）',p.get('guideline_recommendation') if p.get('design_category')=='指南/共识' else '')]
    er=p.get('errata'); er=', '.join(er) if isinstance(er,list) else er
    if has(er): ev.append(('勘误',f'PMID {er}'))
    if has(p.get('internal_inconsistency')): ev.append(('论文内部不一致',p['internal_inconsistency']))
    evt='<table class="kv">'+''.join(f'<tr><th>{k}</th><td>{E_(clean(v))}</td></tr>' for k,v in ev if has(v))+'</table>'+appraisal(p)
    terms=sec_get(S,'关键术语')
    if p.get('fulltext_translation_allowed') is True:
        orig=f'<p>许可 {E_(str(p.get("license","")).upper())} 允许全文翻译；逐段中英对照译文尚未生成。</p>'
    else:
        orig=f'<p>许可{("（"+E_(str(p["license"]))+"）") if has(p.get("license")) else ""}不允许全文翻译转载，本站只提供速读与术语对照。</p>'
    bib=B.bibtex(B.view({**p,'id':p['sid']})); ris=B.ris(B.view({**p,'id':p['sid']}))
    gaps=[k for k,f in [('资助','funding'),('多中心','multicenter'),('分析样本量','n_analysed'),('推荐依据','recommendation_basis')] if p.get(f)=='未核']
    parts=[('为什么重要',why),('研究快照',snap),('关键结果',kr),('能说 / 不能说',cs)]
    parts=[x for x in parts if x[1]]
    body=head+bl+''.join(blk(f'{n:02d}',t,c) for n,(t,c) in enumerate(parts,1))
    body+=f'<details class="fold"><summary>证据评价</summary>{evt}</details>'
    if terms: body+=f'<details class="fold"><summary>关键术语中英对照</summary>{mdc(terms)}</details>'
    body+=f'<details class="fold"><summary>原文与许可</summary>{orig}</details><details class="fold"><summary>引用（BibTeX / RIS）</summary><pre>{E_(bib)}</pre><pre>{E_(ris)}</pre></details>'
    body+=f'<p class="note sig">速读：AI 撰写，单人评估，未双人复核 · 阅读深度：{E_(DEPTH.get(p.get("reading_depth"),"尚未速读"))}{" · 未核项："+"、".join(gaps) if gaps else ""}</p>'
    return page(clean(p.get('title_zh') or p.get('first_author','')+' '+str(p.get('year',''))),body,2)
def w(rel,s):
    f=os.path.join(OUT,rel); os.makedirs(os.path.dirname(f),exist_ok=True); open(f,'w',encoding='utf-8').write(s)
def main():
    shutil.rmtree(OUT,ignore_errors=True)
    w('index.html',home()); w('library/index.html',library()); w('topics/index.html',topics_index())
    for t in VIS: w(f'topics/{t["id"]}/index.html',topic_page(t))
    for p in P.values(): w(f'papers/{p["sid"]}/index.html',paper(p))
    os.makedirs(os.path.join(OUT,'static'),exist_ok=True); shutil.copy(os.path.join(ROOT,'static','preview','v.css'),os.path.join(OUT,'static','v.css'))
    print('merge',{k:(v if isinstance(v,int) else len(v)) for k,v in MERGE.items()},MERGE['sr_un'],MERGE['ap_un'])
    print(f'preview: {len(P)} papers, {len(VIS)} topics, {len(FRESH)} fresh -> {OUT}')
if __name__=='__main__': main()
