import sys; sys.path.insert(0,sys.path[0])
import numpy as np, trimesh
from holes import find
from slot2d import scan
from run_part import approach
from convert import apply, verify, NUT_T
from sect import basis
def annulus_out(m,p,e,r=2.05,n=12):
    _,u,v=basis(e); a=np.linspace(0,2*np.pi,n,endpoint=False)
    pts=p+np.outer(np.cos(a),u)*r+np.outer(np.sin(a),v)*r
    return 1-m.contains(pts).mean()
def auto_specs(m,cl,entry_rule='near_bound',prefer=None,s_min=2.0,only=None,verbose=True,min_len=2.4):
    lo,hi=m.bounds; specs=[]
    ins=[c for c in cl if 2.2<np.mean(c['rs'])<2.5 and c['h1']-c['h0']>=min_len]
    for i,c in enumerate(ins):
        if only is not None and i not in only: continue
        ax=c['ax']; a=np.zeros(3); a[ax]=1; base=c['P']-a*c['P'][ax]
        p0=base+a*c['h0']; p1=base+a*c['h1']
        if callable(entry_rule): use_p0=entry_rule(c,m)
        else: use_p0=(c['h0']-lo[ax])<(hi[ax]-c['h1'])
        pe,e=(p0,a.copy()) if use_p0 else (p1,-a)
        # walk outward to the real face
        F=pe.copy()
        for s in np.arange(0.3,12,0.05):
            q=pe-e*s
            if annulus_out(m,q,e)>0.7: F=q; break
        skin=np.dot(pe-F,e); D=skin+(c['h1']-c['h0'])
        s0=max(s_min,skin) if skin<0.5 else max(1.4,skin)
        sp=dict(name=f"#{i} {'xyz'[ax]}",F=F.tolist(),e=e.tolist(),fill=(max(skin-0.05,0),D),s0=round(float(s0),2))
        r,_,_=scan(m,F,e,s0,t=NUT_T,ndir=72)
        cands=[]
        for x in r:
            if x['clean']<0.96 or x['wall']<0.85 or x['L']>9.0: continue
            sp2=dict(sp,d=x['d'].tolist(),L=x['L']+1.2,extra=1.2)
            ap=min(approach(m,sp2,ext=(8,)))
            if ap<0.95: continue
            pen=x['L']-(0.6 if (prefer is not None and np.dot(x['d'],prefer)>0.3) else 0)
            cands.append((pen,x,ap))
        if not cands:
            print('  !! no good slot for',sp['name'],np.round(F,2)); sp['bad']=True; specs.append(sp); continue
        cands.sort(key=lambda t:t[0]); _,x,ap=cands[0]
        sp.update(d=x['d'].tolist(),L=float(x['L'])+1.2,extra=1.2)
        if verbose: print(f"  {sp['name']} F={np.round(F,2)} e={np.round(e,0)} skin={skin:.2f} depth={D:.2f} s0={s0:.2f} d={np.round(x['d'],2)} exit={x['L']:.2f} wall={x['wall']:.2f}")
        specs.append(sp)
    return specs
def process(src,dst,img,prefer=None,entry_rule='near_bound',only=None,extra_specs=()):
    m,cl=find(src,rmin=2.0,rmax=2.6)
    specs=auto_specs(m,cl,entry_rule,prefer,only=only)+list(extra_specs)
    if any(s.get('bad') for s in specs): return None
    m1=apply(m,specs)
    print('  ->',dst.split('/')[-1],'watertight',m1.is_watertight,'bodies',len(m1.split(only_watertight=False)),'dV',round(m1.volume-m.volume,1))
    verify(m,m1,specs,img); m1.export(dst); return specs
