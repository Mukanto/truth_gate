import ast, json, sys, time, importlib.util, zlib
from pathlib import Path
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE / "pkg"))
import truth_gate  # noqa: E402

BATCH = {b["id"]: b for b in json.loads((HERE / "BATCH.json").read_text(encoding="utf-8"))}
BANNED = {"open", "eval", "exec", "compile", "__import__", "input", "breakpoint", "globals", "locals", "vars",
          "getattr", "setattr", "delattr", "exit", "quit", "print", "__builtins__"}
NP_FILE = {"load", "save", "savez", "savetxt", "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap"}
STUDY_KW = {"name", "criteria", "worlds", "controls", "premises", "relational"}


def ast_check(path, bid):
    errs = []
    src = path.read_text(encoding="utf-8")
    tree = ast.parse(src)
    body = tree.body
    doc = ast.get_docstring(tree, clean=False)
    want = f"{bid}: {BATCH[bid]['claim']}"
    if doc != want:
        errs.append("docstring mismatch")
    for i, node in enumerate(body):
        if i == 0 and isinstance(node, ast.Expr):
            continue
        if isinstance(node, (ast.Import, ast.ImportFrom, ast.Assign, ast.FunctionDef)):
            continue
        errs.append(f"module-level node {type(node).__name__} line {node.lineno}")
    imports = [ast.unparse(n) for n in body if isinstance(n, (ast.Import, ast.ImportFrom))]
    if imports != ["import numpy as np", "from truth_gate import Study, Criterion, World, Premise, Control"]:
        errs.append(f"imports {imports}")
    for node in ast.walk(tree):
        if isinstance(node, ast.Name) and node.id in BANNED:
            errs.append(f"banned name {node.id}")
        if isinstance(node, ast.Attribute):
            if node.attr.startswith("__"):
                errs.append(f"dunder attr {node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id == "np" and node.attr in NP_FILE:
                errs.append(f"np file fn {node.attr}")
            if isinstance(node.value, ast.Name) and node.value.id == "np" and node.attr == "random":
                errs.append("np.random used")
            if node.attr in NP_FILE:
                errs.append(f"file-like attr {node.attr}")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id == "World":
                kws = sorted(k.arg for k in node.keywords)
                if not ((len(node.args) == 1 and kws == []) or (len(node.args) == 1 and kws == ["change", "derived_from"])):
                    errs.append("World call form")
            if node.func.id == "Study":
                bad = [k.arg for k in node.keywords if k.arg not in STUDY_KW]
                if bad or node.args:
                    errs.append(f"Study kwargs {bad}")
    return errs


def load(path):
    spec = importlib.util.spec_from_file_location("sk_" + path.stem.replace("-", "_"), path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def rng_for(stream, i):
    return np.random.default_rng(np.random.SeedSequence([20261105, zlib.crc32(stream.encode()), i]))


def check_dict(d, brief):
    errs = []
    keys = [k["key"] for k in brief["data_keys"]]
    if sorted(d) != sorted(keys):
        errs.append(f"keys {sorted(d)} vs {sorted(keys)}")
        return errs
    for k in brief["data_keys"]:
        a = d[k["key"]]
        want_dtype = np.float64 if k["dtype"] == "float" else np.bool_
        if not isinstance(a, np.ndarray) or a.dtype != want_dtype:
            errs.append(f"{k['key']} dtype {getattr(a, 'dtype', type(a))}")
        if tuple(a.shape) != tuple(k["dims"]):
            errs.append(f"{k['key']} shape {a.shape} vs {k['dims']}")
        if a.dtype == np.float64 and not np.all(np.isfinite(a)):
            errs.append(f"{k['key']} non-finite")
        if max(a.shape) > 2000 or a.size > 2_000_000:
            errs.append(f"{k['key']} too big")
    return errs


def same(a, b):
    return a.shape == b.shape and a.dtype == b.dtype and np.array_equal(a, b)


def main(ids):
    for bid in ids:
        path = HERE / "skeletons" / f"{bid}.py"
        brief = BATCH[bid]
        errs = ast_check(path, bid)
        mod = load(path)
        st = mod.STUDY
        assert st.name == bid
        tmax = 0.0
        diffkeys = set()
        stats = {"plus": {}, "minus": {}}
        for i in range(40):
            ds = {}
            for w in ("plus", "minus"):
                t0 = time.perf_counter()
                d = st.worlds[w].generate(rng_for("world:" + w, i))
                tmax = max(tmax, time.perf_counter() - t0)
                errs += check_dict(d, brief)
                ds[w] = d
                for k, a in d.items():
                    stats[w].setdefault(k, []).append((float(np.mean(a)), float(np.std(a))))
            # paired: same i for plus and minus with the plus stream (as the identical-minus check pairs them)
            dp = st.worlds["plus"].generate(rng_for("pair", i))
            dm = st.worlds["minus"].generate(rng_for("pair", i))
            diffkeys |= {k for k in dp if not same(dp[k], dm[k])}
            if i < 10:
                for c in st.controls:
                    t0 = time.perf_counter()
                    dc = c.transform(ds["plus"], rng_for("control:" + c.id, i))
                    tmax = max(tmax, time.perf_counter() - t0)
                    errs += [f"control {c.id}: " + e for e in check_dict(dc, brief)]
                    if all(same(dc[k], ds["plus"][k]) for k in ds["plus"]):
                        errs.append(f"control {c.id} unchanged on draw {i}")
        # determinism: same seed twice
        a = st.worlds["plus"].generate(rng_for("det", 0))
        b = st.worlds["plus"].generate(rng_for("det", 0))
        if not all(same(a[k], b[k]) for k in a):
            errs.append("non-deterministic world")
        line = f"{bid}: errors={sorted(set(errs)) or 'none'} max_ms={tmax*1000:.1f} minus_changes={sorted(diffkeys)}"
        print(line)
        for k in stats["plus"]:
            mp = np.array(stats["plus"][k]); mm = np.array(stats["minus"][k])
            print(f"    {k:22s} mean plus {mp[:,0].mean():10.4f} minus {mm[:,0].mean():10.4f} | "
                  f"sd plus {mp[:,1].mean():9.4f} minus {mm[:,1].mean():9.4f}")


if __name__ == "__main__":
    main(sys.argv[1:] or sorted(BATCH))
