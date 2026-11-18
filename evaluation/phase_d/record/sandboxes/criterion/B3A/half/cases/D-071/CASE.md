# CASE D-071 (author-local id B3A-04)

## 1. Case
- Case id: D-071 (brief author's local id B3A-04)
- Class: B-3, coupling by construction (half A)
- Tag: shared-measured-component; statistic family: correlation; role pair (ARC81 pair 1 of 2)

## 2. Source and documenting passage
- Source key: ARC81
- Passage: 'Type 2 coupling is the functional relationship between two calculated variables which have one or more common component variables.' (abstract, PubMed 7212790). The abstract gives no correction; the correction used is the standard remedy of using an independent measurement of the shared term.
- Read: Read by the brief author in the abstract (PubMed efetch text, `fetched/arc81_pubmed.txt`); the abstract documents the coupling, not a correction (the correction used is the generic remedy of an independent measurement of the shared term; not verified in the source text). I fetched nothing online.

## 3. Brief
- Claim: Across patients, oxygen delivery and oxygen consumption are positively correlated: the Pearson correlation coefficient between them is at least 0.4.
- Data keys:
  - `cardiac_output` (patients,) float: cardiac output of each patient, in L/min
  - `arterial_o2_content` (patients,) float: oxygen content of arterial blood of each patient, in mL O2 per dL
  - `venous_o2_content` (patients,) float: oxygen content of mixed venous blood of each patient, in mL O2 per dL
  - `vo2_expired_gas` (patients,) float: oxygen consumption of each patient measured from expired-gas analysis, in mL/min
- Sizes: {"patients": 120}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 46: `vo2 = co * (ca - cv) * 10.0`
  - Oxygen consumption calculated by the Fick equation VO2 = cardiac_output * (arterial - venous content) * 10 from the same cardiac output that enters delivery DO2 = cardiac_output * arterial content * 10; Pearson correlation of DO2 with it, compared with 0.4 (`>=`). Parameters: the factor 10 (mL/dL to mL/L); no other numeric parameter in the source. Documented in ARC81 (passage above, type 2 coupling).
- **Fixed body, the correction** (`fixed_body.py`): line 46: `vo2 = vo`
  - Pearson correlation of the same DO2 with the independently measured expired-gas consumption `vo2_expired_gas`, compared with the same 0.4 (`>=`). The correction is the generic remedy, not stated in the abstract (flagged in the private note).
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Correlation between calculated oxygen delivery and consumption measured by a method that does not use cardiac output.

## 5. Allowed-guard minimum
2 patients, non-finite values, zero variance of delivery or of the consumption used (inside `_corr`). Same as the note.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-071 types ['bool'] max_time_s 0.00006`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none. The correction is not verified in the source text (abstract only), as the private note says.
