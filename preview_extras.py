"""Optional preview blocks fed by teammates' files. Each block hides if its file is absent.
Sources (synced into data/v5/extras/ by scripts/sync_extras.py from /workspace/vetlit/extracts):
  top_picks.json, related_reading.json, text_source.json, translations/<pmid>.json"""
import json, os, glob, html, re
E_=html.escape
D=os.path.join(os.path.dirname(os.path.abspath(__file__)),'data','v5','extras')
def _load(n):
    f=os.path.join(D,n)
    try: return json.load(open(f,encoding='utf-8'))
    except Exception: return None
TOP=_load('top_picks.json'); LA=_load('licence_audit.json'); REL=_load('related_reading.json'); TS=_load('text_source.json')
TR={}
try: TN=json.load(open(os.path.join(os.path.dirname(D),'translator_notes.json'),encoding='utf-8'))
except Exception: TN={}
for f in glob.glob(os.path.join(D,'translations','*.json')):
    try: t=json.load(open(f,encoding='utf-8')); TR[str(t.get('pmid') or os.path.basename(f)[:-5])]=t
    except Exception: pass
def _recs(x,key):
    if x is None: return {}
    if isinstance(x,dict) and isinstance(x.get(key),(list,dict)): x=x[key]
    if isinstance(x,dict): return {str(k):v for k,v in x.items()}
    return {str(r.get('pmid') or r.get('id')):r for r in x if isinstance(r,dict)}
def text_source(pmid):
    v=_recs(TS,'records').get(str(pmid))
    if isinstance(v,dict): v=v.get('text_source') or v.get('source')
    if not v: return None
    v=str(v).lower()
    if 'citation' in v: return '题录'
    return '全文' if ('full' in v or '全文' in v) else '摘要'
CCBY=re.compile(r'^cc[\s\-]?by(\s*[\d.]+)?$',re.I)
def ccby(lic): return bool(CCBY.match(str(lic or '').strip().replace('-4.0','').replace(' 4.0','')))
def _audit(pmid):
    v=_recs(LA,'records').get(str(pmid)) if LA else None
    return v.get('translation_ok') if isinstance(v,dict) else None
def can_translate(p):
    a=_audit(p.get('pmid'))
    return (a is True) if a is not None else p.get('fulltext_translation_allowed') is True
def translation(pmid,lic):
    t=TR.get(str(pmid))
    if not t: return None
    return t
def related_block(pmid,link):
    rs=_recs(REL,'records').get(str(pmid))
    if isinstance(rs,dict): rs=rs.get('related') or rs.get('items')
    if not rs: return ''
    li=''
    for r in rs[:5]:
        t=r.get('title_zh') or r.get('title') or ''
        if not t: continue
        href=link(r)
        why=r.get('reason') or r.get('basis') or ''
        meta=' · '.join(str(x) for x in [r.get('first_author'),r.get('journal'),r.get('year')] if x)
        li+=f'<li><a href="{E_(href)}">{E_(t)}</a><span class="m">{E_(meta)}{(" · "+E_(why)) if why else ""}</span></li>'
    if not li: return ''
    note=(REL.get('rule') if isinstance(REL,dict) else '') or '同专题、共同引用与关键词；外部条目来自 OpenAlex related_works，仅犬猫。'
    return f'<section class="blk"><h2 class="sec"><span>+</span> 相关阅读</h2><ul class="rows">{li}</ul><p class="note">{E_(note)}</p></section>'
def rule_text():
    return (TOP.get('rule') or TOP.get('rule_text') or '') if TOP else ''
def top_block(get,card):
    if not TOP: return ''
    rule=TOP.get('rule') or TOP.get('rule_text') or ''
    groups=TOP.get('topics') or TOP.get('groups') or TOP.get('picks') or []
    if isinstance(groups,dict): groups=[{'topic':k,'items':v} for k,v in groups.items()]
    out=''
    for g in groups:
        items=g.get('items') or g.get('picks') or g.get('papers') or []
        cards=''
        for it in items[:3]:
            pid=str(it.get('pmid') or it.get('id') if isinstance(it,dict) else it)
            p=get(pid)
            if p:
                c=card(p,'')
                rs=it.get('reason') if isinstance(it,dict) else ''
                sb=str(it.get('superseded_by') or '') if isinstance(it,dict) else ''
                q=get(sb) if sb else None
                if q: c=c.replace('</article>',f'<p class="note"><a class="tag2" href="papers/{E_(q["sid"])}/">已有更新版 →</a></p></article>',1)
                elif sb: c=c.replace('</article>',f'<p class="note"><a class="tag2" href="https://pubmed.ncbi.nlm.nih.gov/{E_(sb)}/">已有更新版 →</a></p></article>',1)
                if rs: c=c.replace('</article>',f'<p class="note">推荐理由：{E_(rs)}</p></article>',1)
                cards+=c
        if cards: out+=f'<h3 class="dg">{E_(g.get("topic_zh") or g.get("name_zh") or g.get("topic") or "")}</h3>'+cards
    if not out: return ''
    return f'<section><h2 class="sec"><span>00</span> 最新 / 最重要</h2>'+(f'<p class="note">按证据等级与时效排序 · <a href="about/ranking/">规则说明</a></p>' if rule else '')+out+'</section>'
def bilingual_page(p,t,page):
    paras=t.get('paragraphs') or t.get('segments') or []
    rows=''; sec=None
    for x in paras:
        s=x.get('section') or ''
        if s and s!=sec: rows+=f'<tr><th colspan="2" class="bsec">{E_(s)}{(" / "+E_(x["section_zh"])) if x.get("section_zh") else ""}</th></tr>'; sec=s
        if x.get('note_zh'): nt=f'<p class="tnote" style="background:#fff4d6;border-left:4px solid #e0a100;padding:.5em .8em;margin:.4em 0;color:#5a4300">{E_(x["note_zh"])}</p>'
        elif any(y.get('note_zh') for y in paras): nt=''
        else: nt=''.join(f'<p class="note tag2">{E_(n["note_zh"])}</p>' for n in TN.get(str(p.get('pmid')),[]) if n.get('match_en') and n['match_en'] in (x.get('en') or ''))
        rows+=f'<tr><td lang="en">{E_(x.get("en") or "")}</td><td lang="zh-CN">{E_(x.get("zh") or "")}{nt}</td></tr>'
    lic=t.get('license') or p.get('license') or ''
    a=t.get('attribution')
    if isinstance(a,dict):
        au=a.get('authors') or []
        a=f"{', '.join(au[:3])}{' 等' if len(au)>3 else ''}. {a.get('title','')}. {a.get('journal','')}, {a.get('year','')}"+(f" · 许可文本 {a['license_url']}" if a.get('license_url') else '')
    attr=a or f'{p.get("first_author","")} 等，{p.get("journal","")}，{p.get("year","")}'
    scope=t.get('scope_zh') or ''
    doi=p.get('doi')
    body=f'''<p class="crumb"><a href="../">← 返回速读</a></p><h1 class="ct">中英对照</h1><p class="en" lang="en">{E_(p.get("title",""))}</p>
<p class="note">原文：{E_(attr)}{f' · <a href="https://doi.org/{E_(doi)}">DOI</a>' if doi else ''} · 许可：{E_(str(lic).upper())}（本译文为改编作品，按同一署名要求发布）{(" · 翻译范围："+E_(scope)) if scope else ""}</p>
<p class="note tag2">AI 翻译，未经人工审校。如有出入以英文原文为准。</p>{(f'<p class="warn" style="background:#fff4d6;border-left:4px solid #e0a100;padding:.5em .8em;margin:.4em 0;color:#5a4300">{E_(p["warn_bilingual"])}</p>') if p.get('warn_bilingual') else ''}
<div class="tw"><table class="bi"><thead><tr><th>English（原文）</th><th>中文（AI 翻译）</th></tr></thead><tbody>{rows}</tbody></table></div>'''
    return page('中英对照 · '+(p.get('first_author') or ''),body,3)
