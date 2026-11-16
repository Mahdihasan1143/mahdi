#!/usr/bin/env python3
"""transcript_bn.txt -> subtitles_bn.srt + subtitles_bn.ass.
Transcript has only block timestamps, so cue times inside a block are distributed by character count (APPROXIMATE).
Fix exact timing by editing subtitles/subtitles_bn.srt, then run with --from-srt."""
import re, sys, os
root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..')); os.chdir(root)
BN = str.maketrans('০১২৩৪৫৬৭৮৯', '0123456789')
MAXC, MINDUR = 38, 0.9
def ts(s): m, x = s.translate(BN).split(':'); return int(m)*60 + int(x)
def srt_t(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h:02d}:{m:02d}:{int(s):02d},{int(round((s-int(s))*1000)):03d}".replace(',1000', ',999')
def ass_t(t): h=int(t//3600); m=int(t%3600//60); s=t%60; return f"{h}:{m:02d}:{s:05.2f}"
def chunks(text):
    out, cur = [], ''
    for w in text.split():
        if cur and len(cur) + 1 + len(w) > MAXC: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    if cur: out.append(cur)
    return out
import subprocess, numpy as np
def speech_clock():
    raw = subprocess.run(['ffmpeg','-v','error','-i','input/IMG_0611.mp4','-vn','-ac','1','-ar','16000','-f','s16le','-'],capture_output=True).stdout
    x = np.frombuffer(raw, np.int16).astype(np.float32) / 32768; n = len(x) // 320
    db = 20*np.log10(np.sqrt((x[:n*320].reshape(n,320)**2).mean(1)) + 1e-6)        # 20 ms frames
    thr = np.percentile(db, 20) + 9; m = (db > thr).astype(np.float32)
    m = np.convolve(m, np.ones(9)/9, 'same') > 0.4                                   # smooth ~0.18 s
    m = np.convolve(m.astype(np.float32), np.ones(11), 'same') > 0                    # bridge short gaps
    return np.concatenate([[0], np.cumsum(m)*0.02])
CLK = speech_clock() if '--uniform' not in sys.argv else None
def S(t): return float(np.interp(t, np.arange(len(CLK))*0.02, CLK))
def Sinv(v): return float(np.interp(v, CLK, np.arange(len(CLK))*0.02))
def build():
    cues, blk = [], None
    for ln in open('subtitles/transcript_bn.txt', encoding='utf-8'):
        ln = ln.rstrip('\n')
        m = re.match(r'^(\S+)\s*[–-]\s*(\S+)$', ln.strip())
        if m and not ln.startswith(' '): blk = [ts(m.group(1)), ts(m.group(2)), []]; cues.append(blk); continue
        if ln.strip().startswith('*'): blk[2] += chunks(ln.strip()[1:].strip())
    out = []
    for a, b, parts in cues:
        tot = sum(len(p) for p in parts); done = 0; Sa, Sb = (S(a), S(b)) if CLK is not None else (0, 0)
        speech = CLK is not None and (Sb - Sa) >= 0.35 * (b - a)                     # enough speech in the block to trust it
        tm = (lambda f: Sinv(Sa + f * (Sb - Sa))) if speech else (lambda f: a + f * (b - a))
        blk = []
        for p in parts:
            f0, f1 = done / tot, (done + len(p)) / tot; blk.append([tm(f0), tm(f1), p]); done += len(p)
        for i, q in enumerate(blk):
            nxt = blk[i+1][0] if i + 1 < len(blk) else b
            q[1] = max(q[0] + MINDUR, min(nxt - 0.02, q[1] + 0.3)); q[1] = min(q[1], b if i + 1 == len(blk) else q[1])
        out += blk
    return out
def read_srt():
    out = []
    for blk in re.split(r'\n\s*\n', open('subtitles/subtitles_bn.srt', encoding='utf-8').read().strip()):
        l = blk.split('\n'); m = re.match(r'(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)', l[1]); g = list(map(int, m.groups()))
        out.append([g[0]*3600+g[1]*60+g[2]+g[3]/1000, g[4]*3600+g[5]*60+g[6]+g[7]/1000, ' '.join(l[2:])])
    return out
cues = read_srt() if '--from-srt' in sys.argv else build()
if '--from-srt' not in sys.argv:
    open('subtitles/subtitles_bn.srt', 'w', encoding='utf-8').write('\n'.join(f"{i}\n{srt_t(a)} --> {srt_t(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)))
hdr = """[Script Info]
ScriptType: v4.00+
PlayResX: 1080
PlayResY: 1920
WrapStyle: 0
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding
Style: Default,Noto Sans Bengali,54,&H00FFFFFF,&H000000FF,&H00101010,&H80000000,-1,0,0,0,100,100,0,0,1,3.2,1.5,2,90,90,330,1

[Events]
Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text
"""
open('subtitles/subtitles_bn.ass', 'w', encoding='utf-8').write(hdr + '\n'.join(
    f"Dialogue: 0,{ass_t(a)},{ass_t(b)},Default,,0,0,0,,{{\\fad(120,120)}}{t}" for a, b, t in cues) + '\n')
print(len(cues), 'cues; first', ass_t(cues[0][0]), 'last end', ass_t(cues[-1][1]))
