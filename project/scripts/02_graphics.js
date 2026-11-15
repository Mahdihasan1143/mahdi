// Renders transparent PNG sequences of graphics/motion.html with Chromium (deterministic frame seeking).
const {chromium}=require('playwright');const fs=require('fs');const path=require('path');
const root=path.resolve(__dirname,'..');const cfg=JSON.parse(fs.readFileSync(root+'/graphics/config.json'));
(async()=>{
  const b=await chromium.launch();const p=await b.newPage({viewport:{width:1080,height:1920}});
  await p.goto('file://'+root+'/graphics/motion.html');
  for(const [mode,secs] of [['intro',cfg.intro_seconds],['outro',cfg.outro_seconds]]){
    const dir=`${root}/graphics/frames_${mode}`;fs.rmSync(dir,{recursive:true,force:true});fs.mkdirSync(dir,{recursive:true});
    await p.evaluate(([c,m])=>window.setup(c,m),[cfg,mode]);
    const n=Math.round(secs*cfg.fps);
    for(let i=0;i<n;i++){
      await p.evaluate(ms=>window.seek(ms),i/cfg.fps*1000);
      await p.screenshot({path:`${dir}/f_${String(i).padStart(4,'0')}.png`,omitBackground:true});
    }
    console.log(mode,n,'frames');
  }
  await b.close();
})();
