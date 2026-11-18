"""Check that every input listed in a sandbox manifest is unchanged (sha256), optionally limited to one sandbox prefix.
Usage: manifest_check.py MANIFEST.json BASE_DIR [PREFIX]. Files the author may append to (LOG.md) are reported apart.
Also lists files present in the sandbox but not in the manifest (the author's outputs)."""
import hashlib, json, os, sys
man, base = json.load(open(sys.argv[1])), sys.argv[2]
pre = sys.argv[3] if len(sys.argv) > 3 else ""
changed, missing, appended = [], [], []
for rel, h in man.items():
    if not rel.startswith(pre):
        continue
    q = os.path.join(base, rel)
    if not os.path.exists(q):
        missing.append(rel)
    elif hashlib.sha256(open(q, "rb").read()).hexdigest() != h:
        (appended if os.path.basename(rel) == "LOG.md" else changed).append(rel)
new = []
for dp, _, fs in os.walk(os.path.join(base, pre)):
    for f in fs:
        rel = os.path.relpath(os.path.join(dp, f), base)
        if rel not in man:
            new.append(rel)
print(json.dumps({"checked": sum(r.startswith(pre) for r in man), "changed": changed, "missing": missing,
                  "log_changed": appended, "new_files": len(new)}, indent=1))
sys.exit(1 if changed or missing else 0)
