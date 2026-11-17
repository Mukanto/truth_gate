"""Phase D shuffle (R2-9, R2-18; TOOLS_SPEC_D_round2 item 9): neutral ids, one shuffle of all briefs, world-author batches.

A copy, adapted, of ``evaluation/phase_c/tools/shuffle.py``.  Differences from Phase C:

| | Phase C (shuffle.py) | Phase D (this file) |
|---|---|---|
| seed | ``int(SHA-256(bytes of FILE + b"phase-c-shuffle"), 16)``, FILE the frozen pre-registration manifest | ``int(SHA-256(bytes of FREEZE_PREREG_D.json + b"phase-d-shuffle"), 16)`` |
| shuffle | Fisher-Yates, ``random.Random(seed)`` | the same |
| input | ``--briefs-dir`` with one folder per class author (BRIEFS.json) and ``--classes`` | ``--items ITEMS.json``: one list of all briefs and reserves (B-2, B-3 and decoys) with designer ids and their class, half, source, subtype or tag and reserve flag |
| order of the input before the shuffle | folders sorted, briefs in file order | sorted by designer id (the result does not depend on the order of the file) |
| neutral id | ``C01``, ``C02``, ... | ``D-001``, ``D-002``, ... (``D-`` and three digits) |
| batches | blocks of 15 | blocks of 12 consecutive briefs, the last one shorter |
| arms | one set of batches | the same batch files serve W-0 and W-1 (``BATCH_01.json`` ... carry no arm) |
| private map | ``ID_MAP.json``: id, folder, local_id, class | ``ID_MAP_D.json``: id, designer_id, class, half, source, subtype_or_tag, reserve; never written into a batch file |
| public fields | claim, data_keys, sizes | the same (``data_keys`` entries keep their ``dims``) |

Usage:
    py shuffle_d.py --items ITEMS.json --seed-from FREEZE_PREREG_D.json --out OUTDIR [--batch 12] [--force]

  ITEMS.json     a list of {"designer_id", "class", "half", "source", "subtype_or_tag", "reserve", "claim", "data_keys",
                 "sizes"}.  ``designer_id`` is unique; ``class`` is the class name ("B-2", "B-3", or the decoy class);
                 ``half`` is "A", "B" or null (decoys); ``subtype_or_tag`` is the B-2 subtype or the B-3 tag (null for a
                 decoy without one); ``reserve`` is true for a reserve.  Only the last three fields of the brief
                 (claim, data_keys, sizes) are ever written into a batch or into BRIEFS_SHUFFLED.json.
  FILE           the frozen pre-registration manifest.  Seed = int(SHA-256(bytes of FILE followed by the ASCII text
                 "phase-d-shuffle"), 16), the hex digest read as a number.  The same inputs always give identical outputs.
  Shuffle        Fisher-Yates over all items (sorted by designer id first), driven by random.Random(seed): for
                 i = n-1 down to 1, j = randrange(i+1), swap(i, j).  The items then get the ids D-001, D-002, ... in
                 shuffled order.

Writes to OUTDIR:
  BRIEFS_SHUFFLED.json   [{"id", "claim", "data_keys", "sizes"}, ...] in shuffle order (public: no class, no designer id)
  ID_MAP_D.json          [{"id", "designer_id", "class", "half", "source", "subtype_or_tag", "reserve"}, ...] (private)
  BATCH_01.json, ...     consecutive blocks of --batch briefs (same public format); the last block may be shorter
Refuses to overwrite existing files unless --force.  Exit code 0, or a message and exit code 1 on bad input.

Subset batches (R3-7, D-R4-7)
-----------------------------
After the validity freeze only some of the briefs go to the world authors (the pairs and decoys of ``FREEZE_VALIDITY.json``;
dropped pairs and unused reserves do not).  ``--subset IDS.json`` re-cuts the batches for them without touching anything else:

    py shuffle_d.py --subset IDS.json --out OUTDIR [--batch 12] [--force]

  IDS.json       a JSON list of neutral ids ("D-007", ...), without duplicates, every one in OUTDIR/BRIEFS_SHUFFLED.json.
  Batches        the public briefs of those ids in neutral-id order (the order of the ids themselves, which is the shuffled
                 order), cut into consecutive blocks of --batch (12; the last block is shorter), written as
                 OUTDIR/batches_subset_01.json, batches_subset_02.json, ...  The same files serve W-0 and W-1.
  Unchanged      the neutral ids, BRIEFS_SHUFFLED.json, ID_MAP_D.json and the item-2 BATCH_NN.json files are never written in
                 this mode.  ``--items`` and ``--seed-from`` are not used.  Existing batches_subset_*.json files are
                 refused unless --force, which removes them first (so no stale batch file stays behind).
"""
import argparse
import hashlib
import json
import os
import random
import sys

PUBLIC_FIELDS = ("claim", "data_keys", "sizes")
PRIVATE_FIELDS = ("designer_id", "class", "half", "source", "subtype_or_tag", "reserve")
SALT = b"phase-d-shuffle"
ID_FORMAT = "D-{:03d}"
MAX_ITEMS = 999
BATCH_SIZE = 12


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


def load_items(path):
    """The validated items of ITEMS.json, sorted by designer id."""
    data = read_json(path)
    if not isinstance(data, list) or not data:
        raise SystemExit("ITEMS.json must be a non-empty list")
    seen = set()
    for n, it in enumerate(data):
        if not isinstance(it, dict):
            raise SystemExit(f"item #{n} is not an object")
        for f in PRIVATE_FIELDS + PUBLIC_FIELDS:
            if f not in it:
                raise SystemExit(f"item #{n} ({it.get('designer_id')}): field {f!r} missing")
        if not isinstance(it["designer_id"], str) or not it["designer_id"]:
            raise SystemExit(f"item #{n}: designer_id must be a non-empty string")
        if it["designer_id"] in seen:
            raise SystemExit(f"duplicate designer_id {it['designer_id']}")
        seen.add(it["designer_id"])
        if not isinstance(it["reserve"], bool):
            raise SystemExit(f"{it['designer_id']}: reserve must be true or false")
    if len(data) > MAX_ITEMS:
        raise SystemExit(f"{len(data)} items: more than {MAX_ITEMS}, the neutral id has three digits")
    return sorted(data, key=lambda it: it["designer_id"])


def shuffled_order(n, seed):
    """Fisher-Yates over ``range(n)`` driven by ``random.Random(seed)``: for i = n-1 down to 1, j = randrange(i+1), swap."""
    rng = random.Random(seed)
    order = list(range(n))
    for i in range(n - 1, 0, -1):
        j = rng.randrange(i + 1)
        order[i], order[j] = order[j], order[i]
    return order


def shuffle(items, seed, batch=BATCH_SIZE):
    """``(public, id_map, batches)`` for sorted ``items``."""
    order = shuffled_order(len(items), seed)
    public, id_map = [], []
    for k, idx in enumerate(order, start=1):
        it = items[idx]
        nid = ID_FORMAT.format(k)
        public.append({"id": nid, **{f: it[f] for f in PUBLIC_FIELDS}})
        id_map.append({"id": nid, **{f: it[f] for f in PRIVATE_FIELDS}})
    batches = [public[s:s + batch] for s in range(0, len(public), batch)]
    return public, id_map, batches


def subset_batches(ids_path, out, batch, force):  # D-R4-7
    """Write ``batches_subset_NN.json`` for the neutral ids in ``ids_path``; nothing else in ``out`` is touched."""
    ids = read_json(ids_path)
    if not isinstance(ids, list) or not ids or not all(isinstance(i, str) for i in ids):
        raise SystemExit("IDS.json must be a non-empty list of neutral ids")
    if len(set(ids)) != len(ids):
        raise SystemExit("IDS.json has duplicate ids")
    public = {b["id"]: b for b in read_json(os.path.join(out, "BRIEFS_SHUFFLED.json"))}
    unknown = sorted(i for i in ids if i not in public)
    if unknown:
        raise SystemExit(f"ids that are not in BRIEFS_SHUFFLED.json: {unknown}")
    chosen = [public[i] for i in sorted(ids)]
    blocks = [chosen[s:s + batch] for s in range(0, len(chosen), batch)]
    width = max(2, len(str(len(blocks))))
    old = sorted(f for f in os.listdir(out) if f.startswith("batches_subset_") and f.endswith(".json"))
    if old and not force:
        raise SystemExit(f"refusing to overwrite {old} (use --force)")
    for f in old:
        os.remove(os.path.join(out, f))
    for b, blk in enumerate(blocks, start=1):
        write_json(os.path.join(out, f"batches_subset_{b:0{width}d}.json"), blk)
    print(f"{len(chosen)} ids; {len(blocks)} subset batch file(s) of up to {batch}")
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--items", help="ITEMS.json: all briefs and reserves with designer ids")
    ap.add_argument("--seed-from", help="FREEZE_PREREG_D.json: its bytes give the seed")
    ap.add_argument("--subset", metavar="IDS.json", help="re-cut batches over these neutral ids (D-R4-7); needs only --out")
    ap.add_argument("--out", required=True)
    ap.add_argument("--batch", type=int, default=BATCH_SIZE)
    ap.add_argument("--force", action="store_true", help="overwrite existing output files")
    a = ap.parse_args(argv)
    if a.batch < 1:
        raise SystemExit("--batch must be >= 1")
    if a.subset:  # D-R4-7
        return subset_batches(a.subset, a.out, a.batch, a.force)  # D-R4-7
    if not a.items or not a.seed_from:  # D-R4-7
        raise SystemExit("--items and --seed-from are required (or --subset IDS.json)")  # D-R4-7
    items = load_items(a.items)
    seed = seed_from(a.seed_from)
    public, id_map, batches = shuffle(items, seed, a.batch)
    bwidth = max(2, len(str(len(batches))))
    outputs = {"BRIEFS_SHUFFLED.json": public, "ID_MAP_D.json": id_map}
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
    print(f"{len(items)} items; {len(batches)} batch file(s) of up to {a.batch}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
