"""3010 hotend-fan variants: widen the No Logo main body fan pocket and move the hotend-mount fan holes to 24 mm spacing."""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, trimesh, manifold3d as mf
from holes import find
from pilot import pilot_specs
from convert import apply, to_mf, to_tm
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..')); OUT = os.path.abspath(os.path.join(HERE, '..', 'STLs'))
def box(x0, x1, y0, y1, z0, z1): return mf.Manifold.cube((x1-x0, y1-y0, z1-z0)).translate((x0, y0, z0))

def main_body_no_logo():
    src = os.path.join(OUT, 'Main_Bodies/O2/No_Logo/ant_head_main_body_no_logo_o2_sf_x1.stl')   # already insert-free
    m = trimesh.load(src); cx = (m.bounds[0][0] + m.bounds[1][0]) / 2
    # stock fan pocket is 29.4 wide (x), y 168.9..202.9, fan sits 5.7..15.7 mm behind the front face (z)
    M = to_mf(m) - box(cx-15.3, cx+15.3, 171.2, 202.4, 4.2, 16.4)
    # The channel behind the pocket is only 27 mm wide (it locates the hotend mount), so a 3010 can't
    # ride in from the back. Instead it goes in through the front before the grill: widen the front
    # opening over the fan's height only. Top lip and the side-lip stubs above/below still hold the grill.
    M = M - box(cx-15.3, cx+15.3, 171.2, 202.4, -1.0, 4.3)
    m1 = to_tm(M); print('  main body removed', round(m.volume - m1.volume, 1), 'mm3')
    return m1

def hotend(src, yc):
    m, cl = find(os.path.join(ROOT, src), rmin=2.0, rmax=2.6)
    sp = pilot_specs(m, cl, lambda c: abs(np.mean(c['rs']) - 2.35) < 0.08)
    side = [s for s in sp if abs(s['e'][2]) < 0.5]                                # main-body screws -> pilots
    fill = [dict(s, r=1e-4, depth=0, fill=(0, s['fill'][1] + 0.5)) for s in sp if abs(s['e'][2]) > 0.5]  # old 2510 inserts -> solid
    M = to_mf(apply(m, side + fill))
    X = -210.89; top = 24.4
    for dy in (-12, 12):
        y = yc + dy
        boss = mf.Manifold.cylinder(4.8, 2.9, 2.9, 48).translate((X, y, top - 4.8))
        lim = box(X-4, X+4, yc-14.3, yc+14.3, top-4.8, top)          # stay inside the main-body pocket
        M = M + (boss ^ lim)
        M = M - mf.Manifold.cylinder(4.8+2, 1.35, 1.35, 32).translate((X, y, top - 4.8))
    t = to_tm(M)
    # tiny sealed slivers left at the bottom of the old insert bores: fill them (keep only the outer shell)
    parts = [b for b in t.split(only_watertight=False) if b.volume > 0]
    return trimesh.util.concatenate(parts)

if __name__ == '__main__':
    jobs = [('Main_Bodies/O2/No_Logo/ant_head_main_body_no_logo_o2_sf_3010fan_x1.stl', main_body_no_logo()),
            ('Hotends/[a]_dragon_3010fan_x1.stl', hotend('STLs/Hotends/[a]_dragon_x1.stl', 24.85)),
            ('Hotends/[a]_tzv6_v6nozzle_3010fan_x1.stl', hotend('STLs/Hotends/[a]_tzv6_v6nozzle_x1.stl', 154.9))]
    for rel, m1 in jobs:
        assert m1.is_watertight and len(m1.split(only_watertight=False)) == 1, rel
        m1.export(os.path.join(OUT, rel)); print('  wrote', rel)
