// Procedural pixel atlas. Shared by world view and exact server-generated preview.
export const biomeNames=['Temperate','Rainforest','Desert','Savanna','Taiga','Tundra','Wetlands','Volcanic','Grassland','Woodland','Burn scar'];
const palettes=[[99,39,44],[143,43,30],[39,59,66],[65,49,49],[155,27,36],[187,20,77],[163,33,34],[19,13,37],[78,45,43],[113,40,31],[26,30,24]];
function noise(x,y,seed){return ((Math.imul(x+17,374761393)^Math.imul(y+37,668265263)^(seed>>>0))>>>0)%101/100;}
export function paintMap(target,world,layer='natural'){
 const c=target.getContext('2d'),s=8;target.width=world.width*s;target.height=world.height*s;
 for(let y=0;y<world.height;y++)for(let x=0;x<world.width;x++){
  const [e,m,g,t,ore,fire,f,temp=.57,biome=0,water=0,lava=0,grassPop=0,treePop=0,road=0,nutrient=0,litter=0,river=0,scar=0]=world.tiles[y*world.width+x];
  const cloud=world.weather?.clouds[Math.floor(y/8)*world.weather.width+Math.floor(x/8)]||0;
  const n=noise(x,y,world.seed),X=x*s,Y=y*s;let color;
  const east=world.tiles[y*world.width+(x+1)%world.width][0],south=world.tiles[((y+1)%world.height)*world.width+x][0];
  const shade=Math.max(-9,Math.min(9,(e-east+e-south)*55));
  if(layer==='moisture')color=`hsl(${35+m*165} 52% ${23+m*30}%)`;
  else if(layer==='food')color=`hsl(${30+g*100} 53% ${18+g*37}%)`;
  else if(layer==='ore')color=`hsl(32 ${Math.min(90,ore*45)}% ${16+Math.min(45,ore*20)}%)`;
  else if(layer==='fertility')color=`hsl(${25+f*90} 42% ${20+f*36}%)`;
  else if(layer==='nutrient')color=`hsl(${23+nutrient*100} ${35+nutrient*35}% ${18+nutrient*43}%)`;
  else if(layer==='weather')color=`hsl(${213-cloud*23} ${34+cloud*30}% ${16+cloud*66}%)`;
  else if(layer==='rivers')color=e<=.37?'#245b78':river>.01?`hsl(195 76% ${26+river*43}%)`:'#554c40';
  else if(layer==='temperature')color=`hsl(${210-temp*200} 65% 52%)`;
  else if(e<=.37){const shallow=Math.max(0,Math.min(1,(e-.18)/.19));color=temp<.12?`hsl(190 33% ${64+shallow*15}%)`:`hsl(${211-shallow*27} ${54+shallow*9}% ${20+shallow*25+n*2}%)`;}
  else if(e<.4)color=`hsl(43 49% ${70+n*5}%)`;
  else if(e>.79)color=`hsl(192 14% ${76+n*9+shade}%)`;
  else if(e>.69)color=`hsl(195 12% ${43+n*7+shade}%)`;
  else{const [h,sat,l]=palettes[biome]||palettes[0];color=`hsl(${h} ${sat}% ${l+n*4+shade+g*3}%)`;}
  c.fillStyle=color;c.fillRect(X,Y,s,s);
  if(layer==='natural'){
   if(e<=.37){if(n>.87){c.fillStyle='#c8eeec35';c.fillRect(X+1,Y+4,4,1);}if(east>.37||south>.37){c.fillStyle='#d5f3de80';c.fillRect(X+6,Y+5,2,2);}}
   else if(e>.69){c.fillStyle='#26333b45';c.fillRect(X+2,Y+3,4,4);c.fillStyle=e>.79?'#f1f2df':'#aab9b0';c.fillRect(X+2,Y+1,3,2);}
   else if(t>.12&&n<t){
    c.fillStyle='#142c3055';c.fillRect(X+3,Y+4,5,3);c.fillStyle='#6c523e';c.fillRect(X+3,Y+4,2,3);
    if(biome===4||biome===5){c.fillStyle=biome===5?'#a8c7bd':'#204b48';c.fillRect(X+2,Y+1,3,5);c.fillRect(X+1,Y+3,5,2);c.fillStyle='#6a9b80';c.fillRect(X+2,Y+1,2,2);}
    else{c.fillStyle=biome===1?'#174f42':'#2d633f';c.fillRect(X+1,Y+1,5,4);c.fillRect(X+2,Y,3,6);c.fillStyle=biome===1?'#389c61':'#75a653';c.fillRect(X+1,Y+1,3,2);}
   }else if(g>.3&&n>.65){c.fillStyle='#d0d67b65';c.fillRect(X+2,Y+3,1,2);c.fillRect(X+5,Y+5,1,1);}
   else if(biome===2&&n>.65){c.fillStyle='#af855644';c.fillRect(X+1,Y+4,5,1);}
  }
  if(layer==='natural'&&water>.008&&e>.37){c.fillStyle=`hsla(188,73%,57%,${Math.min(.68,water*2.7)})`;c.fillRect(X,Y+3,s,4);if(n>.55){c.fillStyle='#d8f5e8aa';c.fillRect(X+1,Y+4,3,1);}}
  if(layer==='natural'&&river>.03&&e>.37){c.fillStyle=`hsla(195,78%,58%,${Math.min(.85,.2+river*.65)})`;c.fillRect(X,Y+2,s,Math.max(1,Math.round(river*3)));}
  if(layer==='natural'&&scar>.15&&e>.37){c.fillStyle=`hsla(25,22%,17%,${Math.min(.42,scar*.38)})`;c.fillRect(X,Y,s,s);if(n>.45){c.fillStyle='#d7b88b66';c.fillRect(X+2,Y+5,3,1);}}
  if(layer==='natural'&&cloud>.72){c.fillStyle=`hsla(192,40%,91%,${Math.min(.24,(cloud-.72)*.7)})`;c.fillRect(X,Y,s,s);}
  if(layer==='natural'&&road>.04&&e>.37){c.fillStyle=`hsla(36,37%,70%,${Math.min(.75,road)})`;c.fillRect(X,Y+3,s,2);}
  if(layer==='natural'&&lava>.01){c.fillStyle=`hsla(13,92%,42%,${Math.min(.95,.4+lava)})`;c.fillRect(X,Y,s,s);c.fillStyle='#ffc059';c.fillRect(X+2,Y+2,4,2);c.fillRect(X+5,Y+5,2,2);}
  if(fire>0){c.fillStyle='#b4413260';c.fillRect(X,Y,s,s);c.fillStyle='#ed6d36';c.fillRect(X+2,Y+2,4,5);c.fillStyle='#ffe6a1';c.fillRect(X+3,Y+3,2,3);}
 }
}
