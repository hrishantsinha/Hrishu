const _show=show;
const api=p=>fetch(p,{headers:{'X-Init-Data':tg.initData}}).then(r=>r.ok?r.json():r.json().then(j=>{throw j.detail||'Error'}));
const fail=e=>{$('app').innerHTML='<div class="card soon"><i>⚠️</i><div class="sub">'+esc(e)+'</div></div>'};
const load=i=>{$('app').innerHTML='<div class="card soon"><i>'+i+'</i><div class="sub">Loading...</div></div>'};
const gb=(v,m,c)=>'<div class="bar"><div class="fill '+c+'" data-w="'+Math.min(100,100*v/Math.max(m,1))+'"></div></div>';
const grow=()=>setTimeout(()=>document.querySelectorAll('.fill[data-w]').forEach(f=>f.style.width=f.dataset.w+'%'),80);
show=function(t){
 if(t!=='rank'&&t!=='battle')return _show(t);
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 if(t==='rank'){load('🏆');api('/api/rank').then(j=>{
  const med=['🥇','🥈','🥉'];
  $('app').innerHTML=`<div class="card hero"><div class="sub">YOUR RANK</div><div class="big">#${j.pos||'-'}</div></div>`+j.top.map((p,i)=>`<div class="card row ${p.me?'me':''} ${i==0?'r1':''}" style="animation-delay:${i*.06}s"><span class="rk">${med[i]||i+1}</span><span class="nm">${esc(p.first_name||p.username||'Unknown')}<small>Level ${p.level}</small></span><b>${p.xp.toLocaleString()} XP</b></div>`).join('');
 }).catch(fail);return}
 load('⚔️');api('/api/arena').then(a=>{
  const kd=a.deaths?(a.kills/a.deaths).toFixed(2):a.kills;
  const pw=[['❤️','Health',a.power_hp_level],['⚔️','Attack',a.power_attack_level],['🗡️','Sword',a.power_sword_level],['🧱','Durability',a.power_durability_level],['🛡️','Shield',a.power_shield_level]];
  const sw=a.sword_durability>0,sh=a.shield_durability>0;
  $('app').innerHTML=`<div class="card hero"><div class="big">ARENA</div><div class="sub">K/D ${kd} · ${a.kills} kills · ${a.deaths} deaths</div></div>
  <div class="card"><div style="display:flex;justify-content:space-between"><b>❤️ Health</b><span>${a.hp}/${a.max_hp}</span></div>${gb(a.hp,a.max_hp,'')}</div>
  <div class="grid"><div class="card tile"><i>🗡️</i><b>${sw?a.sword_durability+' hits':'None'}</b><span>${sw?(a.sword_upgrade?'Upgraded +30%':'+40% damage'):'Buy in Shop'}</span>${gb(a.sword_durability,12,'gold')}</div>
  <div class="card tile"><i>🛡️</i><b>${sh?a.shield_durability+' hits':'None'}</b><span>${sh?'-50% damage taken':'Buy in Shop'}</span>${gb(a.shield_durability,4,'blue')}</div></div>
  <div class="card"><b>⚡ Power Levels</b>${pw.map(p=>`<div class="pw"><span>${p[0]} ${p[1]}</span><b>Lv ${p[2]}</b></div>`).join('')}</div>
  <div class="card soon" style="padding:22px"><div class="sub">To duel, use /fight @username in the bot chat.<br>Live in-app duels are coming soon.</div></div>`;
  grow();
 }).catch(fail);
};
const _show2=show;
const post=(p,b)=>fetch(p,{method:'POST',headers:{'X-Init-Data':tg.initData,'Content-Type':'application/json'},body:JSON.stringify(b)}).then(r=>r.ok?r.json():r.json().then(j=>{throw j.detail||'Error'}));
const toast=m=>{const d=document.createElement('div');d.className='toast';d.textContent=m;document.body.appendChild(d);setTimeout(()=>d.remove(),2200)};
const pop=(t,x,y)=>{const d=document.createElement('div');d.className='pop';d.textContent=t;d.style.left=x+'px';d.style.top=y+'px';document.body.appendChild(d);setTimeout(()=>d.remove(),1000)};
const buzz=k=>{try{tg.HapticFeedback.notificationOccurred(k)}catch(e){}};
function shopView(s){
 const it=[['sword','🗡️','Sword','+40% damage · 12 hits'],['shield','🛡️','Shield','-50% damage taken · 4 hits'],['potion','🧪','Potion','Restores full HP']];
 $('app').innerHTML='<div class="card hero"><div class="sub">YOUR COINS</div><div class="big" id="cn">0</div></div>'+it.map((x,i)=>{
  const d=s[x[0]],own=d.owned,can=s.coins>=d.price&&!own;
  return '<div class="card row" style="animation-delay:'+(i*.1)+'s"><span class="rk" style="font-size:38px;width:52px">'+x[1]+'</span><span class="nm">'+x[2]+'<small>'+x[3]+'</small>'+(x[0]==='potion'?'<small>You own '+d.count+'</small>':'')+'</span><button class="buy '+(can?'':'off')+'" data-i="'+x[0]+'" data-p="'+d.price+'" data-o="'+(own?1:0)+'">'+(own?'Equipped':'🪙 '+d.price.toLocaleString())+'</button></div>';
 }).join('');
 count($('cn'),s.coins);
}
show=function(t){
 if(t!=='shop')return _show2(t);
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 load('🛒');api('/api/shop').then(shopView).catch(fail);
};
$('app').addEventListener('click',e=>{
 const b=e.target.closest('.buy');if(!b)return;
 if(b.dataset.o==='1'){toast('Already equipped');buzz('warning');return}
 if(b.classList.contains('off')){toast('Not enough coins');buzz('error');return}
 b.disabled=true;const r=b.getBoundingClientRect(),p=b.dataset.p;
 post('/api/buy',{item:b.dataset.i}).then(s=>{buzz('success');pop('-'+Number(p).toLocaleString()+' 🪙',r.left,r.top);shopView(s)}).catch(er=>{b.disabled=false;buzz('error');toast(String(er))});
});
const _show3=show;
let ARN=null,PWS=null;
const PWL=[['hp','❤️','Health'],['attack','⚡','Attack Power'],['shield','🛡️','Shield Protection'],['defense','🧱','Defense']];
function battleView(a,p){
 const kd=a.deaths?(a.kills/a.deaths).toFixed(2):a.kills;
 const sw=a.sword_durability>0,sh=a.shield_durability>0;
 const cards=PWL.map((x,i)=>{
  const d=p[x[0]],mx=d.level>=7,can=!mx&&p.coins>=d.coins&&p.xp>=d.xp;
  const segs=Array.from({length:10},(_,k)=>'<span class="'+(mx||k<d.upgrades?'on':'')+'"></span>').join('');
  return '<div class="card" style="animation-delay:'+(i*.08)+'s"><div style="display:flex;justify-content:space-between"><b>'+x[1]+' '+x[2]+'</b><span>'+(mx?'🏆 MAX':'Lv '+d.level+'/7')+' · x'+d.mult.toFixed(2)+'</span></div><div class="seg">'+segs+'</div><div style="display:flex;justify-content:space-between;align-items:center;margin-top:12px"><small style="opacity:.7">'+(mx?'Fully upgraded':'🪙 '+d.coins.toLocaleString()+' · ⭐ '+d.xp.toLocaleString()+' XP')+'</small><button class="pup '+(can?'':'off')+'" data-k="'+x[0]+'">'+(mx?'MAX':'⚡ Power Up')+'</button></div></div>';
 }).join('');
 $('app').innerHTML='<div class="card hero"><div class="big">ARENA</div><div class="sub">K/D '+kd+' · '+a.kills+' kills · '+a.deaths+' deaths</div><div class="sub" style="margin-top:6px">🪙 '+p.coins.toLocaleString()+' · ⭐ '+p.xp.toLocaleString()+' XP</div></div>'
 +'<div class="card"><div style="display:flex;justify-content:space-between"><b>❤️ Health</b><span>'+p.hp+'/'+p.max_hp+'</span></div>'+gb(p.hp,p.max_hp,'')+'</div>'
 +'<div class="grid"><div class="card tile"><i>🗡️</i><b>'+(sw?a.sword_durability+' hits':'None')+'</b><span>'+(sw?(a.sword_upgrade?'Upgraded +30%':'+40% damage'):'Buy in Shop')+'</span>'+gb(a.sword_durability,12,'gold')+'</div>'
 +'<div class="card tile"><i>🛡️</i><b>'+(sh?a.shield_durability+' hits':'None')+'</b><span>'+(sh?'-50% damage taken':'Buy in Shop')+'</span>'+gb(a.shield_durability,4,'blue')+'</div></div>'
 +'<div class="card hero"><b>⚡ POWER UP</b></div>'+cards
 +'<div class="card soon" style="padding:22px"><div class="sub">To duel, use /fight @username in the bot chat.<br>Live in-app duels are coming soon.</div></div>';
 grow();
}
show=function(t){
 if(t!=='battle')return _show3(t);
 document.querySelectorAll('.nav button').forEach(b=>b.classList.toggle('on',b.dataset.t===t));
 load('⚔️');Promise.all([api('/api/arena'),api('/api/power')]).then(r=>{ARN=r[0];PWS=r[1];battleView(ARN,PWS)}).catch(fail);
};
$('app').addEventListener('click',e=>{
 const b=e.target.closest('.pup');if(!b||!PWS)return;
 const k=b.dataset.k,d=PWS[k];
 if(d.level>=7){toast('Already MAX level');buzz('warning');return}
 if(PWS.coins<d.coins){toast('You need '+d.coins.toLocaleString()+' coins');buzz('error');return}
 if(PWS.xp<d.xp){toast('You need '+d.xp.toLocaleString()+' XP');buzz('error');return}
 b.disabled=true;const r=b.getBoundingClientRect();
 post('/api/power',{type:k}).then(s=>{buzz('success');pop('⚡ Power Up!',r.left,r.top);if(s.leveled)toast('🎉 LEVEL UP!');PWS=s;battleView(ARN,PWS)}).catch(er=>{b.disabled=false;buzz('error');toast(String(er))});
});
const _shopView=shopView;
let PF=null,SY=null;
function pfpHTML(){
 if(!PF)return '<div class="sub" style="text-align:center;padding:24px">Loading PFPs...</div>';
 if(!PF.items.length)return '<div class="sub" style="text-align:center;padding:24px">No PFPs available yet.</div>';
 return '<div class="grid">'+PF.items.map((x,i)=>{
  const eq=PF.equipped===x.id;
  const btn=eq?'<button class="pfb off">✓ Equipped</button>':x.owned?'<button class="pfb" data-id="'+x.id+'" data-act="equip">Equip</button>':'<button class="pfb '+(PF.coins>=x.price?'':'off')+'" data-id="'+x.id+'" data-act="buy">🪙 '+x.price.toLocaleString()+'</button>';
  const m=x.media==='photo'?'<img class="pfi" loading="lazy" src="/api/pfpimg/'+x.id+'">':'<video class="pfi" src="/api/pfpimg/'+x.id+'" autoplay muted loop playsinline></video>';
  return '<div class="card pfc" style="animation-delay:'+(i%6*.06)+'s">'+m+'<b>'+esc(x.title)+'</b>'+btn+'</div>';
 }).join('')+'</div>';
}
const pfpBox=()=>'<div class="dv"><span>🖼️ PFP SHOP</span></div>'+pfpHTML();
shopView=function(s){
 _shopView(s);
 const d=document.createElement('div');d.id='pfx';d.innerHTML=pfpBox();$('app').appendChild(d);
 if(SY!=null){scrollTo(0,SY);SY=null}
 api('/api/pfps').then(j=>{const same=PF&&JSON.stringify(j)===JSON.stringify(PF);PF=j;const x=$('pfx');if(x&&!same)x.innerHTML=pfpBox()}).catch(()=>{});
};
$('app').addEventListener('click',e=>{
 const b=e.target.closest('.pfb');if(!b||!b.dataset.id||!PF)return;
 if(b.classList.contains('off')){toast('Not enough coins');buzz('error');return}
 b.disabled=true;const r=b.getBoundingClientRect(),id=b.dataset.id,act=b.dataset.act;
 post('/api/pfp',{id:id,act:act}).then(()=>{
  buzz('success');const it=PF.items.find(z=>z.id===id);
  if(act==='buy'){it.owned=true;PF.coins-=it.price;pop('-'+it.price.toLocaleString()+' 🪙',r.left,r.top)}else{PF.equipped=id;toast('✅ PFP equipped!')}
  SY=scrollY;api('/api/shop').then(shopView);
 }).catch(er=>{b.disabled=false;buzz('error');toast(String(er))});
});
