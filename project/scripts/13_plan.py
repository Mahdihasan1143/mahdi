#!/usr/bin/env python3
"""Builds analysis/plan.json: a continuous list of blocks covering 0..170.03 s (no content removed).
 full  = single close-up (pivot zoom on the face) ; split = A on top / B at the bottom, live speaker panel highlighted.
Partner (listener) panel = nearest footage of the OTHER person (NOT simultaneous - see report).  Edit plan.json by hand to tweak."""
import json, os, numpy as np
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DUR = 170.033
shots = json.load(open('analysis/shots.json')); faces = json.load(open('analysis/faces.json'))
shots[-1]['t1'] = DUR
def track(who, a, b):
    f = [q for q in faces if q['who'] == who and a - 0.5 <= q['t'] <= b + 0.5]
    allp = [q for q in faces if q['who'] == who]
    ref = f if len(f) >= 3 else allp
    mx, my, mw = [np.median([q[k] for q in ref]) for k in ('cx', 'cy', 'w')]
    good = [q for q in ref if abs(q['cx']-mx) < 160 and abs(q['cy']-my) < 200 and 0.6*mw < q['w'] < 1.6*mw]
    if len(good) < 2: good = ref
    ts = np.array([q['t'] for q in good]); P = np.array([[q['cx'], q['cy'], q['w']] for q in good])
    def at(t):  # smoothed value near t (gaussian-weighted average of detections within the shot)
        w = np.exp(-((ts - t) / 1.2) ** 2); w = w + 1e-6
        return [float(x) for x in (w[:, None] * P).sum(0) / w.sum()]
    return at
tracks = {}
def get_track(i): 
    if i not in tracks: s = shots[i]; tracks[i] = track(s['who'], s['t0'], s['t1'])
    return tracks[i]
usable = lambda s: s['who'] in 'AB' and (s['t1'] - s['t0']) >= 2.0
def partners(i):
    who = shots[i]['who']; o = 'B' if who == 'A' else 'A'; t = (shots[i]['t0'] + shots[i]['t1']) / 2
    c = [j for j, s in enumerate(shots) if s['who'] == o and usable(s)]
    return sorted(c, key=lambda j: abs((shots[j]['t0'] + shots[j]['t1']) / 2 - t))[:3]
ptr = {}   # per partner-shot read pointer so reaction windows differ from block to block
blocks = []
def add(**k): k['id'] = len(blocks); blocks.append(k)
for i, s in enumerate(shots):
    a, b, who = s['t0'], s['t1'], s['who']; L = b - a
    if L < 0.05: continue
    if who not in 'AB' or L < 2.6:
        z0, z1 = (1.0, 1.06)
        pt = get_track(i)(a + L/2) if who in 'AB' else [540, 800, 250]
        add(kind='full', t0=round(a,2), t1=round(b,2), fx='whip', z0=z0, z1=z1, cx=pt[0], cy=pt[1], who=who); continue
    pattern = [('full', 1.7), ('split', 4.0), ('full', 2.6), ('split', 4.0)]
    t, k, first = a, 0, True
    while t < b - 0.01:
        kind, ln = pattern[k % 4]; k += 1
        end = t + ln
        if b - end < 2.0: end = b
        end = min(end, b)
        if kind == 'split':
            sp = None
            for j in partners(i):
                P = shots[j]; lo, hi = P['t0'] + 0.5, P['t1'] - 0.4; d = end - t
                if hi - lo < min(d, 1.8): continue
                st = max(lo, min(ptr.get(j, lo), hi - min(d, hi - lo)))
                ptr[j] = st + d if st + d < hi else lo
                sp = (j, st, min(d, hi - st)); break
            if sp is None or sp[2] < 1.5: kind = 'full'
            else:
                j, st, dd = sp; end = t + dd if dd < end - t - 0.01 else end
        fx = 'whip' if first else 'flash'
        if kind == 'full':
            big = (k % 4 == 3)
            zmax = 1.35 if who == 'B' else 1.22
            z0, z1 = (1.14, zmax) if big else (1.0, 1.08)
            pt = get_track(i)(t + (end - t)/2)
            add(kind='full', t0=round(t,2), t1=round(end,2), fx=fx, z0=z0, z1=z1, cx=pt[0], cy=pt[1], who=who)
        else:
            j, st, dd = sp; d = end - t
            lv0, lv1 = get_track(i)(t), get_track(i)(end)
            p0, p1 = get_track(j)(st), get_track(j)(st + d)
            live = {'src': [round(t,2), round(end,2)], 'f0': lv0, 'f1': lv1}
            part = {'src': [round(st,2), round(st + d,2)], 'f0': p0, 'f1': p1}
            top, bot = (live, part) if who == 'A' else (part, live)
            add(kind='split', t0=round(t,2), t1=round(end,2), fx=fx, who=who, live='top' if who == 'A' else 'bot', top=top, bot=bot)
        t = end; first = False
# make blocks tile the timeline exactly
for x, y in zip(blocks, blocks[1:]): y['t0'] = x['t1']
blocks[-1]['t1'] = DUR
json.dump(blocks, open('analysis/plan.json', 'w'), indent=1)
n = lambda k: sum(1 for b in blocks if b['kind'] == k)
print(len(blocks), 'blocks:', n('full'), 'full,', n('split'), 'split;', 'split time', round(sum(b['t1']-b['t0'] for b in blocks if b['kind']=='split'),1), 's')
for b in blocks[:14]: print(b['id'], b['kind'], b['fx'], b['t0'], b['t1'], b.get('who'))
