#!/usr/bin/env python3
"""Refine shot boundaries (camera whip peaks) and detect faces per person-shot on the SDR mezzanine.
Nominal shots were labelled by eye from 1-fps contact sheets: A = glasses + dark jersey, B = grey kurta, C = black t-shirt, X = mixed/other.
Writes analysis/shots.json and analysis/faces.json (source-pixel coords, 1080x1920)."""
import json, os, subprocess, numpy as np, cv2
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DUR = 170.0
NOMINAL = [(0.0,'B'),(1.0,'A'),(3.0,'B'),(6.0,'A'),(10.0,'B'),(20.0,'C'),(23.0,'A'),(28.0,'B'),(46.0,'A'),(65.0,'X'),
           (67.5,'B'),(70.0,'C'),(71.0,'A'),(91.0,'B'),(93.0,'A'),(97.0,'B'),(115.0,'A'),(123.0,'B'),(147.0,'A'),(160.0,'B')]
W, H = 54, 96
raw = subprocess.run(['ffmpeg','-v','error','-i','mezz/sdr30.mp4','-an','-vf',f'scale={W}:{H},format=gray','-f','rawvideo','-'],capture_output=True).stdout
fr = np.frombuffer(raw, np.uint8).reshape(-1, H, W).astype(np.float32)
d = np.abs(np.diff(fr, axis=0)).mean(axis=(1,2)); d = np.convolve(d, np.ones(3)/3, mode='same')
bounds = [0.0]
for t, _ in NOMINAL[1:]:
    lo, hi = max(0, int((t-1.0)*30)), min(len(d)-1, int((t+1.0)*30))
    bounds.append(round((lo + int(np.argmax(d[lo:hi]))) / 30.0, 2))
bounds.append(DUR)
shots = [{'t0': bounds[i], 't1': bounds[i+1], 'who': NOMINAL[i][1]} for i in range(len(NOMINAL))]
json.dump(shots, open('analysis/shots.json','w'), indent=1)
print('shots:', [(s['who'], s['t0'], s['t1']) for s in shots])
# --- faces ---
casc = [cv2.CascadeClassifier(cv2.data.haarcascades + n) for n in ('haarcascade_frontalface_alt2.xml','haarcascade_frontalface_default.xml','haarcascade_profileface.xml')]
eye = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_eye.xml')
cap = cv2.VideoCapture('mezz/sdr30.mp4'); faces = []
for s in shots:
    if s['who'] not in 'AB': continue
    t = s['t0'] + 0.4
    while t < s['t1'] - 0.3:
        cap.set(cv2.CAP_PROP_POS_MSEC, t*1000); ok, im = cap.read()
        if ok:
            g = cv2.cvtColor(cv2.resize(im, (540, 960)), cv2.COLOR_BGR2GRAY); g = cv2.equalizeHist(g)
            best = None
            for c in casc:
                r = c.detectMultiScale(g, 1.1, 5, minSize=(36, 36))
                for (x, y, w, h) in r:
                    roi = g[y:y+int(0.6*h), x:x+w]                                  # a real face has an eye in its upper part
                    if len(eye.detectMultiScale(roi, 1.1, 3, minSize=(max(8, w//10), max(8, w//10)))) < 1: continue
                    if not (450 <= (y + h/2) * 2 <= 1250): continue                 # faces sit in the upper-middle of the frame
                    if best is None or w > best[2]: best = (x, y, w, h)
                if best is not None: break
            if best is not None:
                x, y, w, h = [v*2 for v in best]
                faces.append({'t': round(t,2), 'who': s['who'], 'cx': float(x+w/2), 'cy': float(y+h/2), 'w': float(w)})
        t += 0.4
json.dump(faces, open('analysis/faces.json','w'))
for who in 'AB':
    f = [q for q in faces if q['who']==who]; print(who, len(f), 'detections; median cx,cy,w:', [int(np.median([q[k] for q in f])) for k in ('cx','cy','w')] if f else None)
