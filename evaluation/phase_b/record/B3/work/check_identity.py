"""Text check: faulty.py and fixed.py equal skeleton.py outside the criterion body (and stay within the NotImplementedError line)."""
import glob, os
ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B3\cases"
for c in sorted(os.listdir(ROOT)):
    sk = open(f"{ROOT}\{c}\skeleton.py", encoding="utf-8", newline="").read()
    a, b = sk.split("    raise NotImplementedError\n")
    for w in ("faulty", "fixed"):
        t = open(f"{ROOT}\{c}\{w}.py", encoding="utf-8", newline="").read()
        ok = t.startswith(a) and t.endswith(b) and "NotImplementedError" not in t
        print(c, w, "identical outside body" if ok else "MISMATCH")
