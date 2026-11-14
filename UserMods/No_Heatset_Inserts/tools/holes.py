import sys, numpy as np, trimesh
from collections import defaultdict
def circfit(p):
    A=np.c_[2*p,np.ones(len(p))]; b=(p**2).sum(1)
    c,*_=np.linalg.lstsq(A,b,rcond=None); r=np.sqrt(c[2]+c[0]**2+c[1]**2)
    res=np.abs(np.linalg.norm(p-c[:2],axis=1)-r).max()
    return c[:2],r,res
def find(path,rmin=0.7,rmax=3.5,step=0.25):
    m=trimesh.load(path); out=[]
    lo,hi=m.bounds
    for ax in range(3):
        n=np.zeros(3);n[ax]=1
        hs=np.arange(lo[ax]+0.05,hi[ax],step)
        secs=m.section_multiplane(plane_origin=np.zeros(3),plane_normal=n,heights=hs)
        for h,s in zip(hs,secs):
            if s is None: continue
            for poly in s.polygons_full:
                for ring in poly.interiors:
                    p=np.array(ring.coords)[:-1]
                    if len(p)<8: continue
                    c,r,res=circfit(p)
                    if rmin<r<rmax and res<0.08:
                        # convert 2D to 3D: section to_3D transform
                        P=trimesh.transform_points(np.array([[c[0],c[1],0]]),s.metadata['to_3D'])[0]
                        out.append((ax,h,P,r))
    # cluster
    cl=[]
    for ax,h,P,r in out:
        o=[i for i in range(3) if i!=ax]
        for c in cl:
            if c['ax']==ax and np.linalg.norm(c['P'][o]-P[o])<0.3 and abs(c['r']-r)<0.15 and h-c['h1']<=step*1.5:
                c['h1']=h; c['rs'].append(r); break
        else: cl.append(dict(ax=ax,P=P,h0=h,h1=h,r=r,rs=[r]))
    return m,cl
if __name__=='__main__':
    for f in sys.argv[1:]:
        m,cl=find(f)
        print('==',f, 'bounds',np.round(m.bounds,2).tolist())
        for c in sorted(cl,key=lambda c:(c['ax'],-np.mean(c['rs']))):
            d=2*np.mean(c['rs'])
            if c['h1']-c['h0']<0.4: continue
            o=[i for i in range(3) if i!=c['ax']]
            print(f"  axis {'xyz'[c['ax']]} dia {d:5.2f} at {np.round(c['P'][o],2)} span {c['h0']:.2f}..{c['h1']:.2f}")
