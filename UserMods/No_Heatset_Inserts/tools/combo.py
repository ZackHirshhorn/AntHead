"""Per insert: captive square-nut slot if a clean one fits, otherwise a 2.7 mm self-tap pilot."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, trimesh
from holes import find
from auto import auto_specs
from pilot import pilot_specs
from convert import apply
def plan(m, cl, prefer=None, force_pilot=False, min_len=2.4):
    ins = [c for c in cl if 2.2 < np.mean(c['rs']) < 2.5 and c['h1'] - c['h0'] >= min_len]
    specs = []
    for i, c in enumerate(ins):
        if abs(np.mean(c['rs']) - 2.35) > 0.12:      # not an M3 insert bore (e.g. 5 mm counterbore)
            continue
        sp = None if force_pilot else auto_specs(m, [c], prefer=prefer, verbose=False, min_len=min_len)[0]
        if sp is None or sp.get('bad'):
            sp = pilot_specs(m, [c], lambda c: True, min_len=min_len)[0]
        sp['name'] = f"#{i} {'pilot' if sp.get('kind') == 'pilot' else 'nut slot'}"
        specs.append(sp)
    return specs
def convert(src, prefer=None, force_pilot=False):
    m, cl = find(src, rmin=2.0, rmax=2.6)
    specs = plan(m, cl, prefer, force_pilot)
    m1 = apply(m, specs)
    parts = [b for b in m1.split(only_watertight=False) if b.volume > 0.05]
    if len(parts) > 1:                      # sealed slivers / voids -> keep outer solid(s)
        m1 = trimesh.util.concatenate(parts)
    return m, m1, specs
