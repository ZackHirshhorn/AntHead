import numpy as np, trimesh
from scipy.optimize import least_squares
def fit(m,P,a,r0=2.35,band=0.6,L=15):
    P=np.asarray(P,float); a=np.asarray(a,float); a/=np.linalg.norm(a)
    for it in range(4):
        V=m.triangles_center; N=m.face_normals
        d=V-P; t=d@a; rad=np.linalg.norm(d-np.outer(t,a),axis=1)
        sel=(np.abs(rad-r0)<band)&(np.abs(t)<L)&(np.abs(N@a)<0.3)
        pts=np.r_[m.triangles[sel].reshape(-1,3)]
        def res(x):
            p=x[:3]; ax=x[3:6]/np.linalg.norm(x[3:6]); r=x[6]
            dd=pts-p; tt=dd@ax; return np.linalg.norm(dd-np.outer(tt,ax),axis=1)-r
        x=least_squares(res,np.r_[P,a,r0]).x
        P=x[:3]; a=x[3:6]/np.linalg.norm(x[3:6]); r0=x[6]; band=0.3
    dd=pts-P; tt=dd@a
    return P+a*tt.min(), a, r0, tt.max()-tt.min(), np.abs(res(x)).max()
