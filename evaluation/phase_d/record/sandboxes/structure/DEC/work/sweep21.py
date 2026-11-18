import sys, os, json, importlib.util
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(root, "pkg"))
import numpy as np
note = json.load(open(os.path.join(root,"cases","D-021","NOTE.json")))
ns={"np":np}; exec(note["structure_statistic"]["code"], ns); stat=ns["stat"]
spec = importlib.util.spec_from_file_location("r", os.path.join(root,"cases","D-021","reference.py"))
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for conc in (2.4, 2.8, 3.2):
  for phi in (0.0, 0.15, 0.3):
    m.CONC=conc; m.PHI=phi
    out=[]
    for w in (m.plus, m.minus):
        rng=np.random.default_rng(1)
        out.append(np.mean([stat(w(rng)) for _ in range(3000)]))
    print(conc, phi, [round(x,3) for x in out])
