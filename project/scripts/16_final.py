#!/usr/bin/env python3
"""Final composite: concat blocks -> Hollywood grade + grain + vignette -> subtitles + place lists + title/outro -> mux master_v2 audio. Usage: 16_final.py [out.mp4]"""
import json, os, subprocess, sys
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
OUT = sys.argv[1] if len(sys.argv) > 1 else 'final/street_talk_v2_1080x1920.mp4'
plan = json.load(open('analysis/plan.json')); cfg = json.load(open('graphics/config.json')); DUR = 170.033
lists = json.load(open('graphics/list_timing.json')) if os.environ.get('LISTS', '1') == '1' else []
open('blocks/blocks.txt', 'w').write('ffconcat version 1.0\n' + ''.join(f"file 'block_{b['id']:03d}.mp4'\n" for b in plan))
grade = open('scripts/grade_dslr.txt').read().strip()
pops = json.load(open('graphics/punch_timing.json')) if os.path.exists('graphics/punch_timing.json') else []; outro_t = round(DUR - cfg['outro_seconds'], 3)
ins = ['-f', 'concat', '-safe', '0', '-i', 'blocks/blocks.txt', '-i', 'audio/master_v2.wav', '-f', 'concat', '-safe', '0', '-i', 'subtitles/subs.ffconcat',
       '-framerate', '30', '-i', 'graphics/frames_intro/f_%04d.png', '-framerate', '30', '-i', 'graphics/frames_outro/f_%04d.png']
for l in lists: ins += ['-framerate', '30', '-i', f"graphics/frames_list_{l['id']}/f_%04d.png"]
for i, q in enumerate(pops): ins += ['-framerate', '30', '-i', f"graphics/frames_pop_{i}/f_%04d.png"]
parts = [f"[0:v]fps=30,{grade},format=yuv420p[g]",
         "[g][2:v]overlay=0:1440:eof_action=repeat:format=auto[v1]"]; cur = 'v1'
for i, l in enumerate(lists):
    parts.append(f"[{5+i}:v]format=rgba,setpts=PTS+{l['start']}/TB[ls{i}]"); parts.append(f"[{cur}][ls{i}]overlay=30:215:eof_action=pass:format=auto[vl{i}]"); cur = f'vl{i}'
for i, q in enumerate(pops):
    n = 5 + len(lists) + i; parts.append(f"[{n}:v]format=rgba,setpts=PTS+{q['start']}/TB[pp{i}]"); parts.append(f"[{cur}][pp{i}]overlay=0:660:eof_action=pass:format=auto[vp{i}]"); cur = f'vp{i}'
parts.append(f"[{cur}]fade=t=out:st={outro_t-0.5}:d=3.2,format=yuva420p[base]")
parts.append(f"[3:v]format=rgba[intro];[4:v]format=rgba,setpts=PTS+{outro_t}/TB[outro]")
parts.append("[base][intro]overlay=0:0:eof_action=pass:format=auto[b1];[b1][outro]overlay=0:0:eof_action=pass:format=auto,format=yuv420p[v]")
cmd = ['ffmpeg', '-hide_banner', '-y'] + ins + ['-filter_complex', ';'.join(parts), '-map', '[v]', '-map', '1:a', '-t', os.environ.get('LIMIT', str(DUR)),
       '-r', '30', '-c:v', 'libx264', '-preset', os.environ.get('PRESET', 'medium'), '-crf', os.environ.get('CRF', '15'), '-profile:v', 'high', '-level', '4.2',
       '-maxrate', '20M', '-bufsize', '40M', '-pix_fmt', 'yuv420p', '-colorspace', 'bt709', '-color_primaries', 'bt709', '-color_trc', 'bt709', '-color_range', 'tv',
       '-c:a', 'aac', '-b:a', '256k', '-ar', '48000', '-movflags', '+faststart', OUT]
open('scripts/last_final_cmd.txt', 'w').write(' '.join(map(repr, cmd))); sys.exit(subprocess.call(cmd))
