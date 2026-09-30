'use strict';
const $ = id => document.getElementById(id);
const canvas = $('world'), ctx = canvas.getContext('2d');
const terrain = document.createElement('canvas'), tc = terrain.getContext('2d');
let state = null, tool = 'inspect', zoom = 1, ox = 0, oy = 0, fitted = false;
let token = '', selected = null, dragging = null, layer = 'natural';
const powers = [['inspect','⌕','Inspect'],['raise','↟','Raise land'],['lower','≈','Lower land'],['rain','☂','Rain'],['forest','♠','Plant forest'],['fire','♨','Wildfire'],['human','♙','Humans'],['grazer','♧','Grazers'],['predator','♜','Predators']];
for (const [id, icon, label] of powers) {
  const b = document.createElement('button');
  b.innerHTML = `<b>${icon}</b>${label}`; b.dataset.tool = id;
  b.classList.toggle('active', id === tool);
  b.onclick = () => {tool = id; document.querySelectorAll('[data-tool]').forEach(x => x.classList.toggle('active', x.dataset.tool === tool));};
  $('tools').append(b);
}
function notice(text) { $('notice').textContent = text; $('notice').style.display = 'block'; clearTimeout(notice.timer); notice.timer = setTimeout(() => $('notice').style.display = 'none', 4000); }
async function command(data) {
  try {
    const response = await fetch('/api/command', {method:'POST',headers:{'Content-Type':'application/json','Authorization':`Bearer ${token}`},body:JSON.stringify(data)});
    const result = await response.json(); if (!response.ok) throw new Error(result.error);
    if (data.action === 'save') notice('World and neural policies saved');
  } catch(error) {notice(error.message);}
}
$('pause').onclick = () => state && command({action:'pause',value:!state.runtime.paused});
$('speed').onchange = e => command({action:'speed',value:Number(e.target.value)});
$('save').onclick = () => command({action:'save'});
$('connect').onclick = () => {token = $('token').value; notice('Connecting…');};
$('layer').onchange = e => {layer = e.target.value; if(state) drawTerrain();};
$('fit').onclick = fit;
function fit(){if(!state)return; zoom = Math.min(canvas.width/state.width,canvas.height/state.height)*.92;ox=(canvas.width-state.width*zoom)/2;oy=(canvas.height-state.height*zoom)/2;fitted=true;}
function resize(){const rect=canvas.getBoundingClientRect();canvas.width=Math.round(rect.width*devicePixelRatio);canvas.height=Math.round(rect.height*devicePixelRatio);if(state)fit();}
new ResizeObserver(resize).observe(canvas);
function hash(x,y){return ((Math.imul(x+17,374761393)^Math.imul(y+37,668265263))>>>0)%100/100;}
function drawTerrain(){
  const scale=6; terrain.width=state.width*scale;terrain.height=state.height*scale;
  for(let y=0;y<state.height;y++)for(let x=0;x<state.width;x++){
    const [e,m,g,t,ore,fire,f]=state.tiles[y*state.width+x],n=hash(x,y);let color;
    if(layer==='moisture')color=`hsl(${35+m*170} 45% ${23+m*25}%)`;
    else if(layer==='food')color=`hsl(${30+g*90} 48% ${17+g*35}%)`;
    else if(layer==='ore')color=`hsl(32 ${Math.min(90,ore*45)}% ${15+Math.min(40,ore*20)}%)`;
    else if(layer==='fertility')color=`hsl(${25+f*75} 40% ${18+f*32}%)`;
    else if(e<.30)color=`hsl(199 48% ${18+n*3}%)`;
    else if(e<=.37)color=`hsl(190 44% ${27+n*4}%)`;
    else if(e<.395)color=`hsl(46 42% ${57+n*8}%)`;
    else if(e>.77)color=`hsl(65 12% ${65+n*12}%)`;
    else if(e>.67)color=`hsl(75 12% ${39+n*10}%)`;
    else color=`hsl(${72+m*40} ${26+m*13}% ${27+g*13+n*5}%)`;
    tc.fillStyle=color;tc.fillRect(x*scale,y*scale,scale,scale);
    if(layer==='natural'&&e>.395&&e<.75&&t>.28&&n<t){
      tc.fillStyle='#193d2c';tc.fillRect(x*scale+2,y*scale+2,3,4);
      tc.fillStyle=t>.65?'#285740':'#3b6544';tc.fillRect(x*scale+1,y*scale,4,4);
      tc.fillStyle='#608151';tc.fillRect(x*scale+1,y*scale,2,1);
    }
    if(fire>0){tc.fillStyle='#e87d39';tc.fillRect(x*scale+1,y*scale+1,4,4);tc.fillStyle='#f0d576';tc.fillRect(x*scale+2,y*scale+2,2,2);}
  }
}
function render(){
  ctx.fillStyle='#102830';ctx.fillRect(0,0,canvas.width,canvas.height);
  if(state){ctx.imageSmoothingEnabled=false;ctx.drawImage(terrain,ox,oy,state.width*zoom,state.height*zoom);
    for(const s of state.settlements){const x=ox+s.x*zoom,y=oy+s.y*zoom;ctx.fillStyle='#3c2f28';ctx.fillRect(x-zoom/2,y,zoom*2,zoom);ctx.fillStyle='#c29565';ctx.fillRect(x-zoom/2,y-zoom/2,zoom*2,zoom*.7);}
    for(const o of state.organisms){const x=ox+(o.x+.5)*zoom,y=oy+(o.y+.5)*zoom,r=Math.max(2,zoom*.29);ctx.fillStyle='#112519';ctx.fillRect(x-r,y-r+1,r*2,r*2);ctx.fillStyle=o.kind==='human'?'#f5d595':o.kind==='predator'?'#e59277':'#e0e6c3';ctx.fillRect(x-r,y-r,r*1.6,r*1.6);if(o.kind==='human'){ctx.fillStyle='#8a6551';ctx.fillRect(x-r,y,r*1.6,r);}}
    if(selected){ctx.strokeStyle='#ffffff';ctx.lineWidth=2;ctx.strokeRect(ox+selected.x*zoom-2,oy+selected.y*zoom-2,zoom+4,zoom+4);}
  }requestAnimationFrame(render);
}
function point(e){const r=canvas.getBoundingClientRect();return [(e.clientX-r.left)*devicePixelRatio,(e.clientY-r.top)*devicePixelRatio];}
canvas.onpointerdown=e=>{const [x,y]=point(e);dragging={x,y,ox,oy,moved:false};canvas.setPointerCapture(e.pointerId);};
canvas.onpointermove=e=>{if(!dragging)return;const [x,y]=point(e);if(Math.hypot(x-dragging.x,y-dragging.y)>5)dragging.moved=true;if(dragging.moved){ox=dragging.ox+x-dragging.x;oy=dragging.oy+y-dragging.y;}};
canvas.onpointerup=e=>{if(!dragging)return;const click=!dragging.moved;dragging=null;if(!click||!state)return;const [px,py]=point(e),x=Math.floor((px-ox)/zoom),y=Math.floor((py-oy)/zoom);if(x<0||y<0||x>=state.width||y>=state.height)return;if(tool==='inspect'){selected={x,y};inspect();}else command({action:'tool',tool,x,y});};
canvas.onpointercancel=()=>dragging=null;
canvas.addEventListener('wheel',e=>{e.preventDefault();const [x,y]=point(e),old=zoom;zoom=Math.max(2,Math.min(100,zoom*Math.exp(-e.deltaY*.001)));ox=x-(x-ox)*zoom/old;oy=y-(y-oy)*zoom/old;},{passive:false});
function inspect(){if(!selected||!state)return;const {x,y}=selected;const o=state.organisms.find(a=>a.x===x&&a.y===y);const t=state.tiles[y*state.width+x];$('inspector').innerHTML=o?`<strong>${o.kind.toUpperCase()} #${o.id}</strong><br>Energy ${o.energy.toFixed(1)} · Age ${o.age}<br>Generation ${o.generation} · Size ${o.size.toFixed(2)}<br>Neural updates ${o.updates}<br>Culture ${o.culture||'—'} · Wood ${o.wood.toFixed(1)}`:`<strong>LAND AT ${x}, ${y}</strong><br>Elevation ${t[0].toFixed(2)}<br>Moisture ${Math.round(t[1]*100)}% · Food ${Math.round(t[2]*100)}%<br>Trees ${Math.round(t[3]*100)}%<br>Minerals ${t[4].toFixed(2)} · Soil ${Math.round(t[6]*100)}%`;}
async function poll(){
  try{const r=await fetch('/api/state',{headers:{Authorization:`Bearer ${token}`}});if(!r.ok)throw new Error(r.status===401?'Access token required':'Server unavailable');state=await r.json();$('connection').textContent=state.runtime.error?'Simulation stopped':'● Connected';$('clock').textContent=`Age ${state.tick}`;$('seed').textContent=`SEED ${state.seed}`;$('population').textContent=state.stats.population.toLocaleString();$('pause').textContent=state.runtime.paused?'Resume':'Pause';$('speed').value=state.runtime.speed;
  const stats=[['Humans',state.stats.counts.human||0],['Settlements',state.settlements.length],['Births',state.stats.births],['Generation',state.stats.generation],['Cultures',state.stats.cultures],['Learning steps',state.stats.training.toLocaleString()]];
  $('stats').innerHTML=stats.map(([k,v])=>`<div class="stat"><strong>${v}</strong><span>${k}</span></div>`).join('');
  $('events').replaceChildren(...state.events.slice(0,6).map(e=>{const p=document.createElement('p'),s=document.createElement('small');s.textContent=`AGE ${e.tick}`;p.append(s,document.createTextNode(e.text));return p;}));
  $('runtime').textContent=`${state.runtime.tick_ms} ms / tick · ${state.runtime.workers} CPU workers · ${state.runtime.device.toUpperCase()}`;drawTerrain();if(!fitted)fit();inspect();
  }catch(e){$('connection').textContent=e.message;}finally{setTimeout(poll,500);}
}resize();render();poll();
