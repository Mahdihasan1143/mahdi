#!/usr/bin/env python3
"""Builds analysis/plan.json (v2, persistent split-screen).
 - Split sequences keep the same two panels on screen (A top / B bottom); panels slide in ONCE per sequence, the background is constant,
   the live-speaker highlight moves between panels, and panel content only changes at camera swings (masked by a horizontal swish).
 - Listener (partner) footage plays continuously from a moving cursor instead of restarting for every block.
 - Every ~11 s a short full-screen close-up 'interlude' of the live person is inserted (swish in, swish out; panels return WITHOUT sliding).
Edit plan.json by hand to tweak."""
import json, os, numpy as np
os.chdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DUR = 170.033; SPLIT_FROM, SPLIT_TO, EVERY, INTERLUDE = 6.03, 166.0, 11.0, 2.4
shots = json.load(open('analysis/shots.json')); faces = json.load(open('analysis/faces.json')); shots[-1]['t1'] = DUR
FPS = 30; snap = lambda t: round(t * FPS) / FPS
for s in shots: s['t0'], s['t1'] = snap(s['t0']), snap(s['t1'])
shots[-1]['t1'] = 5101 / FPS
merged = []
for s in shots:                                   # fold sub-0.3 s slivers (a whip peak that is only a frame or two) into the previous shot
    if merged and s['t1'] - s['t0'] < 0.3: merged[-1]['t1'] = s['t1']
    else: merged.append(s)
shots = merged; DUR = shots[-1]['t1']
def track(who, a, b):
    ref = [q for q in faces if q['who'] == who and a - 0.5 <= q['t'] <= b + 0.5]
    if len(ref) < 3: ref = [q for q in faces if q['who'] == who]
    mx, my, mw = [np.median([q[k] for q in ref]) for k in ('cx', 'cy', 'w')]
    good = [q for q in ref if abs(q['cx']-mx) < 160 and abs(q['cy']-my) < 200 and 0.6*mw < q['w'] < 1.6*mw] or ref
    ts = np.array([q['t'] for q in good]); P = np.array([[q['cx'], q['cy'], q['w']] for q in good])
    def at(t):
        w = np.exp(-((ts - t) / 1.2) ** 2) + 1e-6
        return [float(x) for x in (w[:, None] * P).sum(0) / w.sum()]
    return at
trk = {}
def tr(j):
    if j not in trk: trk[j] = track(shots[j]['who'], shots[j]['t0'], shots[j]['t1'])
    return trk[j]
usable = lambda s: s['who'] in 'AB' and (s['t1'] - s['t0']) >= 2.0
mid = lambda j: (shots[j]['t0'] + shots[j]['t1']) / 2
cur = {}   # per person: (shot index, cursor time) -> listener footage keeps playing instead of restarting
def take(P, dur, exclude, center):
    out, need, last = [], dur, None
    for _ in range(40):
        if need < 0.03: break
        j, t = cur.get(P, (None, 0))
        ok = j is not None and j not in exclude and shots[j]['t1'] - 0.4 - t >= 0.8 and abs(mid(j) - center) < 60
        if not ok:
            c = [k for k, s in enumerate(shots) if s['who'] == P and usable(s) and k not in exclude and k != last and (s['t1'] - s['t0']) >= 2.0]
            if not c: return None
            j = min(c, key=lambda k: abs(mid(k) - center)); t = shots[j]['t0'] + 0.5
        avail = shots[j]['t1'] - 0.4 - t; d = min(need, avail)
        if 0 < need - d < 0.7 and need - 0.7 >= 0.7: d = need - 0.7      # never leave a sliver piece (it would flicker at the join)
        out.append({'src0': round(t, 3), 'dur': round(d, 3), 'f0': tr(j)(t), 'f1': tr(j)(t + d), 'shot': j}); cur[P] = (j, t + d); need -= d; last = j
    for i, q in enumerate(out):                      # no piece shorter than 0.7 s: borrow time from the previous piece
        if q['dur'] < 0.7 and i > 0 and out[i-1]['dur'] - (0.7 - q['dur']) >= 0.7:
            pv = out[i-1]; pv['dur'] = round(pv['dur'] - (0.7 - q['dur']), 3); pv['f1'] = tr(pv['shot'])(pv['src0'] + pv['dur'])
            sh = shots[q['shot']]; q['dur'] = 0.7; q['src0'] = round(max(sh['t0'] + 0.3, min(q['src0'], sh['t1'] - 0.4 - 0.7)), 3)
            q['f0'], q['f1'] = tr(q['shot'])(q['src0']), tr(q['shot'])(q['src0'] + 0.7)
    return out
blocks = []
def add(**k): k['id'] = len(blocks); blocks.append(k)
seq = []                      # pending split slices [(shot_idx, t0, t1)]
def fit(ps, total):                               # make piece durations whole frames that sum exactly to the block length
    fr = [max(1, round(p['dur'] * FPS)) for p in ps]; fr[-1] += round(total * FPS) - sum(fr)
    for p, f in zip(ps, fr): p['dur'] = f / FPS
    return ps
def flush(slide):
    global seq
    if not seq: return
    t0, t1 = seq[0][1], seq[-1][2]; ex = {s[0] for s in seq}; top, bot, spans, rel = [], [], [], 0.0
    ok = True
    for j, a, b in seq:
        d = b - a; who = shots[j]['who']
        live = [{'src0': round(a, 3), 'dur': round(d, 3), 'f0': tr(j)(a), 'f1': tr(j)(b), 'shot': j}]
        other = take('B' if who == 'A' else 'A', d, ex, (a + b) / 2)
        if other is None: ok = False; break
        top += live if who == 'A' else other; bot += live if who == 'B' else other
        spans.append({'t0': round(rel, 3), 't1': round(rel + d, 3), 'live': 'top' if who == 'A' else 'bot'}); rel += d
    if ok: add(kind='split', t0=t0, t1=t1, fx='whip', slide=slide, top=fit(top, t1 - t0), bot=fit(bot, t1 - t0), spans=spans)
    else:
        for j, a, b in seq: add(kind='full', t0=a, t1=b, fx='whip', z0=1.0, z1=1.07, who=shots[j]['who'], cx=tr(j)((a+b)/2)[0], cy=tr(j)((a+b)/2)[1], interlude=False)
    seq = []
def full(j, a, b, interlude, z0=1.0, z1=1.07):
    who = shots[j]['who']; pt = tr(j)((a + b) / 2) if who in 'AB' else [540, 800, 250]
    add(kind='full', t0=a, t1=b, fx='whip', z0=z0, z1=z1, who=who, cx=pt[0], cy=pt[1], interlude=interlude)
since, slide_next = 0.0, True
for j, s in enumerate(shots):
    a, b = s['t0'], min(s['t1'], DUR)
    if b - a < 0.05: continue
    split_ok = s['who'] in 'AB' and b - a >= 1.4 and a >= SPLIT_FROM - 0.05 and b <= SPLIT_TO + 0.05
    if not split_ok:
        flush(slide_next); full(j, a, b, False); since = 0.0; slide_next = True; continue
    t = a
    while t < b - 0.01:
        budget = EVERY - since
        if budget < 0.05: budget = 0.0                       # guard against float dust producing zero-length slices
        if t == a and 0 < budget < 1.5: budget = 1.5          # never leave a sliver slice at the start of a shot
        if budget <= 0 and b - t >= INTERLUDE + 2.5:
            flush(slide_next); slide_next = False
            full(j, t, t + INTERLUDE, True, 1.12, 1.24 if s['who'] == 'A' else 1.32); t += INTERLUDE; since = 0.0; continue
        if b - t > max(budget, 0.1) + INTERLUDE + 2.5 and budget > 0:
            e = t + budget; seq.append((j, t, e)); since += e - t; t = e
        else:
            seq.append((j, t, b)); since += b - t; t = b
flush(slide_next)
for x, y in zip(blocks, blocks[1:]): assert abs(y['t0'] - x['t1']) < 1e-6, (x['id'], x['t1'], y['t0'])
assert abs(blocks[0]['t0']) < 1e-6 and abs(blocks[-1]['t1'] - DUR) < 1e-6
for b in blocks: b['t0'], b['t1'] = round(b['t0'], 4), round(b['t1'], 4)
json.dump(blocks, open('analysis/plan.json', 'w'), indent=1)
# SFX times: block starts (whip) + panel-content swaps inside split blocks
sfx = [b['t0'] for b in blocks if b['t0'] > 0.5]
for b in blocks:
    if b['kind'] == 'split': sfx += [round(b['t0'] + sp['t0'], 3) for sp in b['spans'][1:]]
json.dump(sorted(set(round(x, 2) for x in sfx)), open('analysis/sfx_times.json', 'w'))
n = lambda k: sum(1 for b in blocks if b['kind'] == k)
print(len(blocks), 'blocks:', n('full'), 'full (', sum(1 for b in blocks if b.get('interlude')), 'interludes ),', n('split'), 'split;', 'split time', round(sum(b['t1']-b['t0'] for b in blocks if b['kind']=='split'), 1), 's; slide-ins:', sum(1 for b in blocks if b.get('slide')))
for b in blocks: print(b['id'], b['kind'], b['t0'], b['t1'], 'slide' if b.get('slide') else '', 'interlude' if b.get('interlude') else '', len(b.get('top', [])), len(b.get('bot', [])))
