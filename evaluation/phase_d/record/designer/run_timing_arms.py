"""PREREG_PHASE_D item 10: per-arm timing (designer). For every given case and arm: py -I validity_check.py --case cases/<id>
--package-root record/pkg --samples 1000 --seed 20261117 --arm W0|W1 --out validity/<id>/TIMING_<arm>.json (the tool
itself uses 20 samples of stream timing:plus and appends a "timing_arm" line to cases/validity_log.jsonl; the first non-dev
run on a (skeleton, fixed body) hash pair is decisive). Same process settings as run_validity.py (BLAS threads 1).
Usage: run_timing_arms.py WORKERS ID [ID ...]   (both arms of every id)"""
import concurrent.futures as cf, datetime, json, os, subprocess, sys, time
W = r"E:\Claude Projects\Kapi\phase_d_work"
TOOL = r"E:\Claude Projects\kapi-oss\evaluation\phase_d\tools\tools\validity_check.py"
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
workers, ids = int(sys.argv[1]), sys.argv[2:]
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run(job):
    i, arm = job
    out = os.path.join(W, "validity", i)
    os.makedirs(out, exist_ok=True)
    cmd = ["py", "-I", TOOL, "--case", os.path.join(W, "cases", i), "--package-root", os.path.join(W, "record", "pkg"),
           "--samples", "1000", "--seed", "20261117", "--arm", arm, "--out", os.path.join(out, f"TIMING_{arm}.json")]
    t0, start = time.time(), now()
    with open(os.path.join(out, f"timing_{arm}.log"), "w", encoding="utf-8") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=out)
    rec = {"case": i, "arm": arm, "start_utc": start, "end_utc": now(), "seconds": round(time.time() - t0, 1), "exit": rc,
           "cmd": cmd}
    with open(os.path.join(W, "validity", "TIMING_RUNNER_LOG.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"{rec['end_utc']} {i} {arm} exit {rc} {rec['seconds']} s", flush=True)
    return rec

with cf.ThreadPoolExecutor(workers) as ex:
    list(ex.map(run, [(i, a) for i in ids for a in ("W0", "W1")]))
print("all done", flush=True)
