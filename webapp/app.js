const tg=window.Telegram.WebApp;tg.ready();tg.expand();
try{tg.setHeaderColor('#0b0820');tg.setBackgroundColor('#0b0820')}catch(e){}
const hap=()=>{try{tg.HapticFeedback.impactOccurred('light')}catch(e){}};
const $=id=>document.getElementById(id);
const esc=s=>String(s==null?'':s).replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
let D=null;
const tabs=[['home','🏠','Home'],['shop','🛒','Shop'],['poke','🐾','Pokémon'],['battle','⚔️','Battle'],['rank','🏆','Ranks']];
$('nav').innerHTML=tabs.map(t=>`<button data-t="${t[0]}"><i>${t[1]}</i>${t[2]}</button>`).join('');
$('nav').onclick=e=>{const b=e.target.closest('button');if(b){hap();show(b.dataset.t)}};
function count(el,to){const t0=performance.now();(function f(t){const p=Math.min((t-t0)/1200,1);el.textContent=Math.round(to*(1-Math.pow(1-p,3))).toLocaleString();if(p<1)requestAnimationFrame(f)})(t0)}
function show(t){
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 const a=$('app');
 if(t!=='home'){const x=tabs.find(z=>z[0]===t);a.innerHTML=`<div class="card soon"><i>${x[1]}</i><div class="name">${x[2]}</div><div class="sub">Coming soon</div></div>`;return}
 if(!D){a.innerHTML='<div class="card soon"><i>⏳</i><div class="sub">Loading...</div></div>';return}
 const need=D.level*100,p=Math.min((D.xp%need)/need,1),C=2*Math.PI*70;
 a.innerHTML=`<div class="card hero"><div class="ring"><svg width="160" height="160"><defs><linearGradient id="g"><stop offset="0" stop-color="#ffe07a"/><stop offset="1" stop-color="#ff5ca8"/></linearGradient></defs><circle cx="80" cy="80" r="70" stroke="#ffffff18" stroke-width="10" fill="none"/><circle id="arc" cx="80" cy="80" r="70" stroke="url(#g)" stroke-width="10" fill="none" stroke-linecap="round" stroke-dasharray="${C}" stroke-dashoffset="${C}" style="transition:stroke-dashoffset 1.6s cubic-bezier(.2,.9,.3,1)"/></svg><div class="in"><small>LEVEL</small><b>${D.level}</b></div></div>
 <div class="name">${esc(D.first_name)}</div><div class="sub">${D.username?'@'+esc(D.username)+' · ':''}${D.xp.toLocaleString()} XP</div></div>
 <div class="card"><div style="display:flex;justify-content:space-between"><b>❤️ Health</b><span>${D.hp}/${D.max_hp}</span></div><div class="bar"><div class="fill" id="hp"></div></div></div>
 <div class="grid">
 <div class="card tile"><i>🪙</i><b id="n1">0</b><span>Coins</span></div>
 <div class="card tile"><i>🏦</i><b id="n2">0</b><span>Bank</span></div>
 <div class="card tile"><i>💀</i><b id="n3">0</b><span>Kills</span></div>
 <div class="card tile"><i>☠️</i><b id="n4">0</b><span>Deaths</span></div></div>`;
 setTimeout(()=>{$('arc').style.strokeDashoffset=C*(1-p);$('hp').style.width=(100*D.hp/Math.max(D.max_hp,1))+'%'},80);
 count($('n1'),D.coins);count($('n2'),D.bank);count($('n3'),D.kills);count($('n4'),D.deaths);
}
show('home');
fetch('/api/me',{headers:{'X-Init-Data':tg.initData}}).then(r=>r.ok?r.json():r.json().then(j=>{throw j.detail||'Error'})).then(j=>{D=j;show('home')}).catch(e=>{$('app').innerHTML=`<div class="card soon"><i>⚠️</i><div class="sub">${esc(e)}</div></div>`});
const cv=$('c'),x=cv.getContext('2d');let P=[];
function rs(){cv.width=innerWidth;cv.height=innerHeight}rs();onresize=rs;
for(let i=0;i<55;i++)P.push({x:Math.random()*innerWidth,y:Math.random()*innerHeight,r:Math.random()*2+.5,v:Math.random()*.5+.2,h:Math.random()*60+260});
(function L(){x.clearRect(0,0,cv.width,cv.height);P.forEach(p=>{p.y-=p.v;if(p.y<-5){p.y=cv.height+5;p.x=Math.random()*cv.width}x.beginPath();x.arc(p.x,p.y,p.r,0,7);x.fillStyle=`hsla(${p.h},90%,75%,.6)`;x.shadowBlur=8;x.shadowColor=`hsl(${p.h},90%,70%)`;x.fill()});requestAnimationFrame(L)})();
