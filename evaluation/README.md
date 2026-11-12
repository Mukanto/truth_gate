# Evaluation material

| Path | Content |
|---|---|
| `cases/E2`, `cases/E4`, `cases/E5` | the evaluation case sets, published unchanged (set E1E3 is not published; see `docs/EVALUATION.md`). Each set holds faulty/fixed study pairs, a `manifest.json` with the expected checks, and a `CASES_SHA256.json` written before the first run |
| `hash_cases.py` | writes and verifies `CASES_SHA256.json` for a set |
| `run_eval_v02.py`, `run_eval_v03.py` | the pre-registered runners of the v0.2 and v0.3 evaluations |
| `../eval/harness*.py` | the harness that computes the pre-registered criteria from a results table |

## Verify the case hashes

```text
python -B -c "import sys; sys.path.insert(0, 'evaluation'); import hash_cases; [print(s, hash_cases.verify_set('evaluation/cases/' + s)) for s in ('E2', 'E4', 'E5')]"
```

(Run from the repository root. An intact set prints an empty list `[]`; otherwise the problems are listed.)

## Run a single case

```text
python -m kapi check evaluation/cases/E5/E5-01_faulty.py --out certs/E5-01_faulty.json
```

The expected checks of each case are in its set's `manifest.json`.

## About the runners

`run_eval_v02.py` and `run_eval_v03.py` are published so that the procedure can be inspected. They refuse to start
unless a freeze record (`FREEZE_v0_2.json` / `FREEZE_v0_3.json`) verifies the frozen `kapi/`, `eval/` and `spec/` files.
Those records belong to the private repository in which the evaluation was run and are not published, and the specification
is published as an edited copy (`docs/SPEC.md`), so the runners cannot be started as they are in this repository. The results
are summarised in [`../docs/EVALUATION.md`](../docs/EVALUATION.md). The harness prints the Turkish words `Tuttu` (held)
and `Tutmadı` (failed).
