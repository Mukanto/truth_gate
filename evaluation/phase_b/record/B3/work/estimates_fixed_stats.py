"""Descriptive means/SDs of the FIXED statistics on plus/minus samples (supports the explanations in CASE.md). Never touches faulty.py."""
import importlib.util, sys
import numpy as np
sys.path.insert(0, r"E:\Claude Projects\kapi-oss")
ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B3\cases"
def load(c):
    sp = importlib.util.spec_from_file_location("m_"+c.replace("-","_"), ROOT + "/" + c + "/fixed.py"); m = importlib.util.module_from_spec(sp); sp.loader.exec_module(m); return m
def rk(x):
    u, inv, cnt = np.unique(x, return_inverse=True, return_counts=True); return (np.cumsum(cnt)-(cnt-1)/2.0)[inv]
def pc(a,b,c):
    rab=np.corrcoef(a,b)[0,1]; rac=np.corrcoef(a,c)[0,1]; rbc=np.corrcoef(b,c)[0,1]
    return (rab-rac*rbc)/np.sqrt((1-rac**2)*(1-rbc**2))
def z(x): return (x-x.mean())/x.std()
def stat(c, d):
    if c=="B3-05": return pc(d["femur_length"],d["tibia_length"],d["vertebral_column_length"])
    if c=="B3-07":
        X=np.column_stack([np.ones(len(d["yield_total"])),z(d["fertilizer_total"]),z(d["farm_area"])]); return np.linalg.lstsq(X,z(d["yield_total"]),rcond=None)[0][1]
    if c=="B3-08": return pc(d["vo2max"],d["peak_power"],d["body_mass"])**2
    if c=="B3-09":
        X=np.column_stack([np.ones(len(d["beds"])),z(d["beds"]),z(d["admissions"])]); return np.linalg.lstsq(X,z(d["infections"]),rcond=None)[0][1]
    if c=="B3-11": return pc(rk(d["occupants"]),rk(d["energy_use"]),rk(d["floor_area"]))
    if c=="B3-12": return pc(d["leavers"],d["payroll"],d["headcount"])**2
for c in ["B3-05","B3-07","B3-08","B3-09","B3-11","B3-12"]:
    m=load(c)
    for w in ("plus","minus"):
        v=np.array([stat(c,getattr(m,w)(np.random.default_rng(31000+i))) for i in range(400)])
        print(c,w,f"mean {v.mean():.3f} sd {v.std():.3f}")
