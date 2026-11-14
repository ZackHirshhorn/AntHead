"""Find M3 insert bores (4.7 mm) at any orientation and convert them (nut slot if clean, else pilot)."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, trimesh
from scipy.spatial import cKDTree
from auto import annulus_out
import slot2d
from run_part import approach
def bores(m, r=2.35, tol=0.08, min_len=2.4, skip_axis_aligned=True):
    N = m.face_normals; C = m.triangles_center
    q = C + r * N                                    # concave bore: normal points to the axis
    tree = cKDTree(q); seen = np.zeros(len(q), bool); out = []
    for i in np.argsort(-m.area_faces):
        if seen[i]: continue
        idx = np.array(tree.query_ball_point(q[i], 1.2))
        idx = idx[~seen[idx]]
        if len(idx) < 10: continue
        P = q[idx]; mu = P.mean(0); _, s, vt = np.linalg.svd(P - mu); a = vt[0]
        # grow along the line
        for _ in range(3):
            d = q - mu; t = d @ a; perp = np.linalg.norm(d - np.outer(t, a), axis=1)
            sel = (perp < 0.25) & (np.abs(N @ a) < 0.15)
            if sel.sum() < 10: break
            P = q[sel]; mu = P.mean(0); _, s, vt = np.linalg.svd(P - mu); a = vt[0]
        if sel.sum() < 10: continue
        # verify radius of the member faces
        pts = m.triangles[sel].reshape(-1, 3); d = pts - mu; t = d @ a
        rad = np.linalg.norm(d - np.outer(t, a), axis=1)
        tt = (C[sel] - mu) @ a
        seen[sel] = True
        if abs(np.median(rad) - r) > tol or np.percentile(np.abs(rad - r), 90) > 0.12 or tt.max() - tt.min() < min_len - 0.6: continue
        # normals must wrap around the axis (a real bore, not a flat face)
        u = np.cross(a, [1, 0, 0] if abs(a[0]) < 0.9 else [0, 1, 0]); u /= np.linalg.norm(u); v = np.cross(a, u)
        ang = np.sort(np.arctan2(N[sel] @ v, N[sel] @ u)); gaps = np.diff(np.r_[ang, ang[0] + 2 * np.pi])
        if 2 * np.pi - gaps.max() < np.radians(200): continue
        mid = mu + a * (t.min() + t.max()) / 2
        if m.contains([mid])[0]: continue
        if a[np.argmax(np.abs(a))] < 0: a = -a
        aligned = np.max(np.abs(a)) > 0.995
        if skip_axis_aligned and aligned: continue
        if not aligned:
            try:
                from cylfit import fit
                P0f, af, rf, Lf, res = fit(m, mu, a, r0=r, L=8)
            except Exception: continue
            if abs(rf - r) > 0.05 or res > 0.08 or not (min_len - 0.6 < Lf < 9): continue
            if af[np.argmax(np.abs(af))] < 0: af = -af; P0f = P0f - af * Lf * 0  # keep start point
            mu, a, tt = P0f, af, np.array([0.0, Lf])
        b = dict(P0=mu + a * tt.min(), a=a, L=tt.max() - tt.min(), aligned=aligned)
        if not any(np.linalg.norm(np.cross(o['a'], b['P0'] - o['P0'])) < 0.5 and abs(o['a'] @ a) > 0.99 for o in out): out.append(b)
    return out
def specs_for(m, b, s_min=2.0, name='angled'):
    a = b['a']; p0 = b['P0']; p1 = p0 + a * b['L']
    def entry_face(pe, e):
        for s in np.arange(0.3, 12, 0.05):
            q = pe - e * s
            if annulus_out(m, q, e) > 0.7: return q, True
        return pe, False
    cands = []
    for pe, e in ((p0, a), (p1, -a)):
        F, ok = entry_face(pe, e)
        if ok: cands.append((np.dot(pe - F, e), F, e))
    cands.sort(key=lambda c: c[0])                    # prefer the end that opens straight to air
    skin, F, e = cands[0]; D = skin + b['L']
    s0 = max(s_min, skin) if skin < 0.5 else max(1.4, skin)
    r, _, _ = slot2d.scan(m, F, e, s0, t=2.0, ndir=72); best = None
    for x in sorted(r, key=lambda x: x['L']):
        if x['clean'] < 0.96 or x['wall'] < 0.85 or x['L'] > 9.0: continue
        sp = dict(name=name + ' nut slot', F=F.tolist(), e=e.tolist(), fill=(max(skin - 0.05, 0), D), s0=s0,
                  d=x['d'].tolist(), L=x['L'] + 1.2, extra=1.2)
        if approach(m, sp, ext=(8,))[0] >= 0.95: best = sp; break
    if best is None:
        d = np.cross(e, [1, 0, 0]) if abs(e[0]) < 0.9 else np.cross(e, [0, 1, 0])
        best = dict(name=name + ' pilot', kind='pilot', F=F.tolist(), e=e.tolist(), d=d.tolist(),
                    fill=(0, D - 0.2), depth=D + 1.0, r=1.35)
    return best
