"""PREREG_PHASE_D section 2.3: run the standard validity run (--samples 1000 --seed 20261117) of the given cases (designer).

Each case runs in its own process: py -I validity_check.py --case cases/<id> --package-root record/pkg --samples 1000
--seed 20261117 --out validity/<id>/RESULT.json [--no-structure for the null decoy D-032 only]; stdout/stderr go to
validity/<id>/run.log. The tool appends to cases/validity_log.jsonl itself (its only log). BLAS thread variables are set
to 1 so that runs neither oversubscribe the cores nor depend on thread count. Usage: run_validity.py WORKERS ID [ID ...]"""
import concurrent.futures as cf, datetime, json, os, subprocess, sys, time
W = r"E:\Claude Projects\Kapi\phase_d_work"
TOOL = r"E:\Claude Projects\kapi-oss\evaluation\phase_d\tools\tools\validity_check.py"
NO_STRUCTURE = {"D-032"}
env = dict(os.environ, OMP_NUM_THREADS="1", OPENBLAS_NUM_THREADS="1", MKL_NUM_THREADS="1", PYTHONDONTWRITEBYTECODE="1")
workers, ids = int(sys.argv[1]), sys.argv[2:]
now = lambda: datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def run(i):
    out = os.path.join(W, "validity", i)
    os.makedirs(out, exist_ok=True)
    cmd = ["py", "-I", TOOL, "--case", os.path.join(W, "cases", i), "--package-root", os.path.join(W, "record", "pkg"),
           "--samples", "1000", "--seed", "20261117", "--out", os.path.join(out, "RESULT.json")]
    if i in NO_STRUCTURE:
        cmd.append("--no-structure")
    t0, start = time.time(), now()
    with open(os.path.join(out, "run.log"), "w", encoding="utf-8") as f:
        rc = subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, env=env, cwd=out)
    rec = {"case": i, "start_utc": start, "end_utc": now(), "seconds": round(time.time() - t0, 1), "exit": rc, "cmd": cmd}
    with open(os.path.join(W, "validity", "RUNNER_LOG.jsonl"), "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    print(f"{rec['end_utc']} {i} exit {rc} {rec['seconds']} s", flush=True)
    return rec

with cf.ThreadPoolExecutor(workers) as ex:
    list(ex.map(run, ids))
print("all done", flush=True)
