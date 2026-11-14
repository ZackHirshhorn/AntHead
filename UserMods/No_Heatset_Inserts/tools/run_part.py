import sys, json; sys.path.insert(0,sys.path[0])
import numpy as np, trimesh
from slot2d import scan
from convert import apply, verify, NUT_T
import slot2d; slot2d.W=5.7; slot2d.T=NUT_T
def plan(m,specs,verbose=True):
    for sp in specs:
        if 'L' in sp: continue
        r,_,_=scan(m,np.array(sp['F'],float),np.array(sp['e'],float),sp['s0'],t=NUT_T,ndir=72)
        want=np.asarray(sp['d'],float)
        # choose scan dir closest to requested d
        best=max(r,key=lambda x:np.dot(x['d'],want)/np.linalg.norm(want))
        sp['d']=best['d'].tolist(); sp['L']=best['L']+sp.get('extra',1.2)
        if verbose: print(f"  {sp['name']}: d={np.round(best['d'],2)} exitL={best['L']:.2f} clean={best['clean']:.2f} wall={best['wall']:.2f}")
    return specs
def run(src,dst,specs,img):
    m=trimesh.load(src); specs=plan(m,specs)
    m1=apply(m,specs)
    print('  watertight',m1.is_watertight,'volume',round(m.volume,1),'->',round(m1.volume,1),'bodies',len(m1.split(only_watertight=False)))
    verify(m,m1,specs,img)
    m1.export(dst); return specs
from slot2d import mat2d
from shapely.geometry import box as sbox
from shapely import affinity
from sect import basis
def approach(m,sp,ext=(4,8,12)):
    F=np.array(sp['F'],float); e=np.array(sp['e'],float); e/=np.linalg.norm(e); _,u,v=basis(e)
    d=np.array(sp['d']); th=np.arctan2(d@v,d@u); L0=sp['L']-sp.get('extra',1.2)
    out=[]
    for X in ext:
        fr=[]
        for s in (sp['s0']+0.1,sp['s0']+NUT_T/2,sp['s0']+NUT_T-0.1):
            sec=mat2d(m,F,e,s,u); b=affinity.rotate(sbox(L0,-2.75,L0+X,2.75),th,origin=(0,0),use_radians=True)
            fr.append(1-sec.intersection(b).area/b.area)
        out.append(round(min(fr),2))
    return out
