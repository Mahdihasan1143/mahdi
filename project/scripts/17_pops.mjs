// Punchline pop-ups -> transparent PNG sequences (1080x300 @30fps) + graphics/punch_timing.json (start second per item).
import {createRequire} from 'module';import fs from 'fs';import path from 'path';import {fileURLToPath} from 'url';
const require=createRequire(import.meta.url);const {chromium}=require('playwright');
const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');const FPS=30,DUR=2.1;
const cues=fs.readFileSync(root+'/subtitles/subtitles_bn.srt','utf8').trim().split(/\n\s*\n/).map(b=>{
  const l=b.split('\n');const m=l[1].match(/(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)/).slice(1).map(Number);
  return {a:m[0]*3600+m[1]*60+m[2]+m[3]/1000,b:m[4]*3600+m[5]*60+m[6]+m[7]/1000,t:l.slice(2).join(' ')}});
const cfg=JSON.parse(fs.readFileSync(root+'/graphics/punch.json','utf8'));
const br=await chromium.launch();const pg=await br.newPage({viewport:{width:1080,height:300}});
await pg.goto('file://'+root+'/graphics/pop.html');const timing=[];
for(const [i,it] of cfg.items.entries()){
  let t0=null;for(const c of cues){if(c.a<it.from)continue;const k=c.t.indexOf(it.find);if(k>=0){t0=c.a+(c.b-c.a)*(k/c.t.length);break;}}
  if(t0===null){console.log('SKIP (not found in subtitles):',it.text);continue;}
  const start=Math.max(0,t0-0.15);
  const html=it.text.split(it.hl).join('<span class="hl">'+it.hl+'</span>');await pg.evaluate(h=>window.setup(h),html);
  const dir=`${root}/graphics/frames_pop_${timing.length}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  const n=Math.round(DUR*FPS);for(let f=0;f<n;f++){await pg.evaluate(([t,d])=>window.at(t,d),[f/FPS,DUR]);await pg.screenshot({path:`${dir}/f_${String(f).padStart(4,'0')}.png`,omitBackground:true});}
  timing.push({text:it.text,start:+start.toFixed(2),dur:DUR});console.log(it.text,'@',start.toFixed(2));
}
fs.writeFileSync(root+'/graphics/punch_timing.json',JSON.stringify(timing,null,1));await br.close();
