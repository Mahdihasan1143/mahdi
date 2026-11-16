#!/usr/bin/env python3
"""Clean edit plan: ONLY the raw footage, continuous, one block per shot (cuts sit on the natural camera swings).
Each block gets a very slow push-in (<=1.12x, pivoting on the face so framing stays put). No panels, no blur/flash transitions."""
import json, os, numpy as np
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
FPS = 30; snap = lambda t: round(t * FPS) / FPS
shots = json.load(open('analysis/shots.json')); faces = json.load(open('analysis/faces.json'))
for s in shots: s['t0'], s['t1'] = snap(s['t0']), snap(s['t1'])
shots[-1]['t1'] = 5101 / FPS
merged = []
for s in shots:
    if merged and s['t1'] - s['t0'] < 0.3: merged[-1]['t1'] = s['t1']
    else: merged.append(s)
def face_at(who, a, b):
    ref = [q for q in faces if q['who'] == who and a - 0.5 <= q['t'] <= b + 0.5] or [q for q in faces if q['who'] == who]
    if not ref: return [540, 800]
    mx, my, mw = [np.median([q[k] for q in ref]) for k in ('cx', 'cy', 'w')]
    good = [q for q in ref if abs(q['cx']-mx) < 160 and abs(q['cy']-my) < 200 and 0.6*mw < q['w'] < 1.6*mw] or ref
    return [float(np.median([q['cx'] for q in good])), float(np.median([q['cy'] for q in good]))]
blocks = []
for i, s in enumerate(merged):
    L = s['t1'] - s['t0']; who = s['who']
    cx, cy = face_at(who, s['t0'], s['t1']) if who in 'AB' else [540, 850]
    z1 = 1.0 + min(0.12, 0.004 * L + 0.02)
    blocks.append({'id': i, 'kind': 'full', 't0': round(s['t0'], 4), 't1': round(s['t1'], 4), 'fx': 'none', 'z0': 1.0, 'z1': round(z1, 3), 'cx': cx, 'cy': cy, 'who': who, 'interlude': False})
for x, y in zip(blocks, blocks[1:]): assert abs(x['t1'] - y['t0']) < 1e-6
json.dump(blocks, open('analysis/plan_clean.json', 'w'), indent=1); json.dump([], open('analysis/sfx_clean.json', 'w'))
print(len(blocks), 'blocks;', [(b['who'], b['t0'], b['t1'], b['z1']) for b in blocks][:8])
