import numpy as np, trimesh
from shapely.geometry import Polygon, Point, box, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity
from sect import basis, section2d
W=5.75; T=2.1
def mat2d(m,F,e,s,u):
    pg=section2d(m,F+e*s,e,u)
    return unary_union(pg) if pg else Polygon()
def is_inside(m,p): return bool(m.contains([p])[0])
def entry(m,P,a,h0,h1):
    a=np.asarray(a,float); base=P-a*np.dot(P,a)
    p0=base+a*h0; p1=base+a*h1
    o0=not is_inside(m,p0-a*0.8); o1=not is_inside(m,p1+a*0.8)
    return p0,p1,o0,o1
def slot_poly(th,L,w=W):
    r=box(-w/2,-w/2,L,w/2)  # along +x in local, includes nut square
    return affinity.rotate(r,th,origin=(0,0),use_radians=True)
def scan(m,F,e,s0,t=T,ndir=36,maxL=25,hole_r=2.45):
    e=np.asarray(e,float); _,u,v=basis(e)
    secs=[mat2d(m,F,e,s,u) for s in (s0+0.1,s0+t/2,s0+t-0.1)]
    hole=Point(0,0).buffer(hole_r)
    res=[]
    for k in range(ndir):
        th=2*np.pi*k/ndir
        best=None
        for L in np.arange(W/2,maxL,0.25):
            tip=affinity.rotate(box(L-0.25,-W/2,L,W/2),th,origin=(0,0),use_radians=True)
            if all(sec.intersection(tip).area<1e-3 for sec in secs): best=L; break
        if best is None: continue
        sl=slot_poly(th,best-0.5)
        clean=min((sec.union(hole)).intersection(sl).area/sl.area for sec in secs)
        # side wall: material within 1.0mm on each side of slot, along its length up to best-1.5
        Lw=max(best-1.5,W/2)
        sides=[affinity.rotate(box(-W/2,W/2,Lw,W/2+0.9),th,origin=(0,0),use_radians=True),
               affinity.rotate(box(-W/2,-W/2-0.9,Lw,-W/2),th,origin=(0,0),use_radians=True),
               affinity.rotate(box(-W/2-0.9,-W/2,-W/2,W/2),th,origin=(0,0),use_radians=True)]
        wall=min(min(sec.intersection(sd).area/sd.area for sd in sides) for sec in secs)
        d=np.cos(th)*u+np.sin(th)*v
        res.append(dict(k=k,th=th,d=d,L=best,clean=clean,wall=wall))
    return res,secs,(u,v)
def plot(ax,secs,th,L,title=''):
    from shapely.plotting import plot_polygon
    for sec in secs[1:2]:
        if not sec.is_empty: plot_polygon(sec,ax=ax,add_points=False,facecolor='#9ab',edgecolor='k',linewidth=0.5)
    plot_polygon(slot_poly(th,L),ax=ax,add_points=False,facecolor=(1,0,0,0.35),edgecolor='r',linewidth=0.8)
    plot_polygon(Point(0,0).buffer(1.7),ax=ax,add_points=False,facecolor='w',edgecolor='b',linewidth=0.5)
    ax.set_xlim(-14,14); ax.set_ylim(-14,14); ax.set_aspect('equal'); ax.set_title(title,fontsize=8); ax.grid(alpha=.3)
