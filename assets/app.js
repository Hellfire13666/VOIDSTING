'use strict';
let activeFilter='ALL';
let activeSession=null;
let sessionRows=[];
const $=id=>document.getElementById(id);
const txt=(node,val)=>{if(node)node.textContent=val===undefined||val===null?'':String(val);};
const el=(tag,cls='',val='')=>{const x=document.createElement(tag);if(cls)x.className=cls;if(val!==''&&val!==undefined)txt(x,val);return x;};
const SVG='http://www.w3.org/2000/svg';
const se=(tag,attrs={})=>{const e=document.createElementNS(SVG,tag);Object.entries(attrs).forEach(([k,v])=>e.setAttribute(k,String(v)));return e;};
const palette={EXACT:'#86f8bd',RELATED:'#5be6f4',UNCERTAIN:'#bca0ff',OTHER:'#f48eaa'};
function safeProfile(url){try{const u=new URL(url);return u.protocol==='https:'&&!u.username&&!u.password;}catch{return false;}}
function group(s){return ['EXACT','RELATED','UNCERTAIN'].includes(s.state)?s.state:'OTHER';}
function allRows(){return activeSession?.signals||[];}
function visibleRows(){const find=$('evidenceFind').value.trim().toLowerCase();return allRows().filter(s=> (activeFilter==='ALL'||group(s)===activeFilter)&&(!find||[s.provider,s.category,s.state,s.reason,s.username,s.profile_url].some(v=>String(v||'').toLowerCase().includes(find))));}
function updateFilter(next){activeFilter=next;document.querySelectorAll('[data-filter]').forEach(b=>{const yes=b.dataset.filter===next;b.classList.toggle('selected',yes);b.setAttribute('aria-pressed',String(yes));});txt($('vpFocus'),next==='ALL'?'ALL RECORDED SIGNALS':`${next} LENS ACTIVE · VIEW EVIDENCE BELOW`);renderResults();}
function rowView(r){
 const card=el('article','result '+group(r).toLowerCase());
 const top=el('div','result-top');top.append(el('span','result-provider',r.provider));top.append(el('span','pill '+group(r).toLowerCase(),r.state));card.append(top);
 card.append(el('p','result-reason',r.reason));
 if(['EXACT','RELATED'].includes(r.state)&&safeProfile(r.profile_url)){
    const a=el('a','result-link',r.profile_url);a.href=r.profile_url;a.rel='noreferrer noopener';a.target='_blank';card.append(a);
 }
 card.append(el('div','result-meta',`${r.category} · ${r.evidence_type} · ${r.latency_ms} ms${r.http_status?' · HTTP '+r.http_status:''}`));
 return card;
}
function renderResults(){
 const root=$('resultList');root.replaceChildren();
 if(!activeSession){txt($('resultCount'),'Open a saved session to view evidence.');root.append(el('p','empty','Select a saved session to inspect public evidence.'));return;}
 const rows=visibleRows();
 txt($('resultCount'),`${rows.length} of ${allRows().length} saved signals displayed · ${activeFilter} lens${$('evidenceFind').value.trim()?' · text filter active':''}`);
 if(!rows.length){root.append(el('p','empty','No matching saved evidence in this view.'));return;}
 for(const item of rows)root.append(rowView(item));
}
function renderControlCore(){
 const s=activeSession;
 const counts=s?.counts||{};
 txt($('coreHandle'),s?.username||'No session selected');
 txt($('coreMode'),s?.scan_mode||'Choose a saved trace');
 txt($('coreExact'),counts.EXACT||0);
 txt($('coreRelated'),counts.RELATED||0);
 txt($('coreUnresolved'),(counts.UNCERTAIN||0)+(counts.BLOCKED||0)+(counts.ERROR||0));
 txt($('coreStatus'),s?'SAVED SIGNAL READY':'AWAITING VAULT');
 const latest=sessionRows[0];
 txt($('coreLatest'),latest?`#${latest.id} · ${latest.username}`:'No saved sessions');
}
function renderSessions(){
 const root=$('sessions');root.replaceChildren();
 for(const s of sessionRows){const b=el('button','session'+(activeSession?.id===s.id?' selected':''));b.type='button';b.setAttribute('aria-label',`Open session ${s.id}, ${s.username}`);
  b.append(el('b','',`#${s.id}  ${s.username}`),el('span','',s.scan_mode),el('small','',s.created_at));b.addEventListener('click',()=>loadSession(s.id));root.append(b);}
 if(!sessionRows.length)root.append(el('p','empty','No saved scans yet. Run a search in the terminal.'));
}
function renderMatrix(){
 const root=$('sourceMatrix');root.replaceChildren();const rows=allRows();
 if(!rows.length){txt($('sourceCount'),'0 SOURCES');root.append(el('p','empty','Select a saved session to view source health.'));return;}
 const grouped=new Map();
 for(const s of rows){let item=grouped.get(s.provider);if(!item){item={name:s.provider,signals:[],state:s.state};grouped.set(s.provider,item);}item.signals.push(s);const order={EXACT:4,RELATED:3,UNCERTAIN:2,BLOCKED:1,ERROR:1,NOT_FOUND:0};if(order[s.state]>order[item.state])item.state=s.state;}
 txt($('sourceCount'),`${grouped.size} PROVIDERS`);
 for(const item of grouped.values()){
  const stateGroup=group({state:item.state});const cell=el('div','source-chip '+stateGroup.toLowerCase());
  const head=el('div','chip-top');head.append(el('b','',item.name),el('em','',item.state));cell.append(head);
  const extra=item.signals.length>1?`${item.signals.length} recorded signals`:`${item.signals[0].latency_ms} ms`;
  cell.append(el('span','',extra));root.append(cell);
 }
}
function renderTimeline(){
 const root=$('timelineTrack');root.replaceChildren();
 const colors=['#ff86c0','#ffd27a','#9affac','#76edeb','#7b9cff','#d3a2ff'];
 for(const [index,s] of sessionRows.slice(0,12).entries()){
  const b=el('button','timeline-item'+(activeSession?.id===s.id?' selected':''));b.type='button';
  b.style.setProperty('--item-color',colors[index%colors.length]);
  b.setAttribute('aria-label',`Reopen saved session ${s.id} for ${s.username}`);
  b.append(el('span','timeline-bead'));
  const middle=el('span');middle.append(el('b','',`#${s.id} ${s.username}`),el('small','',`${s.scan_mode} · ${s.checked_count} stored results`));b.append(middle);
  b.append(el('span','time-side',String(s.created_at||'').replace('T',' ').slice(5,16)));
  b.addEventListener('click',()=>loadSession(s.id));root.append(b);
 }
 if(!sessionRows.length)root.append(el('p','empty','No saved sessions yet. Terminal scans create them.'));
}
function renderPulse(){
 const root=$('pulseStrip');root.replaceChildren();
 if(!activeSession){root.append(el('span','', 'Select a session for provider pulse.'));return;}
 const counts=activeSession.counts||{};
 for(const [label,count,groupName] of [
  ['EXACT',counts.EXACT||0,'exact'],['RELATED',counts.RELATED||0,'related'],
  ['UNCERTAIN',counts.UNCERTAIN||0,'uncertain'],
  ['BLOCKED',counts.BLOCKED||0,'other'],['NOT FOUND',counts.NOT_FOUND||0,'other'],
  ['ERROR',counts.ERROR||0,'other']])root.append(el('span','pulse-chip '+groupName,`${label} ${count}`));
}
async function renderReferences(id){
 const root=$('referenceList');root.replaceChildren();
 txt($('referenceLabel'),activeSession?.username||'SELECT A SESSION');
 txt($('referenceCount'),'Reference templates are NOT checked and NEVER count as findings.');
 try{
  const response=await fetch(`/api/references/${encodeURIComponent(id)}`,{cache:'no-store'});
  if(!response.ok)throw Error('Cannot read reference templates');
  const data=await response.json();
  // A user may have already opened another session while the request was in flight.
  if(!activeSession||activeSession.id!==id)return;
  for(const item of data.references||[]){
   if(item.state!=='NOT_CHECKED'||!safeProfile(item.url))continue;
   const link=el('a','reference-item');link.href=item.url;link.target='_blank';link.rel='noopener noreferrer';
   link.setAttribute('aria-label',`Open manual ${item.provider} reference for ${data.username}, not checked`);
   link.append(el('b','',item.provider),el('span','', 'NOT CHECKED · opens only on click'));root.append(link);
  }
  txt($('referenceCount'),`${root.children.length} manual templates · 0 verified by Reference Atlas`);
  if(!root.children.length)root.append(el('p','empty','No manual references available.'));
 }catch(error){if(activeSession?.id===id)root.append(el('p','empty',error.message));}
}
function renderVoidpulseControls(){
 const rows=allRows();const counts={EXACT:0,RELATED:0,UNCERTAIN:0,OTHER:0};
 for(const item of rows)counts[group(item)]++;
 txt($('vpHandle'),activeSession?.username||'AWAITING SESSION');
 txt($('vpMode'),activeSession?.scan_mode||'NO SESSION');
 txt($('vpSession'),activeSession?`SAVED TRACE #${activeSession.id}`:'Select a saved trace from the right');
 txt($('vpTimestamp'),activeSession?.created_at||'NOT SELECTED');
 const latest=sessionRows[0];txt($('vpLatest'),latest?`#${latest.id} · ${latest.username}`:'NO SESSIONS');
 for(const key of ['EXACT','RELATED','UNCERTAIN','OTHER'])txt($('vp'+key.charAt(0)+key.slice(1).toLowerCase()),counts[key]);
 txt($('vpAll'),rows.length);
 const total=rows.length;
 for(const [key,id] of [['EXACT','vpBarExact'],['RELATED','vpBarRelated'],['UNCERTAIN','vpBarUncertain'],['OTHER','vpBarOther']]){
  const node=$(id);if(node)node.style.width=(total?100*counts[key]/total:0)+'%';
 }
}
function renderConstellation(){
 renderVoidpulseControls();
 const root=$('signalMap');root.replaceChildren();
 const rows=allRows();txt($('mapHandle'),activeSession?.username||'NO SESSION');txt($('mapMode'),activeSession?.scan_mode||'AWAITING VAULT');txt($('mapTotal'),rows.length);
 txt($('mapLinks'),new Set(rows.filter(r=>['EXACT','RELATED'].includes(r.state)&&safeProfile(r.profile_url)).map(r=>r.profile_url.toLowerCase())).size);
 const defs=se('defs');const glow=se('filter',{id:'signalGlow',x:'-40%',y:'-40%',width:'180%',height:'180%'});glow.append(se('feGaussianBlur',{stdDeviation:'3',result:'blur'}));const merge=se('feMerge');merge.append(se('feMergeNode',{in:'blur'}),se('feMergeNode',{in:'SourceGraphic'}));glow.append(merge);defs.append(glow);root.append(defs);
 const center={x:320,y:166};
 for(const radius of [42,91,139])root.append(se('ellipse',{cx:center.x,cy:center.y,rx:radius*1.65,ry:radius,stroke:'#3d5581','stroke-opacity':'.52',fill:'none','stroke-dasharray':radius===79?'3 7':'1 0'}));
 for(let i=0;i<27;i++){const x=(i*127+39)%640,y=(i*73+39)%340;root.append(se('circle',{cx:x,cy:y,r:i%5?'.85':'1.3',fill:'#7895bb',opacity:'.33'}));}
 const core=se('g');core.append(se('circle',{cx:center.x,cy:center.y,r:31,fill:'#152a38',stroke:'#a77cf1','stroke-width':'1.8'}));const coreText=se('text',{x:center.x,y:center.y+6,'text-anchor':'middle',fill:'#9bffda','font-size':'19','font-weight':'bold'});txt(coreText,'VP');core.append(coreText);
 if(!rows.length){root.append(core);const notice=se('text',{x:320,y:328,'text-anchor':'middle',fill:'#8d9fbf','font-size':'11'});txt(notice,'SELECT A SESSION TO MAP PUBLIC SIGNALS');root.append(notice);return;}
 const visible=rows.slice(0,70);const total=visible.length;
 visible.forEach((s,i)=>{
   const theta=(i/total)*Math.PI*2-Math.PI/2;const ring=111+(i%3)*18;
   const x=center.x+Math.cos(theta)*ring*1.65;const y=center.y+Math.sin(theta)*ring;
   const state=group(s);const color=palette[state];
   root.append(se('line',{x1:center.x,y1:center.y,x2:x,y2:y,stroke:color,'stroke-opacity':state==='EXACT'?'.38':'.22','stroke-width':'1'}));
   const n=se('circle',{cx:x,cy:y,r:state==='EXACT'?5.4:state==='RELATED'?4.1:3.1,fill:color,stroke:'#07131f','stroke-width':'1.2',tabindex:'0',role:'button','aria-label':`${s.provider}, ${s.state}; filter ${state}`});
   const title=se('title');txt(title,`${s.provider}: ${s.state} (${s.username})`);n.append(title);
   const click=()=>{updateFilter(state);$('evidence').scrollIntoView({behavior:'smooth',block:'start'});};
   n.addEventListener('click',click);n.addEventListener('keydown',e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();click();}});
   root.append(n);
 });
 root.append(core);
 if(rows.length>70){const note=se('text',{x:320,y:329,'text-anchor':'middle',fill:'#9eb3ca','font-size':'10'});txt(note,`FIRST 70 OF ${rows.length} NODES SHOWN`);root.append(note);}
}
async function loadSession(id){
 try{const resp=await fetch(`/api/session/${encodeURIComponent(id)}`,{cache:'no-store'});if(!resp.ok)throw Error('Saved session unavailable');
  activeSession=await resp.json();txt($('currentUser'),activeSession.username);txt($('currentMode'),activeSession.scan_mode);
  const c=activeSession.counts||{};txt($('countExact'),c.EXACT||0);txt($('countRelated'),c.RELATED||0);txt($('countUnknown'),(c.UNCERTAIN||0)+(c.BLOCKED||0)+(c.ERROR||0));
  renderResults();renderSessions();renderMatrix();renderConstellation();renderTimeline();renderPulse();renderControlCore();
  void renderReferences(id);
 }catch(e){txt($('resultCount'),'Cannot open session: '+e.message);}
}
async function init(){
 txt($('topClock'),'READ ONLY');
 document.querySelectorAll('[data-filter]').forEach(b=>b.addEventListener('click',()=>updateFilter(b.dataset.filter)));
 $('evidenceFind').addEventListener('input',renderResults);updateFilter('ALL');renderConstellation();
 try{const resp=await fetch('/api/sessions',{cache:'no-store'});if(!resp.ok)throw Error('Vault unavailable');
  sessionRows=await resp.json();txt($('countSessions'),sessionRows.length);renderControlCore();renderSessions();renderTimeline();if(sessionRows.length)await loadSession(sessionRows[0].id);
 }catch(e){txt($('resultCount'),'Cannot load local vault: '+e.message);txt($('coreStatus'),'VAULT UNAVAILABLE');}
}
init();
