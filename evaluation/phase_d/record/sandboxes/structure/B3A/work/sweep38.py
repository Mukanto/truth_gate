import sys, json, importlib.util
sys.path.insert(0,'pkg')
import numpy as np
note=json.load(open('cases/D-038/NOTE.json')); ns={'np':np}; exec(note['structure_statistic']['code'],ns); stat=ns['stat']
spec=importlib.util.spec_from_file_location('r','cases/D-038/reference.py'); m=importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
for load in (0.1,0.15,0.2,0.25,0.3):
    for sd in (0.3,0.45):
        m.CIG_POP_LOAD=load; m.CIG_LOG_SD=sd
        v=[stat(m.plus(np.random.default_rng(i))) for i in range(200)]
        print(load,sd,round(np.mean(v),3),round(np.std(v),3))
