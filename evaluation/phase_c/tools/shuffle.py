"""Phase C shuffle (PREREG_PHASE_C section 4 step 2): random ids, shuffled briefs, world-author batches.

Usage:
    py shuffle.py --briefs-dir DIR --classes CLASSES.json --seed-from FILE --out OUTDIR [--batch 15] [--force]

  DIR            holds one subfolder per class author, each with BRIEFS.json (a list of {"local_id", "claim",
                 "data_keys", "sizes"}); PRIVATE.json of the folder is read only to carry the local ids of briefs that
                 have none (matched by position) and is otherwise ignored.
  CLASSES.json   {"<folder>": "<class>", ...}: every folder with a BRIEFS.json must be listed, and the reverse.
  FILE           the frozen pre-registration manifest. Seed = int(SHA-256(bytes of FILE followed by the ASCII text
                 "phase-c-shuffle"), 16), i.e. the hex digest read as a number. The same inputs always give identical
                 outputs (folders are taken in sorted order, briefs in file order).
  Shuffle        Fisher-Yates over all briefs, driven by random.Random(seed): for i = n-1 down to 1, j = randrange(i+1),
                 swap(i, j). The briefs then get the ids C01, C02, ... in shuffled order.

Writes to OUTDIR:
  BRIEFS_SHUFFLED.json   [{"id", "claim", "data_keys", "sizes"}, ...] in shuffle order (public: no class, no local id)
  ID_MAP.json            [{"id", "folder", "local_id", "class"}, ...] (private)
  BATCH_01.json, ...     consecutive blocks of --batch briefs (same public format); the last block may be shorter
Refuses to overwrite existing files unless --force.
"""
import argparse, hashlib, json, os, random, sys

PUBLIC_FIELDS = ("claim", "data_keys", "sizes")
SALT = b"phase-c-shuffle"


def seed_from(path):
    with open(path, "rb") as f:
        data = f.read()
    return int(hashlib.sha256(data + SALT).hexdigest(), 16)


def read_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def write_json(path, obj):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)
        f.write("\n")


def collect(briefs_dir, classes):
    folders = sorted(d for d in os.listdir(briefs_dir) if os.path.isfile(os.path.join(briefs_dir, d, "BRIEFS.json")))
    missing = sorted(set(folders) - set(classes))
    extra = sorted(set(classes) - set(folders))
    if missing:
        raise SystemExit(f"folders with BRIEFS.json but no class in the mapping: {missing}")
    if extra:
        raise SystemExit(f"classes mapping lists folders without BRIEFS.json: {extra}")
    items, seen = [], set()
    for folder in folders:
        briefs = read_json(os.path.join(briefs_dir, folder, "BRIEFS.json"))
        priv_path = os.path.join(briefs_dir, folder, "PRIVATE.json")
        priv = read_json(priv_path) if os.path.isfile(priv_path) else None
        for i, b in enumerate(briefs):
            lid = b.get("local_id", b.get("id"))
            if lid is None and priv is not None and len(priv) == len(briefs):
                lid = priv[i].get("local_id")
            if lid is None:
                raise SystemExit(f"{folder}: brief #{i} has no local_id (and PRIVATE.json cannot supply one)")
            for f in PUBLIC_FIELDS:
                if f not in b:
                    raise SystemExit(f"{folder}/{lid}: field {f!r} missing")
            if (folder, lid) in seen:
                raise SystemExit(f"{folder}: duplicate local_id {lid}")
            seen.add((folder, lid))
            items.append({"folder": folder, "local_id": lid, "class": classes[folder], **{f: b[f] for f in PUBLIC_FIELDS}})
    return items


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--briefs-dir", required=True)
    ap.add_argument("--classes", required=True, help="JSON {folder: class}")
    ap.add_argument("--seed-from", required=True, help="file whose bytes give the seed (the frozen manifest)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=15)
    ap.add_argument("--force", action="store_true", help="overwrite existing output files")
    a = ap.parse_args(argv)
    if a.batch < 1:
        raise SystemExit("--batch must be >= 1")
    items = collect(a.briefs_dir, read_json(a.classes))
    n = len(items)
    seed = seed_from(a.seed_from)
    rng = random.Random(seed)
    order = list(range(n))
    for i in range(n - 1, 0, -1):  # Fisher-Yates
        j = rng.randrange(i + 1)
        order[i], order[j] = order[j], order[i]
    width = max(2, len(str(n)))
    public, id_map = [], []
    for k, idx in enumerate(order, start=1):
        it = items[idx]
        cid = f"C{k:0{width}d}"
        public.append({"id": cid, **{f: it[f] for f in PUBLIC_FIELDS}})
        id_map.append({"id": cid, "folder": it["folder"], "local_id": it["local_id"], "class": it["class"]})
    batches = [public[s:s + a.batch] for s in range(0, n, a.batch)]
    bwidth = max(2, len(str(len(batches))))
    outputs = {"BRIEFS_SHUFFLED.json": public, "ID_MAP.json": id_map}
    for b, blk in enumerate(batches, start=1):
        outputs[f"BATCH_{b:0{bwidth}d}.json"] = blk
    os.makedirs(a.out, exist_ok=True)
    exist = [f for f in outputs if os.path.exists(os.path.join(a.out, f))]
    if exist and not a.force:
        raise SystemExit(f"refusing to overwrite {exist} (use --force)")
    for f, obj in outputs.items():
        write_json(os.path.join(a.out, f), obj)
    print(f"seed (decimal) = {seed}")
    print(f"seed (hex)     = {seed:064x}")
    print(f"{n} briefs from {len({i['folder'] for i in items})} folder(s); {len(batches)} batch file(s) of up to {a.batch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
