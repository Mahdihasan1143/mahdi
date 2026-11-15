// Place-name list graphics: items reveal one by one at the moment each name is spoken (time from subtitles_bn.srt, approximate).
// Output: graphics/frames_list_<id>/ (transparent PNG 560x480 @30fps) + graphics/list_timing.json (start/dur for render).
import {createRequire} from 'module';import fs from 'fs';import path from 'path';import {fileURLToPath} from 'url';
const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
const FPS=30,ACC='#F2A33A',BN='০১২৩৪৫৬৭৮৯';
const cues=fs.readFileSync(root+'/subtitles/subtitles_bn.srt','utf8').trim().split(/\n\s*\n/).map(b=>{
  const l=b.split('\n');const m=l[1].match(/(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)/).slice(1).map(Number);
  return {a:m[0]*3600+m[1]*60+m[2]+m[3]/1000,b:m[4]*3600+m[5]*60+m[6]+m[7]/1000,t:l.slice(2).join(' ')}});
const cfg=JSON.parse(fs.readFileSync(root+'/graphics/lists.json','utf8'));
const E=t=>t<=0?0:t>=1?1:1-Math.pow(1-t,3), C=t=>Math.max(0,Math.min(1,t));
const bnNum=n=>String(n).split('').map(d=>BN[+d]).join('');
function times(l){ // time each item is spoken
  const out=[];let prev=l.search_from-1;
  for(const w of l.items){let best=null;
    for(const c of cues){const i=c.t.indexOf(w);if(i<0)continue;const t=c.a+(c.b-c.a)*(i/c.t.length);
      if(t>prev+0.3&&t>=l.search_from-0.5&&(best===null||t<best))best=t;}
    if(best===null)throw new Error('not found in subtitles: '+w);out.push(best);prev=best;}
  return out;
}
function html(items,rel,t,dur){
  const op=Math.min(1,C((dur-t)/0.5));
  return items.map((w,i)=>{
    const p=E((t-rel[i])/0.55);if(p<=0)return '';
    const hot=C(1-(t-rel[i])/1.6)*0.9; // brief glow on the newly-spoken item
    return `<div style="display:inline-flex;align-items:center;height:92px;margin:0 0 16px;border-radius:20px;overflow:hidden;
      background:rgba(10,16,26,.66);box-shadow:0 8px 28px rgba(0,0,0,.35),0 0 ${(26*hot).toFixed(0)}px rgba(242,163,58,${(0.55*hot).toFixed(2)});
      transform:translateX(${((1-p)*-60).toFixed(1)}px);opacity:${(p*op).toFixed(3)};clear:both;float:left">
      <div style="width:9px;height:${(92*p).toFixed(0)}px;background:${ACC}"></div>
      <div style="font-size:26px;color:${ACC};padding:0 6px 0 22px;letter-spacing:1px;min-width:42px">${bnNum(i+1).padStart(2,'০')}</div>
      <div style="font-size:54px;color:#fff;padding:0 34px 0 12px;line-height:1.5;white-space:nowrap">${w}</div></div>`;}).join('');
}
const b=await chromium.launch();const pg=await b.newPage({viewport:{width:560,height:480}});
await pg.goto('file://'+root+'/graphics/list.html');const timing=[];
for(const l of cfg.lists){
  const ts=times(l),start=Math.max(0,ts[0]-0.35),rel=ts.map(t=>t-start),dur=rel[rel.length-1]+3.2;
  const dir=`${root}/graphics/frames_list_${l.id}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  const n=Math.round(dur*FPS);
  for(let i=0;i<n;i++){await pg.evaluate(h=>window.draw(h),html(l.items,rel,i/FPS,dur));await pg.screenshot({path:`${dir}/f_${String(i).padStart(4,'0')}.png`,omitBackground:true});}
  timing.push({id:l.id,start:+start.toFixed(2),dur:+dur.toFixed(2),items:l.items.map((w,i)=>({w,t:+ts[i].toFixed(2)}))});
  console.log(l.id,n,'frames; start',start.toFixed(2),'items',ts.map(x=>x.toFixed(1)).join(', '));
}
fs.writeFileSync(root+'/graphics/list_timing.json',JSON.stringify(timing,null,1));await b.close();
