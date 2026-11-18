import json, sys, traceback
T = r"E:\Claude Projects\kapi-oss\evaluation\phase_d\tools\tools"
sys.path.insert(0, T)
import check_skeletons_d as c
print(c.verify_package_root(r"E:\Claude Projects\Kapi\phase_d_work\record\pkg"))
case = sys.argv[1]
brief = json.load(open(case + r"\brief.json", encoding="utf-8"))
mod = c.load(case + r"\reference.py", "skel_x")
try:
    print(c.dyn_check(brief["id"], mod, brief)[0])
except Exception:
    traceback.print_exc()
