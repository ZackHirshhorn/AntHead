import numpy as np, trimesh, matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from shapely.plotting import plot_polygon
def basis(a):
    a=np.asarray(a,float); a/=np.linalg.norm(a)
    t=np.array([1,0,0]) if abs(a[0])<0.9 else np.array([0,1,0])
    u=np.cross(a,t); u/=np.linalg.norm(u); v=np.cross(a,u); return a,u,v
def section2d(m,origin,normal,xdir):
    s=m.section(plane_origin=origin,plane_normal=normal)
    if s is None: return []
    n=np.asarray(normal,float); n/=np.linalg.norm(n); x=np.asarray(xdir,float); y=np.cross(n,x)
    T=np.eye(4); T[:3,0]=x; T[:3,1]=y; T[:3,2]=n; T[:3,3]=origin
    p2,_=s.to_2D(to_2D=np.linalg.inv(T))
    return p2.polygons_full
def show(m,holes,out,win=12,labels=None):
    """holes: list of (P, axis). For each: 3 panels: two axial sections + perpendicular section at P."""
    n=len(holes); fig,axs=plt.subplots(n,3,figsize=(12,4*n),squeeze=False)
    for i,(P,a) in enumerate(holes):
        a,u,v=basis(a)
        for j,(nrm,xd,ttl) in enumerate([(u,a,'axial(x=axis) plane⊥u'),(v,a,'axial(x=axis) plane⊥v'),(a,u,'perp (x=u,y=v)')]):
            ax=axs[i,j]
            for pg in section2d(m,P,nrm,xd):
                plot_polygon(pg,ax=ax,add_points=False,facecolor='#9ab',edgecolor='k',linewidth=0.5)
            ax.plot(0,0,'r+',ms=12)
            if j<2: ax.axhline(0,color='r',lw=0.5)
            ax.set_xlim(-win,win); ax.set_ylim(-win,win); ax.set_aspect('equal'); ax.grid(alpha=0.3)
            ax.set_title(f"{labels[i] if labels else i}: {ttl}",fontsize=8)
    plt.tight_layout(); plt.savefig(out,dpi=60); plt.close()
    return [basis(a) for P,a in holes]
