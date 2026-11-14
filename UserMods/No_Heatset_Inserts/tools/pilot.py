import sys; sys.path.insert(0,sys.path[0])
import numpy as np
from holes import find
from auto import annulus_out
from convert import apply, verify
def pilot_specs(m,cl,select,depth_extra=1.0,r=1.35,min_len=2.4):
    lo,hi=m.bounds; out=[]
    ins=[c for c in cl if 2.2<np.mean(c['rs'])<2.5 and c['h1']-c['h0']>=min_len]
    for i,c in enumerate(ins):
        if not select(c): continue
        ax=c['ax']; a=np.zeros(3); a[ax]=1; base=c['P']-a*c['P'][ax]
        p0=base+a*c['h0']; p1=base+a*c['h1']
        use_p0=(c['h0']-lo[ax])<(hi[ax]-c['h1'])
        pe,e=(p0,a.copy()) if use_p0 else (p1,-a)
        F=pe.copy()
        for s in np.arange(0.3,12,0.05):
            q=pe-e*s
            if annulus_out(m,q,e)>0.7: F=q; break
        D=np.dot(pe-F,e)+c['h1']-c['h0']
        d=np.cross(e,[1,0,0]) if abs(e[0])<0.9 else np.cross(e,[0,1,0])
        out.append(dict(name=f"#{i} {'xyz'[ax]} pilot",kind='pilot',F=F.tolist(),e=e.tolist(),d=d.tolist(),fill=(0,D-0.2),depth=D+depth_extra,r=r))
        print(f"  #{i} pilot F={np.round(F,2)} e={e} depth={D:.2f}")
    return out
