// Renders each cue in subtitles/subtitles_bn.srt as a transparent PNG band (1080x300) with Chromium (correct Bengali shaping),
// then writes subtitles/subs.ffconcat (timed image list incl. blank gaps) for FFmpeg overlay.
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const root=path.resolve(__dirname,'..');const END=Number(process.env.SUB_END||169.0);
const cues=fs.readFileSync(root+'/subtitles/subtitles_bn.srt','utf8').trim().split(/\n\s*\n/).map(b=>{
  const l=b.split('\n');const m=l[1].match(/(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)/).slice(1).map(Number);
  return {a:m[0]*3600+m[1]*60+m[2]+m[3]/1000,b:m[4]*3600+m[5]*60+m[6]+m[7]/1000,t:l.slice(2).join(' ')}});
(async()=>{
  const dir=root+'/subtitles/png';fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
  const br=await chromium.launch();const p=await br.newPage({viewport:{width:1080,height:300}});
  await p.goto('file://'+root+'/graphics/subtitle.html');
  await p.evaluate(()=>window.setText(''));await p.screenshot({path:dir+'/blank.png',omitBackground:true});
  const lines=['ffconcat version 1.0'];let t=0;
  for(let i=0;i<cues.length;i++){
    const c=cues[i];const a=Math.max(c.a,t),b=Math.min(c.b,END);if(b<=a)continue;
    if(a>t+0.001)lines.push(`file 'png/blank.png'`,`duration ${(a-t).toFixed(3)}`);
    const f=`cue_${String(i+1).padStart(3,'0')}.png`;
    await p.evaluate(s=>window.setText(s),c.t);await p.screenshot({path:`${dir}/${f}`,omitBackground:true});
    lines.push(`file 'png/${f}'`,`duration ${(b-a).toFixed(3)}`);t=b;
  }
  lines.push(`file 'png/blank.png'`,`duration 5`,`file 'png/blank.png'`);
  fs.writeFileSync(root+'/subtitles/subs.ffconcat',lines.join('\n')+'\n');
  await br.close();console.log(cues.length,'cues rendered');
})();
