import sys; sys.path.insert(0,sys.path[0])
import numpy as np, trimesh, manifold3d as mf
from sect import basis, section2d
import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
NUT_W=5.7; NUT_T=2.0; CLR_R=1.7; FILL_R=2.42
def to_mf(m): return mf.Manifold(mf.Mesh(vert_properties=np.asarray(m.vertices,np.float32),tri_verts=np.asarray(m.faces,np.uint32)))
def to_tm(M):
    g=M.to_mesh(); t=trimesh.Trimesh(g.vert_properties[:,:3],g.tri_verts,process=True)
    bs=t.split(only_watertight=False)
    if len(bs)>1:
        keep=[b for b in bs if abs(b.volume)>0.05]
        drop=[b for b in bs if abs(b.volume)<=0.05]
        if drop: print('   (dropped',len(drop),'degenerate slivers)')
        if any(b.volume<0 for b in keep): print('   !! enclosed void(s):',[round(b.volume,2) for b in keep if b.volume<0])
        t=trimesh.util.concatenate(keep)
    return t
def frame(origin,e,d):
    e=np.asarray(e,float); e/=np.linalg.norm(e); d=np.asarray(d,float); d=d-e*np.dot(d,e); d/=np.linalg.norm(d); w=np.cross(e,d)
    T=np.eye(4); T[:3,0]=d; T[:3,1]=w; T[:3,2]=e; T[:3,3]=origin; return T
def xf(M,T): return M.transform(T[:3,:].astype(np.float64))
def cyl(r,z0,z1,T,n=48):
    c=mf.Manifold.cylinder(z1-z0,r,r,n).translate((0,0,z0)); return xf(c,T)
def boxm(x0,x1,y0,y1,z0,z1,T):
    b=mf.Manifold.cube((x1-x0,y1-y0,z1-z0)).translate((x0,y0,z0)); return xf(b,T)
def apply(m,specs):
    M=to_mf(m)
    for sp in specs:
        F=np.asarray(sp['F'],float); e=np.asarray(sp['e'],float); e/=np.linalg.norm(e)
        T=frame(F,e,sp['d'])
        # fill old insert bore
        if sp.get('fill'):
            f0,f1=sp['fill']; M=M+cyl(FILL_R,f0,f1,T)
        if sp.get('kind')=='pilot':
            M=M-cyl(sp.get('r',1.35),-2.0,sp['depth'],T); continue
        s0=sp['s0']; t=sp.get('t',NUT_T); L=sp['L']
        hole_end=sp.get('hole_end',max(s0+t+2.5,(sp['fill'][1]+0.6) if sp.get('fill') else 0))
        M=M-cyl(CLR_R,-2.0,hole_end,T)
        if sp.get('kind','slot')=='slot':
            M=M-boxm(-NUT_W/2,L,-NUT_W/2,NUT_W/2,s0,s0+t,T)
        elif sp['kind']=='pocket':   # axial pocket opening at s0 going to s0+depth backwards toward exit
            M=M-boxm(-NUT_W/2,NUT_W/2,-NUT_W/2,NUT_W/2,s0,L,T)
    return to_tm(M)
def verify(m0,m1,specs,out,win=13):
    n=len(specs); fig,axs=plt.subplots(n,4,figsize=(16,4*n),squeeze=False)
    for i,sp in enumerate(specs):
        F=np.asarray(sp['F'],float); e=np.asarray(sp['e'],float); e/=np.linalg.norm(e)
        T=frame(F,e,sp['d']); d=T[:3,0]; w=T[:3,1]; s0=sp.get('s0',1.0); t=sp.get('t',NUT_T)
        cfg=[(m0,F+e*(s0+t/2),e,d,'BEFORE perp @nut (x=d,y=w)'),(m1,F+e*(s0+t/2),e,d,'AFTER perp @nut (x=d,y=w)'),
             (m1,F,w,e,'AFTER axial (x=e,y=d)'),(m1,F,d,e,'AFTER axial (x=e,y=-w)')]
        for j,(mm,o,nrm,xd,tt) in enumerate(cfg):
            ax=axs[i,j]
            for pg in section2d(mm,o,nrm,xd): plot_polygon(pg,ax=ax,add_points=False,facecolor='#9ab',edgecolor='k',linewidth=0.5)
            ax.plot(0,0,'r+',ms=10); ax.set_xlim(-win,win); ax.set_ylim(-win,win); ax.set_aspect('equal'); ax.grid(alpha=.3)
            ax.set_title(f"{sp.get('name',i)}: {tt}",fontsize=8)
    plt.tight_layout(); plt.savefig(out,dpi=55); plt.close()
