"""Phase D designer adapter (REVISIONS-post-freeze P-3, the Phase C P-3 adapter in case-folder layout).

The frozen check_skeletons_d.py reads brief["sizes"] as text (line 325), but the briefs state sizes as JSON objects. For
every case folder cases/<id>/ this writes validity/skelcheck/<id>/: brief.json, a copy of the case's brief.json in which a
non-string `sizes` is replaced by its JSON text (json.dumps(sizes, ensure_ascii=False); same names and numbers; every
other field unchanged), plus copies of reference.py and, when present, skeletons/W0.py and skeletons/W1.py. The case
folders are not changed. Rerunning refreshes the copies. Usage: py -I skelcheck_folders.py [ID ...]"""
import json, os, shutil, sys
W = r"E:\Claude Projects\Kapi\phase_d_work"
ids = sys.argv[1:] or sorted(d for d in os.listdir(os.path.join(W, "cases")) if d.startswith("D-"))
n = 0
for i in ids:
    src, dst = os.path.join(W, "cases", i), os.path.join(W, "validity", "skelcheck", i)
    os.makedirs(dst, exist_ok=True)
    b = json.load(open(os.path.join(src, "brief.json"), encoding="utf-8"))
    if not isinstance(b.get("sizes"), str):
        b["sizes"] = json.dumps(b["sizes"], ensure_ascii=False)
        n += 1
    json.dump(b, open(os.path.join(dst, "brief.json"), "w", encoding="utf-8"), indent=1, ensure_ascii=False)
    for rel in ("reference.py", os.path.join("skeletons", "W0.py"), os.path.join("skeletons", "W1.py")):
        if os.path.exists(os.path.join(src, rel)):
            os.makedirs(os.path.dirname(os.path.join(dst, rel)), exist_ok=True)
            if os.path.exists(os.path.join(dst, rel)):  # the source may be read-only (frozen); copy2 keeps that bit
                os.chmod(os.path.join(dst, rel), 0o666)
                os.remove(os.path.join(dst, rel))
            shutil.copy2(os.path.join(src, rel), os.path.join(dst, rel))
print(f"{len(ids)} check folders, {n} sizes rendered as JSON text")
