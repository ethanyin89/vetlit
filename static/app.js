(function(){
var P=window.PAPERS,C=window.CITE,$=function(i){return document.getElementById(i)},sort='new';
var CU={'改变诊疗':0,'提示性':1,'背景':2};
function esc(s){return String(s==null?'':s).replace(/[&<>"]/g,function(c){return{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]})}
function cur(){var q=$('q').value.trim().toLowerCase(),sp=$('sp').value,spec=$('spec').value,gr=$('gr').value,dt=$('dt').value,oa=$('oa').checked;
 var r=P.filter(function(p){
  if(sp&&p.species.indexOf(sp)<0)return false; if(spec&&p.specialty.indexOf(spec)<0)return false;
  if(gr&&p.cebm_display!==gr)return false; if(dt&&p.doc_type!==dt)return false;
  if(oa&&p.oa_bool!==true)return false;
  if(q&&[p.title,p.title_zh,p.first_author,p.journal,p.pmid,p.one_line_conclusion_zh].join(' ').toLowerCase().indexOf(q)<0)return false;return true});
 r.sort(sort==='new'?function(a,b){return String(b.date).localeCompare(String(a.date))}:function(a,b){
  return ((CU[a.clinical_utility]||3)-(CU[b.clinical_utility]||3))||(b.has_detail-a.has_detail)||String(b.date).localeCompare(String(a.date))});
 return r}
function render(){var r=cur();$('count').textContent='显示 '+r.length+' / '+P.length+' 篇';
 $('list').innerHTML=r.map(function(p){
  return '<li><a class="t" lang="en" href="papers/'+p.id+'/index.html">'+esc(p.title)+'</a>'+(p.title_zh?'<div>'+esc(p.title_zh)+'</div>':'')+
  '<div class="s">'+esc(p.first_author)+' · <em>'+esc(p.journal)+'</em> · '+esc(p.date)+' · '+esc(p.species.join('/'))+' · '+esc(p.specialty.join('/'))+' · '+esc(p.doc_type)+
  ' <span class="pill ev">CEBM '+esc(p.cebm_display)+'</span> <span class="pill ev">偏倚 '+esc(p.rob_overall)+'</span> <span class="pill'+(p.verified_label==='全文已核'?' ok':'')+'">'+esc(p.verified_label)+'</span>'+(p.oa_bool===true?' <span class="pill">OA</span>':'')+
  (p.has_detail?' <span class="pill ok">深度速读</span>':'')+(p.status==='待处理'?' <span class="pill pend">待处理</span>':'')+'</div>'+
  (p.one_line_conclusion_zh?'<div class="s">'+esc(p.one_line_conclusion_zh)+'</div>':'')+'</li>'}).join('')}
function dl(name,text){var a=document.createElement('a');a.href=URL.createObjectURL(new Blob([text],{type:'text/plain;charset=utf-8'}));a.download=name;document.body.appendChild(a);a.click();a.remove()}
['q','sp','spec','dt','gr','oa'].forEach(function(i){$(i).addEventListener('input',render)});
document.querySelectorAll('.tabs button').forEach(function(b){b.addEventListener('click',function(){sort=b.dataset.sort;document.querySelectorAll('.tabs button').forEach(function(x){x.setAttribute('aria-selected',x===b)});render()})});
$('exb').addEventListener('click',function(e){e.preventDefault();dl('vetlit-selection.bib',cur().map(function(p){return C[p.id][0]}).join('\n'))});
$('exr').addEventListener('click',function(e){e.preventDefault();dl('vetlit-selection.ris',cur().map(function(p){return C[p.id][1]}).join('\n'))});
render()})();
