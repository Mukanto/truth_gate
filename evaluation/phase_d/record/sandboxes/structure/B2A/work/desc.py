import sys, os, glob, importlib.util
sys.path.insert(0, os.path.abspath('pkg'))
import numpy as np
for cid in ['D-004','D-005','D-010','D-014','D-022','D-027','D-039','D-044','D-055','D-060','D-029','D-042']:
    p=f'cases/{cid}/reference.py'
    spec=importlib.util.spec_from_file_location('r'+cid.replace('-','_'),p); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    out=[]
    for w in ('plus','minus'):
        v=[];ac=[]
        for i in range(60):
            d=getattr(m,w)(np.random.default_rng(i)); y=d['y'].astype(float)
            v.append(y.var())
            if y.ndim==1 and cid in('D-039','D-055'):
                yy=y-y.mean(); ac.append((yy[1:]*yy[:-1]).sum()/(yy**2).sum())
            if cid=='D-004':
                yy=y-y.mean(); ac.append((yy[:,1:]*yy[:,:-1]).sum()/(yy**2).sum())
        out.append('%s var=%.3f%s'%(w,np.mean(v),(' ac=%.3f'%np.mean(ac)) if ac else ''))
    print(cid,' | '.join(out))
