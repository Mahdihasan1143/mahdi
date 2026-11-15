#!/usr/bin/env python3
"""Renders every block of analysis/plan.json from mezz/sdr30.mp4 into blocks/block_NNN.mp4 (video only, 1080x1920@30). Usage: 14_blocks.py [ids...]"""
import json, os, sys, subprocess, hashlib
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
plan = json.load(open('analysis/plan.json')); MEZ = 'mezz/sdr30.mp4'
PW, PH, PX, PY_TOP, PY_BOT = 1000, 640, 40, 170, 830
clamp = lambda v, lo, hi: max(lo, min(hi, v))
FX = {
 'whip': "gblur=sigma=46:sigmaV=0:steps=1:enable='lt(t,0.07)',gblur=sigma=22:sigmaV=0:steps=1:enable='between(t,0.07,0.13)',gblur=sigma=8:sigmaV=0:steps=1:enable='between(t,0.13,0.20)'",
 'flash': "eq=brightness='0.30*max(0,1-t/0.12)':eval=frame",
 'none': "null"}
def panel(src, f0, f1, d, tag, mask):
    w0, w1 = f0[2], f1[2]; sc = clamp(400.0 / ((w0 + w1) / 2), 1.05, 1.75)
    cw = int(round(PW / sc / 2) * 2); ch = int(round(cw * PH / PW / 2) * 2)
    def pos(f): return (clamp(f[0] - cw / 2, 0, 1080 - cw), clamp(f[1] - 0.42 * ch, 0, 1920 - ch))
    (xa, ya), (xb, yb) = pos(f0), pos(f1)
    return (f"{src}crop={cw}:{ch}:x='{xa:.1f}+({xb:.1f}-{xa:.1f})*t/{d:.3f}':y='{ya:.1f}+({yb:.1f}-{ya:.1f})*t/{d:.3f}',"
            f"scale={PW}:{PH}:flags=lanczos,format=yuva420p[{tag}r];[{tag}r][{mask}]alphamerge[{tag}m]")
def build(b):
    d = round(b['t1'] - b['t0'], 3); fx = FX[b['fx']]; ins = ['-ss', f"{b['t0']}", '-t', f'{d}', '-i', MEZ]
    if b['kind'] == 'full':
        z0, z1 = b['z0'], b['z1']; pulse = '+0.07*exp(-t*9)' if b['fx'] == 'flash' else ''
        zz = f"({z0}+({z1}-{z0})*t/{d}{pulse})"
        fc = (f"[0:v]scale=w='trunc(1080*{zz}/2)*2':h='trunc(1920*{zz}/2)*2':eval=frame:flags=lanczos,"
              f"crop=1080:1920:x='min(max({b['cx']:.1f}*(iw/1080-1),0),iw-1080)':y='min(max({b['cy']:.1f}*(ih/1920-1),0),ih-1920)',{fx},format=yuv420p[out]")
        return ins, fc, d
    top, bot = b['top'], b['bot']; live = b['live']
    live_p, other_p = (top, bot) if live == 'top' else (bot, top)
    # inputs: 0 live source (also blurred background), 1 partner source, 2 mask, 3 live border, 4 dim overlay
    ins += ['-ss', f"{other_p['src'][0]}", '-t', f'{d}', '-i', MEZ, '-loop', '1', '-framerate', '30', '-i', 'assets/ui/mask_panel.png',
            '-loop', '1', '-framerate', '30', '-i', 'assets/ui/border_live.png', '-loop', '1', '-framerate', '30', '-i', 'assets/ui/dim_panel.png']
    parts = ["[2:v]format=gray,split=2[mk1][mk2]", "[0:v]format=yuv420p,split=2[l0][l1]",
             "[l1]scale=1080:1920,gblur=sigma=38:steps=2,eq=brightness=-0.32:saturation=0.75[bg]",
             panel('[l0]', live_p['f0'], live_p['f1'], d, 'L', 'mk1'),
             panel('[1:v]format=yuv420p,', other_p['f0'], other_p['f1'], d, 'O', 'mk2'),
             "[3:v]format=rgba[bord]", "[4:v]format=rgba[dim]",
             "[Lm][bord]overlay=0:0:format=auto[Lf]", "[Om][dim]overlay=0:0:format=auto[Of]"]
    ptop, pbot = ('Lf', 'Of') if live == 'top' else ('Of', 'Lf')
    parts.append(f"[bg][{ptop}]overlay=x='{PX}-({PW}+{PX})*pow(1-min(t/0.34\\,1)\\,3)':y={PY_TOP}:format=auto[s1]")
    parts.append(f"[s1][{pbot}]overlay=x='{PX}+({PW}+{PX})*pow(1-min(t/0.34\\,1)\\,3)':y={PY_BOT}:format=auto,{fx},format=yuv420p[out]")
    return ins, ';'.join(parts), d
def render(b):
    out = f"blocks/block_{b['id']:03d}.mp4"; key = hashlib.md5(json.dumps(b, sort_keys=True).encode()).hexdigest()[:10]
    stamp = out + '.key'
    if os.path.exists(out) and os.path.exists(stamp) and open(stamp).read() == key: return out
    ins, fc, d = build(b)
    cmd = ['ffmpeg', '-hide_banner', '-v', 'error', '-y'] + ins + ['-filter_complex', fc, '-map', '[out]', '-t', f'{d}', '-r', '30',
           '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '14', '-pix_fmt', 'yuv420p', '-an', out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode: print('FAIL block', b['id'], r.stderr[-900:]); sys.exit(1)
    open(stamp, 'w').write(key); return out
want = set(map(int, sys.argv[1:]))
for b in plan:
    if want and b['id'] not in want: continue
    render(b); print('ok', b['id'], b['kind'], b['fx'], b['t0'], b['t1'], flush=True)
