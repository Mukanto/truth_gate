# Rule text (Phase D pre-registration, section 5, excerpt)

- **Run.** Truth_Gate at tag `v0.5.1`, full mode, default settings, one check at a time. For every pair, both twins run
  in arm R (the reference worlds), arm W-0 and arm W-1. Infrastructure failures are handled as PC §6. A check beyond 60
  minutes is a timeout.
- **Expected flags** as PC §6, from `EXPECTED_FLAGS_D.json`.
- **Rate flags and their streams:**

  | Flag | Stream |
  |---|---|
  | `K2_HIGH_SIZE`, `K2_FAILS_UNREACHABLE` | `world:minus` |
  | `HIGH_RATE:control:<id>` | that control's stream |
  | `K4_CONTROL_ALSO_HOLDS` | each control stream s with `bounds[s].upper ≥ bounds[world:plus].lower` (the gate's rule) |
  | `K5_HOLDS_ON_NOISE`, `HIGH_RATE:probe:noise` | `probe:noise` |
  | `K5_HOLDS_ON_NULL`, `HIGH_RATE:world:null` | `world:null` |
  | `HIGH_RATE:probe:shuffle:<a>,<b>` | that shuffle stream |
  | `K5_HOLDS_ON_SHUFFLE` | each shuffle stream s with `bounds[s].upper ≥ bounds[world:plus].lower` |

  `K2_NO_SEPARATION` alone is not a rate flag.
- **Attributable detection** of a pair in an arm (`tools/attributable.py`). The faulty study's verdict is
  NOT_FALSIFIABLE, and at least one of its expected rate flags, on a stream s, meets both conditions:
  - **(a)** the fixed study of the same arm carries no rate flag on s;
  - **(b)** the faulty count on s exceeds the fixed count, with a one-sided Fisher exact p < 0.05.

  A stream does not qualify if the fixed study has a load error or a hard UNDEFINED on s (`hard_undefined > 0`). A
  faulty load error is not a detection. Each such case is listed.

  The rule asks whether some expected flag is explained by the error on its stream. That differs from D-3's question,
  whether the faulty verdict would occur with the fixed criterion: B3-04 is attributable under the rule, generic only,
  and counted by D-3.

  The twins share seeds, so their counts on a stream come from the same samples. The certificates hold only counts, so
  a paired test is not available. Fisher's test treats the counts as independent, which is conservative here.
- **Generic and declared.** An attributable detection is **generic** if `probe:noise` is among its qualifying streams,
  and **declared** if a qualifying stream other than `probe:noise` exists. A detection can be both. The noise probe
  draws N(0, 1) and Bernoulli arrays from the brief's keys, shapes and dtypes, which are identical in every arm, so its
  distribution is the same in every arm.
