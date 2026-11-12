# Convergence criteria on synthetic worlds

A generic pattern for studies of the form: *a deterministic model with an update law `x_{k+1} = f(x_k)` has a fixed point
`x_star`. Is it attracting within N cycles, while transients stay inside the model's domain of validity?*

The study file is [`study.py`](study.py). Run it with:

```text
mkdir certs
python -m kapi check examples/convergence_criteria/study.py --out certs/convergence.json
```

## What is in the study

| Part | Content |
|---|---|
| Data schema | `x_star` (fixed point), `lam` (local multiplier), `traj` (S x (N + 1) trajectories), `in_domain` (S x N booleans: is each transition inside the domain) |
| `C1_local_attraction` | the local multiplier satisfies `abs(lam) < 1` |
| `C2_convergence_N` | among starts that stay in the domain, every trajectory is within `TOL` of `x_star` after N cycles; UNDEFINED if no start stays in the domain |
| `C3_in_domain` | the whole grid of starts stays in the domain for all N cycles |
| `plus` world | a linear update law with multiplier 0.02 (contracting): all criteria can hold |
| `minus` world | the same world with multiplier 1.39 (repelling): the criteria can fail. The change is declared in `change=` |
| Controls | `frozen_state` (nothing moves, for C2), `unit_multiplier` (`lam = 1`, for C1), `forced_exit` (one start leaves the domain, for C3) |
| Mode | `deterministic=True`: every stream is sampled once |

The domain rule of the synthetic worlds: a transition that lands below `LOWER_BOUND` is out of the domain, and so is every
later transition of that start.

## The verdict, and why it is not clean

| Criterion | Verdict | Flags |
|---|---|---|
| C1 | `NOT_FALSIFIABLE` | `K5_HOLDS_ON_NOISE`, `K5_HOLDS_ON_DEGENERATE` |
| C2 | `WEAK` | `K5_INCONCLUSIVE:noise`, `K5_INCONCLUSIVE:zeros` |
| C3 | `FALSIFIABLE` | none |

The study verdict is `NOT_FALSIFIABLE`, because that is the most severe component verdict.

The four flags have one cause. The gate's vacuity probes replace **every** array in the data by noise or zeros. C1 reads a
single precomputed scalar, `lam`. With `lam` replaced by a draw from N(0, 1) or by 0, `abs(lam) < 1` holds, and the probe
reports that the criterion "holds on noise". C2 depends on `in_domain`, which the probes turn into random or all-False
values, so no start qualifies and C2 is UNDEFINED, which the gate reports as inconclusive.

In the real study these four flags were examined and **rejected with written reasons**: the generic probes had been applied
to a precomputed scalar and to a conditional criterion, which is not what the probes were designed for. The protocol rule
is that a mandatory flag is never silenced by adding a cosmetic control; if a flag is not accepted as a defect, the
pre-registration records why. You may choose differently: for example, make C1 estimate the multiplier from the
trajectories, which makes the probes meaningful, at the cost of changing the criterion (and then that change belongs in the
pre-registration, before the freeze).

## Why the real model must not run inside the certificate before the freeze

This file contains only synthetic worlds. The **real runner** imports `C1_local_attraction`, `C2_convergence_N` and
`C3_in_domain` from `study.py` unchanged and feeds them the real model's output in the same schema. The same functions are
therefore tested on synthetic worlds first and applied to the real model later.

Do not put the real model into `study.py`, and do not add a "real" world to the certificate. The certificate is hashed,
attached to the pre-registration and shown to reviewers **before** the freeze. A world that calls the real model would
make the certificate contain the real result (or something that determines it), and then nothing in the pre-registration
would be prospective any more. The gate's whole purpose is to answer "could this criterion fail?" without knowing whether it
does.

A sketch of the runner (in a separate file, frozen with the rest):

```python
# run_real.py (frozen, started with protocol/templates/run_guarded.py)
from study import C1_local_attraction, C2_convergence_N, C3_in_domain
from my_model import run_model            # your model; never imported by study.py

data = run_model()                        # returns x_star, lam, traj, in_domain in the schema above
print(C1_local_attraction(data), C2_convergence_N(data), C3_in_domain(data))
```

Note that `study.py` is a single file that the gate loads under its leak guard. It cannot import local helper modules,
which is also why the model cannot be imported into it by accident.
