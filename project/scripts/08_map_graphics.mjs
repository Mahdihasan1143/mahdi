// Animated location-map card: renders transparent PNG sequences (600x660 @30fps) with Chromium.
// Variants: all (3 pins in order of mention), thanchi, lama (highlight). Positions: assets/map/places.json.
import {createRequire} from 'module';import fs from 'fs';import path from 'path';import {fileURLToPath} from 'url';
import {geoMercator,geoPath,geoGraticule} from 'd3-geo';import {feature} from 'topojson-client';
const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const W=600,H=660,FPS=30,ACC='#F2A33A';
const topo=JSON.parse(fs.readFileSync(root+'/assets/map/countries-10m.json'));
const all=feature(topo,topo.objects.countries).features;
const pick=n=>all.find(f=>f.properties.name===n);
const BD=pick('Bangladesh'),NB=[pick('India'),pick('Myanmar')];
if(!BD||NB.some(x=>!x))throw new Error('basemap countries missing');
const PL=JSON.parse(fs.readFileSync(root+'/assets/map/places.json'));const places=PL.places;
const pts={type:'MultiPoint',coordinates:places.map(p=>[p.lon,p.lat])};
const pA=geoMercator().fitExtent([[40,60],[560,560]],BD);
const pB=geoMercator().fitExtent([[120,200],[480,480]],pts);
const raw=geoMercator().scale(1).translate([0,0]);
const ctr=[(places[0].lon+places[1].lon+places[2].lon)/3,(places[0].lat+places[1].lat+places[2].lat)/3];
const mP=raw(ctr),sA=pA(ctr),sB=pB(ctr);
const E=t=>t<0?0:t>1?1:t<.5?4*t*t*t:1-Math.pow(-2*t+2,3)/2;
const L=(a,b,t)=>a+(b-a)*t, C=(t)=>Math.max(0,Math.min(1,t));
const back=t=>{t=C(t);const c1=1.70158,c3=c1+1;return 1+c3*Math.pow(t-1,3)+c1*Math.pow(t-1,2)};
function proj(e){const k=Math.exp(L(Math.log(pA.scale()),Math.log(pB.scale()),e));
  const s=[L(sA[0],sB[0],e),L(sA[1],sB[1],e)];
  return geoMercator().scale(k).translate([s[0]-k*mP[0],s[1]-k*mP[1]]).clipExtent([[-30,-30],[W+30,H+30]]);}
function frame(variant,t,dur){
  const zoomT=variant==='all'?[1.5,3.1]:[0,0];
  const e=variant==='all'?E((t-zoomT[0])/(zoomT[1]-zoomT[0])):1;
  const pr=proj(e),gp=geoPath(pr);
  const fadeIn=C(t/0.45),fadeOut=C((dur-t)/0.45),op=Math.min(E(fadeIn),E(fadeOut));
  const lift=(1-E(fadeIn))*16;
  let s=`<svg xmlns="http://www.w3.org/2000/svg" width="${W}" height="${H}" viewBox="0 0 ${W} ${H}"><defs>
   <clipPath id="c"><rect x="0" y="0" width="${W}" height="${H}" rx="30"/></clipPath>
   <filter id="sh" x="-30%" y="-30%" width="160%" height="160%"><feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#000" flood-opacity=".55"/></filter></defs>
   <g opacity="${op.toFixed(3)}" transform="translate(0 ${lift.toFixed(1)})"><g clip-path="url(#c)">
   <rect width="${W}" height="${H}" fill="#0b1420" fill-opacity=".80"/>`;
  const grat=geoGraticule().extent([[91.5,21.0],[93.0,22.5]]).step([0.1,0.1]);
  s+=`<path d="${gp(grat())}" fill="none" stroke="#8fb0d0" stroke-opacity="${(0.10*e).toFixed(3)}" stroke-width="1"/>`;
  for(const f of NB)s+=`<path d="${gp(f)}" fill="#18273a" fill-opacity=".85" stroke="#2c4058" stroke-width="1.2"/>`;
  const bdIn=variant==='all'?E(C((t-0.25)/1.0)):1;
  s+=`<path d="${gp(BD)}" fill="#22364d" fill-opacity="${(0.95*bdIn).toFixed(2)}" stroke="${ACC}" stroke-opacity="${(0.9*bdIn).toFixed(2)}" stroke-width="${L(2.4,1.6,e).toFixed(2)}"/>`;
  if(variant==='all'&&e<0.98){const c=pr(ctr),pulse=(t*1.3)%1;
    s+=`<circle cx="${c[0]}" cy="${c[1]}" r="${(10+pulse*26).toFixed(1)}" fill="none" stroke="${ACC}" stroke-opacity="${((1-pulse)*0.9*(1-e)*bdIn).toFixed(2)}" stroke-width="2.5"/><circle cx="${c[0]}" cy="${c[1]}" r="6" fill="${ACC}" fill-opacity="${((1-e)*bdIn).toFixed(2)}"/>`;}
  // region label
  const regOp=variant==='all'?C((t-2.7)/0.5):1;
  s+=`<text x="34" y="62" fill="#fff" fill-opacity="${(0.85*regOp).toFixed(2)}" font-size="30" font-weight="700" letter-spacing="1">${PL.region_bn}</text><rect x="34" y="74" width="${(54*regOp).toFixed(1)}" height="3" rx="1.5" fill="${ACC}"/>`;
  places.forEach((p,i)=>{
    const appear=variant==='all'?back((t-(2.9+i*0.6))/0.5):1; if(appear<=0.001)return;
    const act=variant==='all'?1:(variant===p.id?1:0), dim=variant==='all'?1:(act?1:0.38);
    const [x,y]=pr([p.lon,p.lat]),sc=Math.max(0.01,appear)*(act&&variant!=='all'?1.25:1);
    const pulse=((t*1.1+i*.3)%1);
    s+=`<g opacity="${dim}">`;
    if(act)s+=`<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="${(12+pulse*(variant==='all'?20:34)).toFixed(1)}" fill="none" stroke="${ACC}" stroke-opacity="${((1-pulse)*0.85).toFixed(2)}" stroke-width="3"/>`;
    const lw=p.bn.length*24+34,ly=y-(54*sc);
    s+=`<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)}) scale(${sc.toFixed(3)})" filter="url(#sh)"><circle r="11" fill="${ACC}" stroke="#fff" stroke-width="3"/></g>
     <g transform="translate(${x.toFixed(1)} ${(y-48*sc).toFixed(1)}) scale(${sc.toFixed(3)})" opacity="${C(appear).toFixed(2)}"><rect x="${-lw/2}" y="-22" width="${lw}" height="44" rx="22" fill="#0b1420" fill-opacity=".92" stroke="${ACC}" stroke-width="2"/><text y="9" text-anchor="middle" fill="#fff" font-size="26" font-weight="700">${p.bn}</text></g></g>`;
  });
  s+=`</g><rect x="1.5" y="1.5" width="${W-3}" height="${H-3}" rx="29" fill="none" stroke="#fff" stroke-opacity=".16" stroke-width="3"/></g></svg>`;
  return s;
}
const variants=[['all',7.5],['thanchi',4.0],['lama',4.0]];
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:W,height:H}});
await pg.goto('file://'+root+'/graphics/map.html');
for(const [v,dur] of variants){
  const dir=`${root}/graphics/frames_map_${v}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  const n=Math.round(dur*FPS);
  for(let i=0;i<n;i++){await pg.evaluate(s=>window.draw(s),frame(v,i/FPS,dur));await pg.screenshot({path:`${dir}/f_${String(i).padStart(4,'0')}.png`,omitBackground:true});}
  console.log(v,n,'frames');
}
await b.close();
