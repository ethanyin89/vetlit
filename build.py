"""Static site build: data/papers/*.json + content/*.md -> dist/. No dependencies (Python 3.9+)."""
import json, os, glob, html, re, shutil, datetime
ROOT=os.path.dirname(os.path.abspath(__file__)); DIST=os.path.join(ROOT,'dist')
SITE_URL=os.environ.get('SITE_URL','https://ethanyin89.github.io/vetlit').rstrip('/')
E_=html.escape
# ---------- minimal markdown ----------
def inline(s):
    s=E_(s,quote=False)
    s=re.sub(r'`([^`]+)`',r'<code>\1</code>',s)
    s=re.sub(r'\[([^\]]+)\]\((https?://[^)\s]+)\)',r'<a href="\2" rel="noopener">\1</a>',s)
    s=re.sub(r'\*\*(.+?)\*\*',r'<strong>\1</strong>',s)
    s=re.sub(r'(?<![\w*])\*(?!\s)(.+?)\*(?!\w)',r'<em>\1</em>',s)
    return s
def md(text):
    out=[];lines=text.split('\n');i=0
    while i<len(lines):
        l=lines[i]
        if not l.strip(): i+=1; continue
        if l.startswith('```'):
            j=i+1;buf=[]
            while j<len(lines) and not lines[j].startswith('```'): buf.append(lines[j]); j+=1
            out.append('<pre><code>'+E_('\n'.join(buf))+'</code></pre>'); i=j+1; continue
        m=re.match(r'(#{1,6})\s+(.*)',l)
        if m:
            n=len(m.group(1)); slug=re.sub(r'[^\w\u4e00-\u9fff]+','-',m.group(2)).strip('-')
            out.append(f'<h{n} id="{E_(slug)}">{inline(m.group(2))}</h{n}>'); i+=1; continue
        if re.match(r'^(-{3,}|\*{3,})$',l.strip()): out.append('<hr>'); i+=1; continue
        if l.lstrip().startswith('|'):
            rows=[]
            while i<len(lines) and lines[i].lstrip().startswith('|'): rows.append(lines[i].strip().strip('|')); i+=1
            cells=[ [c.strip() for c in re.split(r'(?<!\\)\|',r)] for r in rows]
            body=[c for c in cells[1:] if not all(re.match(r'^:?-+:?$',x) for x in c if x)] if len(cells)>1 else []
            t='<div class="tw"><table><thead><tr>'+''.join(f'<th>{inline(c)}</th>' for c in cells[0])+'</tr></thead><tbody>'
            t+=''.join('<tr>'+''.join(f'<td>{inline(c)}</td>' for c in r)+'</tr>' for r in body)+'</tbody></table></div>'
            out.append(t); continue
        if re.match(r'^\s*([-*]|\d+\.)\s+',l):
            tag='ol' if re.match(r'^\s*\d+\.',l) else 'ul'; items=[]
            while i<len(lines) and re.match(r'^\s*([-*]|\d+\.)\s+',lines[i]):
                items.append(re.sub(r'^\s*([-*]|\d+\.)\s+','',lines[i])); i+=1
                while i<len(lines) and lines[i].startswith('  ') and lines[i].strip() and not re.match(r'^\s*([-*]|\d+\.)\s+',lines[i]): items[-1]+=' '+lines[i].strip(); i+=1
            out.append(f'<{tag}>'+''.join(f'<li>{inline(x)}</li>' for x in items)+f'</{tag}>'); continue
        if l.startswith('>'):
            buf=[]
            while i<len(lines) and lines[i].startswith('>'): buf.append(lines[i][1:].strip()); i+=1
            out.append('<blockquote>'+md('\n'.join(buf))+'</blockquote>'); continue
        buf=[]
        while i<len(lines) and lines[i].strip() and not re.match(r'^(#|\||```|>|\s*([-*]|\d+\.)\s)',lines[i]): buf.append(inline(lines[i])); i+=1
        if buf: out.append('<p>'+'<br>'.join(buf)+'</p>')
        else: out.append('<p>'+inline(l)+'</p>'); i+=1
    return '\n'.join(out)
def strip_legacy_grades(text):
    """Remove the retired custom A–D/共识 grades from deep-extract pages (source files left untouched)."""
    out=[];skip=False
    for l in text.split('\n'):
        if l.startswith('**证据等级'):
            out.append('> 原速读页中的自定义证据等级（A–D）已按 2026-11-02 决定移除；本文献待按 Oxford CEBM 2011 与偏倚风险工具重评。'); skip=True; continue
        if skip and l.startswith('- '): continue
        skip=False
        if '证据等级 A"按模板' in l: continue
        l=l.replace('## 1. 一句话结论 + 证据等级','## 1. 一句话结论').replace('成立（A 级）','成立')
        out.append(l)
    return '\n'.join(out)
# ---------- data ----------
SPEC={'肾脏':'肾病','行为/认知':'行为与认知','流行病学（日本）':'日本流行病学','心脏':'心血管'}
def split(v): return [x.strip() for x in re.split(r'[/;；]',v or '') if x.strip()]
def tri(v): return True if v=='是' else False if v=='否' else None
def view(c):
    """Adapter: canonical (Vibe Feline 25-field) record -> render view. Canonical data is never modified."""
    p=dict(c)
    p['pmid']=c.get('pmid') or ''
    p['species']=split(c.get('species')); p['specialty']=[SPEC.get(x,x) for x in split(c.get('specialty'))]
    p['year']=int(re.sub(r'\D','',str(c.get('year')))[:4] or 0); p['date']=str(c.get('date') or c.get('year'))
    lv=c.get('cebm_level') or '待评'
    p['cebm_display']=('Level '+lv) if re.match(r'^[1-5]',lv) else lv
    p['cebm_basis']='；'.join(x for x in [c.get('cebm_question') if c.get('cebm_question') not in (None,'','—') else '', c.get('cebm_basis') or ''] if x)
    p['rob_tool']=c.get('rob_tool') or '待评'
    p['rob_overall']=c.get('rob_judgement') or '待评'
    p['reporting']=c.get('reporting_checklist') or '待评'
    p['is_guideline']='指南' in (c.get('doc_type') or '') or '共识' in (c.get('doc_type') or '')
    p['oa_bool']=tri(c.get('oa'))
    p['verified_label']='全文已核' if c.get('verified')=='yes' else '摘要级'
    return p
def load():
    return [view(json.load(open(f,encoding='utf-8'))) for f in sorted(glob.glob(os.path.join(ROOT,'data','papers','*.json')))]
def authors_short(p): return p.get('first_author','')+(' et al.' if p.get('first_author') else '')
def bibkey(p): return re.sub(r'\W','',(p.get('first_author') or 'anon').split()[0])+str(p['year'])+'_'+(p['pmid'] or re.sub(r'\W','',p['id']))
def bibtex(p):
    f=[('title','{'+p['title']+'}'),('author',p.get('first_author','')+' and others'),('journal',p.get('journal','')),('year',str(p['year'])),('doi',p.get('doi','')),('pmid',p['pmid'])]
    return '@article{'+bibkey(p)+',\n'+',\n'.join(f'  {k} = {{{v}}}' for k,v in f if v)+'\n}\n'
def ris(p):
    r=['TY  - JOUR',f"TI  - {p['title']}",f"AU  - {p.get('first_author','')}",f"JO  - {p.get('journal','')}",f"PY  - {p['year']}"]
    if p.get('doi'): r.append(f"DO  - {p['doi']}")
    if p['pmid']: r+= [f"AN  - PMID:{p['pmid']}",f"UR  - https://pubmed.ncbi.nlm.nih.gov/{p['pmid']}/"]
    r.append('ER  - ')
    return '\n'.join(r)+'\n'
def gb(g,st=None):
    cls={'A':'ga','B':'gb','C':'gc','D':'gd','共识':'gk','不适用':'gn'}.get(g,'gn')
    s=f'<span class="badge {cls}">{E_(str(g))}</span>'
    if st and st!='已定': s+=f'<span class="flag">{E_(st)}</span>'
    return s
def oa_txt(p):
    if p.get('oa_bool') is True: return '开放获取'
    if p.get('oa_bool') is False: return '非 OA'
    return 'OA 未核'
NAV=[('index.html','文献'),('rules/index.html','证据评价方法'),('about/index.html','方法与声明'),('feed.xml','RSS')]
def page(title,body,depth,desc='犬猫兽医文献专业速读：证据分级、方法学审读、中英对照'):
    r='../'*depth
    nav=''.join(f'<a href="{r}{h}">{t}</a>' for h,t in NAV)
    return f'''<!doctype html><html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E_(title)} · 宠物医学文献速读</title><meta name="description" content="{E_(desc)}"><link rel="stylesheet" href="{r}static/style.css">
<link rel="alternate" type="application/rss+xml" title="宠物医学文献速读" href="{r}feed.xml"></head><body>
<a class="skip" href="#main">跳到正文</a><header class="top"><a class="brand" href="{r}index.html">宠物医学文献速读 <small>VetLit · 犬猫</small></a><nav aria-label="主导航">{nav}</nav></header>
<main id="main">{body}</main><footer>仅供专业参考，不构成临床诊疗建议。数据与分级见 <a href="{r}rules/index.html">规则</a> · <a href="{r}about/index.html">方法</a> · 构建于 {datetime.date.today().isoformat()}</footer></body></html>'''
def field(label,v):
    if v in (None,'',[]): return ''
    if isinstance(v,list): v='<ul>'+''.join(f'<li>{E_(x if isinstance(x,str) else json.dumps(x,ensure_ascii=False))}</li>' for x in v)+'</ul>'
    elif isinstance(v,bool): v='是' if v else '否'
    else: v=E_(str(v))
    return f'<tr><th scope="row">{label}</th><td>{v}</td></tr>'
def errata_html(es):
    if not es: return ''
    li=''
    for e in es:
        ref=' · '.join(x for x in [f"PMID <a href=\"https://pubmed.ncbi.nlm.nih.gov/{e['pmid']}/\">{e['pmid']}</a>" if e.get('pmid') else '', f"DOI <a href=\"https://doi.org/{e['doi']}\">{E_(e['doi'])}</a>" if e.get('doi') else ''] if x)
        li+=f"<li><strong>{E_(e.get('type','勘误'))}</strong> {ref}：{E_(e.get('note',''))}</li>"
    return f'<section class="callout warn"><h2>勘误与更正</h2><ul>{li}</ul></section>'
def mc_html(v):
    if not v: return ''
    s=E_(v)
    return s.replace('推断','<mark class="infer" title="由摘要推断，未经全文核实">推断</mark>')
def detail(p):
    tags=(['厂商资助'] if p.get('funding') and '未核' not in p['funding'] and '非厂商' not in p['funding'] and any(x in p['funding'] for x in ['Boehringer','Purina','Mars','Hill','Royal Canin','Zoetis','Elanco']) else [])
    guideline='指南' in (p.get('doc_type') or '') or '共识' in (p.get('doc_type') or '')
    links=[f'<a href="https://pubmed.ncbi.nlm.nih.gov/{p["pmid"]}/">PubMed {p["pmid"]}</a>' if p['pmid'] else '',
           f'<a href="https://doi.org/{E_(p["doi"])}">DOI</a>' if p.get('doi') else '',
           f'<a href="https://europepmc.org/article/PMC/{p["pmcid"]}">Europe PMC 全文</a>' if p.get('pmcid') else '',
           f'来源：{E_(p["source"])}' if p.get('source') and 'PubMed' not in p['source'] else '',
           '<a href="cite.bib" download>BibTeX</a>','<a href="cite.ris" download>RIS</a>']
    head=f'''<p class="crumb"><a href="../../index.html">文献</a> / {E_(p.get('first_author',''))} {p['year']}</p>
<h1 lang="en">{E_(p['title'])}</h1>{f'<p class="zh">{E_(p["title_zh"])}</p>' if p.get('title_zh') else ''}
<p class="meta">{E_(authors_short(p))} · <em>{E_(p.get('journal',''))}</em> · {E_(p['date'])} · <span class="pill ev">CEBM 2011：{E_(p['cebm_display'])}</span> <span class="pill ev">偏倚风险：{E_(p['rob_overall'])}</span> <span class="pill">{E_(p.get('doc_type',''))}</span> <span class="pill {'ok' if p['verified_label']=='全文已核' else ''}">{p['verified_label']}</span> <span class="pill">{oa_txt(p)}</span> {''.join(f'<span class="pill tag">{E_(t)}</span>' for t in tags)} {'<span class="pill pend">待处理</span>' if p.get('status')=='待处理' else ''}</p>
<p class="links">{' · '.join(x for x in links if x)}</p>'''
    one=f'<p class="one"><strong>一句话结论：</strong>{E_(p["one_line_conclusion_zh"])}</p>' if p.get('one_line_conclusion_zh') else ''
    gr=p.get('guideline_recommendation')
    cebm_txt=p['cebm_display']+(f"（{p['cebm_basis']}）" if p['cebm_basis'] else '')
    ev=f'''<section class="card"><h2>证据评价（每项注明工具；各维度分开，不合成总分）</h2><table class="kv">
<tr><th scope="row">证据水平</th><td>{E_(cebm_txt)}<br><small>工具：<a href="https://www.cebm.ox.ac.uk/resources/levels-of-evidence/ocebm-levels-of-evidence">Oxford CEBM Levels of Evidence 2011</a>（按设计记录原始 Level，不作上/下调）</small></td></tr>
<tr><th scope="row">偏倚风险</th><td>工具：{E_(p['rob_tool'])}<br>判断：<strong>{E_(p['rob_overall'])}</strong>{f'<br><small>{E_(p["rob_rationale"])}</small>' if p.get('rob_rationale') else ''}</td></tr>
<tr><th scope="row">报告规范清单</th><td>{E_(p['reporting'])}<br><small>适用清单，不代表已逐项核对符合度</small></td></tr>
{f'<tr><th scope="row">指南推荐强度（原文）</th><td>{E_(gr)}</td></tr>' if gr and gr!='不适用' else ''}
</table></section>'''
    rows=''.join([field('文献类型',p.get('doc_type')),field('研究设计',p.get('design')),field('物种',' / '.join(p['species'])),field('专科',' / '.join(p['specialty'])),
        field('实际分析样本量',p.get('sample_size_analysed')),
        f'<tr><th scope="row">多中心</th><td>{mc_html(p.get("multicenter"))}</td></tr>' if p.get('multicenter') else '',
        field('临床可用性',p.get('clinical_utility')),field('资助方',p.get('funding')),field('推荐依据',p.get('recommendation_basis')),field('推荐依据（细节）',p.get('recommendation_basis_detail')),
        field('核对级别',p['verified_label']),field('日本来源',p.get('japan_source')),field('数据来源',', '.join(p.get('provenance',[])))])
    gsec=''
    if guideline:
        g=[('适用范围','scope'),('核心推荐（附推荐强度）','core_recommendations'),('证据薄弱点','evidence_gaps'),('与旧版相比的变化','changes_vs_previous')]
        gsec='<section class="card"><h2>指南速读模板</h2><table class="kv">'+''.join(field(l,p.get(k)) or f'<tr><th scope="row">{l}</th><td class="muted">待按指南模板整理</td></tr>' for l,k in g)+'</table></section>'
    er=p.get('errata_detail') or ([{'type':'勘误/更正','pmid':p['errata']}] if p.get('errata') else [])
    ic=p.get('internal_inconsistency_detail') or ([p['internal_inconsistency']] if p.get('internal_inconsistency') else [])
    contra='<section class="callout warn"><h2>论文内部矛盾</h2><ul>'+''.join(f'<li>{E_(x)}</li>' for x in ic)+'</ul></section>' if ic else ''
    body=head+one+ev+f'<section class="card"><h2>{"指南信息" if guideline else "研究卡片"}（结构化数据）</h2><table class="kv">{rows}</table></section>'+gsec+errata_html(er)+contra
    if p.get('detail') and os.path.exists(os.path.join(ROOT,'content',p['detail'])):
        note='<p class="callout">以下为 deep extract 速读页原文。原页中的自定义等级已移除；证据评价以上方“证据评价”栏为准。</p>'
        body+='<article class="prose">'+note+md(strip_legacy_grades(open(os.path.join(ROOT,'content',p['detail']),encoding='utf-8').read()))+'</article>'
    else:
        body+='<p class="callout">深度速读页尚未完成（仅书目与分级数据）。请以原文为准。</p>'
    return page(f"{p.get('first_author','')} {p['year']}",body,2,desc=p['title'])
def index(ps):
    data=[{k:p.get(k) for k in ('id','title','title_zh','first_author','year','date','journal','species','specialty','cebm_display','rob_overall','rob_tool','oa_bool','doc_type','sample_size_analysed','status','clinical_utility','verified_label','one_line_conclusion_zh','pmid')}|{'has_detail':bool(p.get('detail'))} for p in ps]
    specs=sorted({s for p in ps for s in p['specialty']}); dts=sorted({p.get('doc_type') or '' for p in ps}-{''}); cebms=sorted({p['cebm_display'] for p in ps})
    opt=lambda xs:''.join(f'<option value="{E_(x)}">{E_(x)}</option>' for x in xs)
    body=f'''<h1>犬猫兽医文献 · 专业速读</h1><p class="lede">{len(ps)} 篇 · 每篇注明证据水平（Oxford CEBM 2011）、偏倚风险工具与报告规范；已精读者附方法学审读。<strong>不构成临床建议。</strong></p>
<div class="tabs" role="tablist"><button role="tab" aria-selected="true" data-sort="new">最新</button><button role="tab" aria-selected="false" data-sort="imp">重要</button></div>
<form class="filters" onsubmit="return false"><label>搜索<input id="q" type="search" placeholder="标题、作者、期刊、PMID"></label>
<label>物种<select id="sp"><option value="">全部</option>{opt(['猫','犬'])}</select></label><label>专科<select id="spec"><option value="">全部</option>{opt(specs)}</select></label>
<label>文献类型<select id="dt"><option value="">全部</option>{opt(dts)}</select></label><label>CEBM 2011<select id="gr"><option value="">全部</option>{opt(cebms)}</select></label><label class="chk"><input id="oa" type="checkbox"> 仅开放获取</label></form>
<p class="actions"><span id="count"></span> · 导出全部：<a href="export/all.bib" download>BibTeX</a> · <a href="export/all.ris" download>RIS</a> · 导出当前筛选：<a href="#" id="exb">BibTeX</a> · <a href="#" id="exr">RIS</a></p>
<ol id="list" class="list"></ol><noscript><ul>{''.join(f'<li><a href="papers/{p["id"]}/index.html">{E_(p["title"])}</a></li>' for p in ps)}</ul></noscript>
<script>window.PAPERS={json.dumps(data,ensure_ascii=False)};window.CITE={json.dumps({p['id']:[bibtex(p),ris(p)] for p in ps},ensure_ascii=False)};</script><script src="static/app.js"></script>'''
    return page('文献',body,0)
def rules():
    return page('证据评价方法',md(open(os.path.join(ROOT,'content','_rules.md'),encoding='utf-8').read()),1)
def about():
    return page('方法与声明',md(open(os.path.join(ROOT,'content','_about.md'),encoding='utf-8').read()),1)
def rss(ps):
    items=sorted(ps,key=lambda p:p['date'],reverse=True)[:50]
    it=''.join(f'''<item><title>{E_(p['title'])}</title><link>{SITE_URL}/papers/{p['id']}/index.html</link><guid>{SITE_URL}/papers/{p['id']}/</guid><description>{E_(f"{p.get('journal','')} {p['date']} · {p.get('doc_type','')} · CEBM 2011：{p['cebm_display']}")}</description></item>''' for p in items)
    return f'<?xml version="1.0" encoding="UTF-8"?><rss version="2.0"><channel><title>宠物医学文献速读</title><link>{SITE_URL}/</link><description>犬猫兽医文献专业速读</description><language>zh-cn</language>{it}</channel></rss>'
def w(path,s):
    os.makedirs(os.path.dirname(path),exist_ok=True); open(path,'w',encoding='utf-8').write(s)
def main():
    ps=load(); shutil.rmtree(DIST,ignore_errors=True); shutil.copytree(os.path.join(ROOT,'static'),os.path.join(DIST,'static'))
    w(os.path.join(DIST,'index.html'),index(ps)); w(os.path.join(DIST,'rules','index.html'),rules()); w(os.path.join(DIST,'about','index.html'),about())
    w(os.path.join(DIST,'feed.xml'),rss(ps)); w(os.path.join(DIST,'export','all.bib'),''.join(bibtex(p) for p in ps)); w(os.path.join(DIST,'export','all.ris'),'\n'.join(ris(p) for p in ps))
    LEG={'evidence_grade','grade_v1','grade_reason','downgrade_tags','grade_status','grade_label'}
    w(os.path.join(DIST,'papers.json'),json.dumps([{k:v for k,v in p.items() if k not in LEG} for p in ps],ensure_ascii=False,indent=1)); w(os.path.join(DIST,'.nojekyll'),'')
    for p in ps:
        d=os.path.join(DIST,'papers',p['id']); w(os.path.join(d,'index.html'),detail(p)); w(os.path.join(d,'cite.bib'),bibtex(p)); w(os.path.join(d,'cite.ris'),ris(p))
    print(f'built {len(ps)} papers -> dist/')
if __name__=='__main__': main()
