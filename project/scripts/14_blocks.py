#!/usr/bin/env python3
"""Renders every block of analysis/plan.json from mezz/sdr30.mp4 into blocks/block_NNN.mp4 (video only, 1080x1920@30, frame-exact).
 full  : pivot-zoom close-up.   split : persistent A-top / B-bottom panels, constant background, moving highlight, swish at content swaps.
Usage: 14_blocks.py [ids...]"""
import json, os, sys, subprocess, hashlib
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
VERSION = 'v5'; PLAN = os.environ.get('PLAN', 'analysis/plan.json'); BLK = os.environ.get('BLK', 'blocks'); os.makedirs(BLK, exist_ok=True); plan = json.load(open(PLAN)); MEZ = 'mezz/sdr30_clean.mp4'
PW, PH, PX, PY_TOP, PY_BOT = 1000, 640, 40, 170, 830
clamp = lambda v, lo, hi: max(lo, min(hi, v))
WHIP = ("gblur=sigma=46:sigmaV=0:steps=1:enable='lt(t,0.07)',gblur=sigma=22:sigmaV=0:steps=1:enable='between(t,0.07,0.13)',"
        "gblur=sigma=8:sigmaV=0:steps=1:enable='between(t,0.13,0.20)'")
def crop_scale(idx, f0, f1, d):
    w0, w1 = f0[2], f1[2]; sc = clamp(400.0 / ((w0 + w1) / 2), 1.05, 1.4)
    cw = int(round(PW / sc / 2) * 2); ch = int(round(cw * PH / PW / 2) * 2)
    def pos(f): return (clamp(f[0] - cw / 2, 0, 1080 - cw), clamp(f[1] - 0.42 * ch, 0, 1920 - ch))
    (xa, ya), (xb, yb) = pos(f0), pos(f1); dd = max(d, 0.04)
    return (f"[{idx}:v]format=yuv420p,crop={cw}:{ch}:x='{xa:.1f}+({xb:.1f}-{xa:.1f})*t/{dd:.3f}':y='{ya:.1f}+({yb:.1f}-{ya:.1f})*t/{dd:.3f}',"
            f"scale={PW}:{PH}:flags=lanczos,fps=30,setpts=PTS-STARTPTS,format=yuv420p")
def build(b):
    d = b['t1'] - b['t0']; N = round(d * 30)
    if b['kind'] == 'full':
        z0, z1 = b['z0'], b['z1']; zz = f"({z0}+({z1}-{z0})*t/{d:.4f})"
        fc = (f"[0:v]scale=w='trunc(1080*{zz}/2)*2':h='trunc(1920*{zz}/2)*2':eval=frame:flags=lanczos,"
              f"crop=1080:1920:x='min(max({b['cx']:.1f}*(iw/1080-1),0),iw-1080)':y='min(max({b['cy']:.1f}*(ih/1920-1),0),ih-1920)',{WHIP if b.get('fx','whip') == 'whip' else 'null'},format=yuv420p[out]")
        return ['-ss', f"{b['t0']:.4f}", '-t', f'{d:.4f}', '-i', MEZ], fc, N
    ins, parts, idx = [], [], 0
    def panel(pieces, tag, mask):
        nonlocal idx
        labels, joins, acc = [], [], 0.0
        for i, p in enumerate(pieces):
            ins.extend(['-ss', f"{p['src0']:.4f}", '-t', f"{p['dur'] + 0.1:.4f}", '-i', MEZ])
            parts.append(crop_scale(idx, p['f0'], p['f1'], p['dur']) + f"[{tag}{i}]"); labels.append(f"[{tag}{i}]"); idx += 1
            acc += p['dur']
            if i < len(pieces) - 1: joins.append(acc)
        src = ''.join(labels)
        parts.append(f"{src}concat=n={len(pieces)}:v=1:a=0[{tag}c]" if len(pieces) > 1 else f"{src}null[{tag}c]")
        blur = ''.join(f",gblur=sigma=36:sigmaV=0:steps=1:enable='between(t,{j-0.05:.3f},{j+0.05:.3f})',gblur=sigma=14:sigmaV=0:steps=1:enable='between(t,{j-0.12:.3f},{j+0.12:.3f})'" for j in joins)
        parts.append(f"[{tag}c]format=yuva420p{blur}[{tag}r];[{tag}r][{mask}]alphamerge[{tag}m]")
    panel(b['top'], 'T', 'mk1'); panel(b['bot'], 'B', 'mk2')
    ui = idx
    ins.extend(['-loop', '1', '-framerate', '30', '-i', 'assets/ui/mask_panel.png', '-loop', '1', '-framerate', '30', '-i', 'assets/ui/border_live.png',
                '-loop', '1', '-framerate', '30', '-i', 'assets/ui/dim_panel.png'])
    expr = lambda who: '+'.join(f"between(t,{s['t0']:.3f},{s['t1']:.3f})" for s in b['spans'] if s['live'] == who) or '0'
    parts += [f"[{ui}:v]format=gray,split=2[mk1][mk2]", f"[{ui+1}:v]format=rgba,split=2[bd1][bd2]", f"[{ui+2}:v]format=rgba,split=2[dm1][dm2]",
              f"[Tm][bd1]overlay=0:0:format=auto:enable='{expr('top')}'[Tb]", f"[Tb][dm1]overlay=0:0:format=auto:enable='lt({expr('top')},0.5)'[Tf]",
              f"[Bm][bd2]overlay=0:0:format=auto:enable='{expr('bot')}'[Bb]", f"[Bb][dm2]overlay=0:0:format=auto:enable='lt({expr('bot')},0.5)'[Bf]",
              f"color=c=0x1b2331:s=1080x1920:r=30:d={d + 0.2:.3f},format=yuv420p,vignette=angle=PI/3:mode=forward[bg]"]
    if b.get('slide'):
        xt = f"{PX}-({PW}+{PX})*pow(1-min(t/0.34,1),3)"; xb = f"{PX}+({PW}+{PX})*pow(1-min(t/0.34,1),3)"
    else: xt = xb = str(PX)
    parts += [f"[bg][Tf]overlay=x='{xt}':y={PY_TOP}:format=auto[s1]", f"[s1][Bf]overlay=x='{xb}':y={PY_BOT}:format=auto,{WHIP},format=yuv420p[out]"]
    return ins, ';'.join(parts), N
def render(b):
    out = f"{BLK}/block_{b['id']:03d}.mp4"; key = hashlib.md5((VERSION + json.dumps(b, sort_keys=True)).encode()).hexdigest()[:10]; stamp = out + '.key'
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key: return out
    ins, fc, N = build(b)
    cmd = ['ffmpeg', '-hide_banner', '-v', 'error', '-y'] + ins + ['-filter_complex', fc, '-map', '[out]', '-frames:v', str(N), '-r', '30',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-an', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print('FAIL block', b['id'], r.stderr[-1200:]); sys.exit(1)
    open(stamp, 'w').write(key); return out
want = set(map(int, sys.argv[1:]))
for b in plan:
    if want and b['id'] not in want: continue
    render(b); print('ok', b['id'], b['kind'], b['t0'], b['t1'], flush=True)
