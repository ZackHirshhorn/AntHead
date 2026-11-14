"""
Regenerates every STL in ../STLs from the stock AntHead STLs in the repository,
replacing heat-set inserts with captive M3 square-nut slots (or self-tapping
pilot holes where the wall is too thin for a nut).

    pip install numpy trimesh manifold3d shapely scipy rtree matplotlib
    python3 UserMods/No_Heatset_Inserts/tools/generate.py      (run from repo root)

Pass --check to also write before/after cross-section images to ../checks/.
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import numpy as np, trimesh
from holes import find
from auto import auto_specs, annulus_out
from pilot import pilot_specs
from convert import apply, verify
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
OUT = os.path.abspath(os.path.join(HERE, '..', 'STLs'))
CHECK = '--check' in sys.argv
is_m3_insert = lambda c: abs(np.mean(c['rs']) - 2.35) < 0.08      # 4.7 mm bores only

def save(src, rel_out, m0, m1, specs):
    assert m1.is_watertight and len(m1.split(only_watertight=False)) == 1, rel_out
    dst = os.path.join(OUT, rel_out); os.makedirs(os.path.dirname(dst), exist_ok=True)
    m1.export(dst)
    if CHECK:
        img = os.path.join(HERE, '..', 'checks', os.path.basename(rel_out)[:-4] + '.png')
        os.makedirs(os.path.dirname(img), exist_ok=True); verify(m0, m1, specs, img)
    print(f'  wrote {rel_out}')

def slots(src, rel_out, prefer=None):
    m, cl = find(os.path.join(ROOT, src), rmin=2.0, rmax=2.6)
    specs = auto_specs(m, cl, prefer=prefer, verbose=False)
    assert not any(s.get('bad') for s in specs), src
    save(src, rel_out, m, apply(m, specs), specs)

def pilots(src, rel_out):
    m, cl = find(os.path.join(ROOT, src), rmin=2.0, rmax=2.6)
    specs = pilot_specs(m, cl, is_m3_insert)
    save(src, rel_out, m, apply(m, specs), specs)

def manual(src, rel_out, specs):
    m = trimesh.load(os.path.join(ROOT, src))
    save(src, rel_out, m, apply(m, specs), specs)

if __name__ == '__main__':
    # --- Main bodies (O2 bolt pattern = BMG / G2 extruders), standard-flow length
    for logo, stem in [('Micron', 'micron'), ('No_Logo', 'no_logo'), ('SaladFork', 'saladfork'),
                       ('StealthFork', 'stealth_fork'), ('Voron', 'voron')]:
        f = f'ant_head_main_body_{stem}_o2_sf_x1.stl'
        slots(f'STLs/Main_Bodies/O2/{logo}/{f}', f'Main_Bodies/O2/{logo}/{f}', prefer=(0, 0, 1))
    # --- Part-cooling ducts (standard flow)
    for f in ['[a]_left_duct_x1.stl', '[a]_right_duct_x1.stl', '[a]_left_duct_hb92_x1.stl', '[a]_right_duct_hb92_x1.stl']:
        slots(f'STLs/Ducts/SF/{f}', f'Ducts/SF/{f}')
    # --- Hotend mounts: walls too thin for a nut -> 2.7 mm pilot holes for M3 screws
    for f in ['[a]_tzv6_v6nozzle_x1.stl', '[a]_tzv6_v6nozzle_m2.5_x1.stl', '[a]_dragon_x1.stl', '[a]_dragon_m2.5_x1.stl']:
        pilots(f'STLs/Hotends/{f}', f'Hotends/{f}')
    # --- BMG extruder
    manual('STLs/Extruders/BMG/[a]_motor_plate_x1.stl', 'Extruders/BMG/[a]_motor_plate_x1.stl',
           [dict(name='motor plate', F=(84.97, 66.24, 172.5), e=(0, 0, -1), s0=1.2,
                 d=(-0.7071, -0.7071, 0), L=4.55, fill=(3.0, 7.25), hole_end=9)])
    manual('STLs/Extruders/BMG/tensioner_arm_b_x1.stl', 'Extruders/BMG/tensioner_arm_b_x1.stl',
           [dict(name='arm B', F=(99.2, 87.8, 0.0), e=(0, 0, 1), s0=4.8,
                 d=(0.342, 0.940, 0), L=6.05, fill=(0, 4.8), hole_end=8)])
    a = np.array([0.93969262, 0.34202014, 0.]); P0 = np.array([88.32801, 22.78350, 14.89983])
    F = np.array([88.05, 22.68, 14.9]); D = float(np.dot(P0 - F, a)) + 5.0
    manual('STLs/Extruders/BMG/extruder_main_body_x1.stl', 'Extruders/BMG/extruder_main_body_x1.stl',
           [dict(name='tension screw', F=F.tolist(), e=a.tolist(), s0=1.8, d=[0.342, -0.940, 0],
                 L=6.3, fill=(0, D - 0.1), hole_end=D + 0.5)])
    pilots('STLs/Extruders/BMG/BoardMounts/toolhead_board_mount_anthead_bmg_micron.stl',
           'Extruders/BMG/BoardMounts/toolhead_board_mount_anthead_bmg_micron.stl')
