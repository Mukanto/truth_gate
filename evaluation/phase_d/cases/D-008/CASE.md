# CASE D-008 (author-local id B3A-08)

## 1. Case
- Case id: D-008 (brief author's local id B3A-08)
- Class: B-3, coupling by construction (half A)
- Tag: shared-measured-component; statistic family: regression-slope; role pair (ARC81 pair 2 of 2)

## 2. Source and documenting passage
- Source key: ARC81
- Passage: 'Type 2 coupling is the functional relationship between two calculated variables which have one or more common component variables.' (abstract, PubMed 7212790). The abstract gives no correction; the correction used is the standard remedy of an independent measurement of the shared term.
- Read: Read by the brief author in the abstract (PubMed efetch text, `fetched/arc81_pubmed.txt`); the abstract documents the coupling, not a correction (the correction used is the generic remedy of an independent measurement of the shared term; not verified in the source text). I fetched nothing online.

## 3. Brief
- Claim: Within patients, oxygen consumption rises with oxygen delivery: the mean over patients of the within-patient slope of oxygen consumption on oxygen delivery is at least 0.1 mL/min per mL/min.
- Data keys:
  - `cardiac_output` (patients, occasions) float: cardiac output of each patient at each measurement occasion, in L/min
  - `arterial_o2_content` (patients, occasions) float: oxygen content of arterial blood of each patient at each occasion, in mL O2 per dL
  - `venous_o2_content` (patients, occasions) float: oxygen content of mixed venous blood of each patient at each occasion, in mL O2 per dL
  - `vo2_expired_gas` (patients, occasions) float: oxygen consumption of each patient at each occasion measured from expired-gas analysis, in mL/min
- Sizes: {"patients": 40, "occasions": 6}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 37: `vo2 = co * (ca - cv) * 10.0`
  - Within each patient the least-squares slope across occasions of the Fick-calculated VO2 = cardiac_output * (arterial - venous content) * 10 on DO2 = cardiac_output * arterial content * 10 (shared cardiac output); mean of the slopes compared with 0.1 (`>=`). Parameters: factor 10; none else numeric in the source. Documented in ARC81 (type 2 coupling).
- **Fixed body, the correction** (`fixed_body.py`): line 37: `vo2 = vo`
  - Same per-patient slope with the independently measured `vo2_expired_gas` as the response, mean over patients compared with the same 0.1 (`>=`). Generic remedy, not stated in the abstract.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Mean within-patient slope of measured consumption on calculated delivery.

## 5. Allowed-guard minimum
2 occasions, at least 1 patient with a defined slope (a patient with zero variance of delivery is not counted), non-finite values (all keys).

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-008 types ['bool'] max_time_s 0.00011`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
Minimum 1 patient with a defined slope instead of the note's 2: a mean over one patient is defined, and the rule caps the guard at the smallest defined size. Non-finite values anywhere give None (the note allows the same).
