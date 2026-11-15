#!/usr/bin/env python3
"""Builds and runs the FFmpeg render. Usage: 04_render.py [out.mp4]  (env: CRF, PRESET)"""
import json, os, subprocess, sys
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
os.chdir(root)
IN, AUDIO = 'input/IMG_0611.mp4', 'audio/master.wav'
OUT = sys.argv[1] if len(sys.argv) > 1 else 'final/street_talk_cinematic_1080x1920.mp4'
SUBS = os.path.exists('subtitles/subs.ffconcat') and os.environ.get('SUBS','1')=='1'
cfg = json.load(open('graphics/config.json'))
dur = float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',IN]))
outro_t = round(dur - cfg['outro_seconds'], 3)
# Virtual-cut anchors = camera-swing moments detected in analysis/motion_candidates.txt
anchors = [0, 11.2, 27.6, 45.5, 66.8, 84.1, 96.7, 124.0, 148.2, dur + 1]
starts = [1.00, 1.12, 1.00, 1.12, 1.00, 1.12, 1.00, 1.12, 1.00]   # alternate wide / punch-in
PUSH = 0.05                                                        # slow push-in per segment
terms = [f"between(t,{a},{b})*({s}+{PUSH}*(t-{a})/({b}-{a}))"
         for a, b, s in zip(anchors[:-1], anchors[1:], starts)]
Z = '(' + '+'.join(terms) + ')'
grade = open('scripts/grade.txt').read().strip()
# Map cards (location callouts): variant, start second (approximate, from subtitle cue times), duration
MAPS = [('all', 4.0, 7.5), ('thanchi', 24.2, 4.0), ('lama', 61.9, 4.0)] if os.environ.get('MAP', '1') == '1' and os.path.isdir('graphics/frames_map_all') else []
nin = 4 + (1 if SUBS else 0)                      # next free input index (0 video,1 intro,2 outro,3 audio[,4 subs])
head = (f"[0:v]fps=60000/1001,{grade},"
 f"scale=w='2*trunc(540*{Z})':h='2*trunc(960*{Z})':eval=frame:flags=lanczos,"
 f"crop=1080:1920:x='(iw-1080)/2':y='(ih-1920)*0.40',"
 f"unsharp=5:5:0.45:5:5:0,vignette=angle=PI/7:mode=forward,noise=alls=2:allf=t[v0]")
parts, cur = [head], 'v0'
if SUBS:
    parts.append(f"[{cur}][4:v]overlay=0:1440:eof_action=repeat:format=auto[v1]"); cur = 'v1'
for i, (name, st, d) in enumerate(MAPS):
    parts.append(f"[{nin+i}:v]format=rgba,scale=500:-2,fps=60000/1001,setpts=PTS+{st}/TB[m{i}]")
    parts.append(f"[{cur}][m{i}]overlay=32:200:eof_action=pass:format=auto[vm{i}]"); cur = f'vm{i}'
parts.append(f"[{cur}]fade=t=out:st={outro_t-0.5}:d=3.2,format=yuva420p[base]")
parts.append(f"[1:v]format=rgba,fps=60000/1001[intro];[2:v]format=rgba,fps=60000/1001,setpts=PTS+{outro_t}/TB[outro]")
parts.append("[base][intro]overlay=0:0:eof_action=pass:format=auto[b1]")
parts.append("[b1][outro]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]")
fc = ';'.join(parts)
extra_in = []
for name, st, d in MAPS: extra_in += ['-framerate', str(cfg['fps']), '-i', f'graphics/frames_map_{name}/f_%04d.png']
cmd = ['ffmpeg','-hide_banner','-y','-i',IN,
  '-framerate',str(cfg['fps']),'-i','graphics/frames_intro/f_%04d.png',
  '-framerate',str(cfg['fps']),'-i','graphics/frames_outro/f_%04d.png',
  '-i',AUDIO] + (['-f','concat','-safe','0','-i','subtitles/subs.ffconcat'] if SUBS else []) + extra_in + ['-filter_complex',fc,'-map','[v]','-map','3:a',
  '-c:v','libx264','-preset',os.environ.get('PRESET','medium'),'-crf',os.environ.get('CRF','19'),
  '-profile:v','high','-level','4.2','-maxrate','14M','-bufsize','28M','-pix_fmt','yuv420p',
  '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709','-color_range','tv',
  '-c:a','aac','-b:a','256k','-ar','48000','-t',os.environ.get('LIMIT',str(dur)),'-movflags','+faststart',OUT]
open('scripts/last_ffmpeg_cmd.txt','w').write(' '.join(map(repr,cmd)))
sys.exit(subprocess.call(cmd))
