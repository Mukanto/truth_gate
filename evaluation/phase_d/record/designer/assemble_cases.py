"""PREREG_PHASE_D section 3 items 4-6: copy the authors' files into the case folders (designer).

For every neutral id of ID_MAP_D.json: faulty_body.py, fixed_body.py, CASE.md from criterion/<half>/half/cases/<id>/ and
reference.py from structure/<half>/cases/<id>/ into cases/<id>/. Refuses to overwrite a different existing file. Writes
MANIFEST_cases_assembled.json (sha256 of every copied file, with its source path)."""
import hashlib, json, os, shutil, sys
WORK = r"E:\Claude Projects\Kapi\phase_d_work"
idmap = json.load(open(os.path.join(WORK, "shuffle", "ID_MAP_D.json"), encoding="utf-8"))
sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()
man, problems = {}, []
for m in sorted(idmap, key=lambda m: m["id"]):
    i, half = m["id"], m["designer_id"].split("-")[0]
    srcs = {f: os.path.join(WORK, "criterion", half, "half", "cases", i, f) for f in ("faulty_body.py", "fixed_body.py", "CASE.md")}
    srcs["reference.py"] = os.path.join(WORK, "structure", half, "cases", i, "reference.py")
    for f, s in srcs.items():
        d = os.path.join(WORK, "cases", i, f)
        if not os.path.exists(s):
            problems.append(f"{i}: missing {os.path.relpath(s, WORK)}")
            continue
        if os.path.exists(d) and sha(d) != sha(s):
            problems.append(f"{i}: {f} exists and differs; not overwritten")
            continue
        shutil.copy2(s, d)
        man[f"{i}/{f}"] = {"sha256": sha(d), "from": os.path.relpath(s, WORK)}
json.dump(man, open(os.path.join(WORK, "MANIFEST_cases_assembled.json"), "w"), indent=1, sort_keys=True)
print(len(man), "files copied;", len(problems), "problems")
for p in problems:
    print(" ", p)
sys.exit(1 if problems else 0)
