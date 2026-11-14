"""
Converts every remaining stock STL that has M3 heat-set inserts (everything not
already produced by generate.py): HF/UHF and Sherpa main bodies, HF/UHF ducts,
the other hotend mounts, 2020 carriage + probe mounts, board mounts and the G2
extruder parts.

Per insert: a captive M3 square-nut slot when a clean one fits (exits to open
air within 9 mm, walls >= ~0.8 mm), otherwise a 2.7 mm self-tap pilot hole.
Angled inserts (2020 carriages, G2 front body) are found by angled.bores().

    python3 UserMods/No_Heatset_Inserts/tools/generate_rest.py   (from repo root)
"""
import os, sys, glob
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, trimesh
import convert
from convert import apply, to_mf
from combo import plan
from holes import find
from angled import bores, specs_for
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..')); OUT = os.path.abspath(os.path.join(HERE, '..', 'STLs'))

def finish(m0, m1, rel, specs):
    # keep internal voids that the stock part already had; drop new slivers/voids from the booleans
    stock_voids = sorted(round(b.volume, 1) for b in m0.split(only_watertight=False) if b.volume < 0)
    parts = []
    for b in m1.split(only_watertight=False):
        v = round(b.volume, 1)
        if v > 0.05 or (v < 0 and any(abs(v - s) < 0.3 for s in stock_voids)): parts.append(b)
    m1 = trimesh.util.concatenate(parts)
    assert m1.is_watertight and len(parts) == len(m0.split(only_watertight=False)), rel
    dst = os.path.join(OUT, rel); os.makedirs(os.path.dirname(dst), exist_ok=True); m1.export(dst)
    print(f"  {rel}: " + ', '.join(s['name'] for s in specs))

def mirrored(m, b):
    cx = (m.bounds[0][0] + m.bounds[1][0]) / 2; P = b['P0'].copy(); P[0] = 2 * cx - P[0]
    a = b['a'].copy(); a[0] = -a[0]; return dict(P0=P, a=a, L=b['L'], aligned=False)

def convert_file(rel):
    src = os.path.join(ROOT, 'STLs', rel)
    m, cl = find(src, rmin=2.0, rmax=2.6)
    specs = plan(m, cl, prefer=(0, 0, 1), min_len=2.0 if 'rapido_x' in rel else 2.4)   # Rapido_X inserts are shallower
    if 'G2/[a]_front_body' in rel:
        # tension-screw insert sits at the bottom of a deeper bore (room for the spring): nut there, bore left open
        F = [315.19, 184.52, 24.63]; e = [0.9397, 0.342, 0.]
        specs.append(dict(name='angled tension nut slot', F=F, e=e, s0=4.27, d=[0.342, -0.940, 0], L=7.3, hole_end=9.87))
    elif 'mgn' in rel:
        bs = bores(m)
        if len(bs) == 1: bs.append(mirrored(m, bs[0]))          # second 45 deg bore is the mirror image
        specs += [specs_for(m, b, name=f'angled#{i}') for i, b in enumerate(bs)]
    if not specs: return
    finish(m, apply(m, specs), rel, specs)

DONE = {os.path.relpath(p, OUT) for p in glob.glob(os.path.join(OUT, '**', '*.stl'), recursive=True)}
if __name__ == '__main__':
    todo = []
    for pat in ['Main_Bodies/*/*/*.stl', 'Ducts/HF/*.stl', 'Ducts/UHF/*.stl', 'Hotends/*.stl', '2020_Carriage/*.stl',
                '2020_Carriage/*/*.stl', 'Extruders/BMG/*.stl', 'Extruders/BMG/BoardMounts/*.stl',
                'Extruders/G2/*.stl', 'Extruders/G2/Board Mounts/*.stl']:
        for p in sorted(glob.glob(os.path.join(ROOT, 'STLs', pat))):
            rel = os.path.relpath(p, os.path.join(ROOT, 'STLs'))
            if rel in DONE or rel in todo: continue
            todo.append(rel)
    for rel in todo: convert_file(rel)
