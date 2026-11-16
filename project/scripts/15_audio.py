#!/usr/bin/env python3
"""Dialogue cleanup + synthesized SFX synced to plan.json cuts + 2-pass loudnorm (-14 LUFS / -1.5 dBTP) -> audio/master_v2.wav"""
import json, os, subprocess, re
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
plan = json.load(open('analysis/plan.json')); DUR = 170.033; cfg = json.load(open('graphics/config.json'))
CHAIN = "highpass=f=80,afftdn=nr=9:nf=-38,equalizer=f=250:t=q:w=1.2:g=-1.5,equalizer=f=3200:t=q:w=1:g=1.8,acompressor=threshold=-21dB:ratio=2.5:attack=15:release=220:makeup=2"
whoosh = [round(max(0, t - 0.9), 3) for t in json.load(open('analysis/sfx_times.json'))]   # block starts + panel swaps (swish)
hits = []
outro_t = DUR - cfg['outro_seconds']
ms = lambda t: int(t * 1000)
parts = [f"[0:a:0]{CHAIN}[d]"]; mix = ['[d]']
def fan(idx, n, name, chain, times):
    if not times: return
    parts.append(f"[{idx}:a]asplit={len(times)}" + ''.join(f"[{name}{i}]" for i in range(len(times))))
    for i, t in enumerate(times):
        parts.append(f"[{name}{i}]{chain},adelay={ms(t)}|{ms(t)}[{name}o{i}]"); mix.append(f"[{name}o{i}]")
fan(1, 0, 'w', 'volume=0.24', whoosh)
fan(2, 0, 'h', 'atrim=0:0.75,afade=t=out:st=0.35:d=0.4,volume=0.20', hits)
parts.append(f"[2:a]volume=0.35,adelay=300|300[i0]"); mix.append('[i0]')
parts.append(f"[3:a]volume=0.12,adelay={ms(outro_t)}|{ms(outro_t)}[o0]"); mix.append('[o0]')
parts.append(f"{''.join(mix)}amix=inputs={len(mix)}:normalize=0:duration=first:dropout_transition=0[m]")
sh = lambda c: subprocess.run(c, capture_output=True, text=True)
r = sh(['ffmpeg','-hide_banner','-v','error','-y','-i','input/IMG_0611.mp4','-i','audio/sfx_whoosh.wav','-i','audio/sfx_impact.wav','-i','audio/sfx_outro_drone.wav',
        '-filter_complex', ';'.join(parts), '-map', '[m]', '-t', str(DUR), '-ar', '48000', '-c:a', 'pcm_s24le', 'audio/premaster_v2.wav'])
if r.returncode: raise SystemExit(r.stderr[-1500:])
m = sh(['ffmpeg','-hide_banner','-nostats','-i','audio/premaster_v2.wav','-af','loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json','-f','null','-']).stderr
j = json.loads(re.search(r'\{.*\}', m, re.S).group(0))
ln = (f"loudnorm=I=-14:TP=-1.5:LRA=11:measured_I={j['input_i']}:measured_TP={j['input_tp']}:measured_LRA={j['input_lra']}:measured_thresh={j['input_thresh']}:offset={j['target_offset']}:linear=true")
r = sh(['ffmpeg','-hide_banner','-v','error','-y','-i','audio/premaster_v2.wav','-af', f"{ln},afade=t=in:d=0.25,afade=t=out:st={DUR-2.2:.3f}:d=2.2:curve=hsin,alimiter=limit=0.84:level=false",
        '-ar','48000','-c:a','pcm_s24le','audio/master_v2.wav'])
if r.returncode: raise SystemExit(r.stderr[-1500:])
print('whoosh', len(whoosh), 'hits', len(hits))
print(sh(['ffmpeg','-hide_banner','-nostats','-i','audio/master_v2.wav','-af','ebur128=peak=true','-f','null','-']).stderr.split('Summary:')[-1][:420])
