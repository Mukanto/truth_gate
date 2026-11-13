import os, difflib, ast
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))+"/cases"
for c in sorted(os.listdir(root)):
    sk = open(f"{root}/{c}/skeleton.py", encoding="utf-8").read().split("\n")
    out = {}
    for w in ("faulty","fixed"):
        t = open(f"{root}/{c}/{w}.py", encoding="utf-8").read().split("\n")
        out[w] = t
        ops = [o for o in difflib.SequenceMatcher(None, sk, t, autojunk=False).get_opcodes() if o[0] != "equal"]
        assert len(ops) == 1 and ops[0][0] == "replace" and sk[ops[0][1]:ops[0][2]] == ["    raise NotImplementedError"], (c, w, ops)
        # no non-numpy imports / forbidden names in the body
        body = "\n".join(t[ops[0][3]-0-(ops[0][4]-ops[0][3]):ops[0][4]]) if False else "\n".join(t[ops[0][3]:ops[0][4]])
        for bad in ("import ", "open(", "scipy", "np.random", "N,", "STUDY", "default_rng"):
            assert bad not in body, (c, w, bad)
    ds = [o for o in difflib.SequenceMatcher(None, out["faulty"], out["fixed"], autojunk=False).get_opcodes() if o[0] != "equal"]
    print(c, "ok; faulty vs fixed differing blocks:", [(o[0], out["faulty"][o[1]:o[2]], out["fixed"][o[3]:o[4]]) for o in ds][:1] if c!="B1-10" else "multi-line variant")
