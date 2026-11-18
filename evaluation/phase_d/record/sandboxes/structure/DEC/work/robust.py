import sys, os, json, importlib.util
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, "pkg"))
import numpy as np
for cid in ["D-012","D-016","D-021","D-030","D-046","D-047","D-052","D-069"]:
    note = json.load(open(os.path.join(root,"cases",cid,"NOTE.json")))
    ss=note["structure_statistic"]; ns={"np":np}; exec(ss["code"],ns); stat=ns["stat"]
    spec = importlib.util.spec_from_file_location("r"+cid[2:], os.path.join(root,"cases",cid,"reference.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    av=note["approved_value"]; tol=0.2*abs(av-ss["null_value"])
    fails=0; trials=30
    for t in range(trials):
        r={}
        for w in ("plus","minus"):
            rng=np.random.default_rng(90000+t*1000+(0 if w=="plus" else 77))
            r[w]=np.array([stat(getattr(m,w)(rng)) for _ in range(200)])
        ok = abs(r["plus"].mean()-av)<=tol and abs(r["minus"].mean()-av)<=tol and abs(r["plus"].mean()-r["minus"].mean())<=3*np.sqrt(r["plus"].var(ddof=1)/200+r["minus"].var(ddof=1)/200)
        fails += (not ok)
        if not ok: print("  ", cid, t, round(r["plus"].mean(),4), round(r["minus"].mean(),4), round(3*np.sqrt(r["plus"].var(ddof=1)/200+r["minus"].var(ddof=1)/200),4))
    print(cid, "fail", fails, "/", trials)
