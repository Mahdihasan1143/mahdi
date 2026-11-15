#!/usr/bin/env python3
"""Detect shot boundaries (camera whip-pans / cuts between people) -> analysis/shots.json, plus one representative frame per shot."""
import subprocess, json, numpy as np, os
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
W, H, FPS = 54, 96, 10
raw = subprocess.run(['ffmpeg','-v','error','-i','input/IMG_0611.mp4','-an','-vf',f'fps={FPS},scale={W}:{H},format=gray','-f','rawvideo','-'],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1,2))             # diff between consecutive frames
# global-appearance change over 0.5 s (robust to slow pans)
lag = 5; g = np.abs(fr[lag:] - fr[:-lag]).mean(axis=(1,2))
print('frames', len(fr), 'diff pctl 50/90/95/99:', np.percentile(d,[50,90,95,99]).round(1), ' lag pctl:', np.percentile(g,[50,90,95,99]).round(1))
np.save('analysis/frame_diff.npy', d)
