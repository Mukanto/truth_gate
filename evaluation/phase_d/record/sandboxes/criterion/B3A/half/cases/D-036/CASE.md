# CASE D-036 (author-local id B3A-15)

## 1. Case
- Case id: D-036 (brief author's local id B3A-15)
- Class: B-3, coupling by construction (half A)
- Tag: shared-measured-component; statistic family: R-squared; role reserve (ARC81)

## 2. Source and documenting passage
- Source key: ARC81
- Passage: 'Type 2 coupling is the functional relationship between two calculated variables which have one or more common component variables.' and 'one variable either directly or indirectly contains the whole or components of the second variable.' (abstract, PubMed 7212790). The abstract gives no correction; the correction used is the standard remedy of an independent measurement of the shared term.
- Read: Read by the brief author in the abstract (PubMed efetch text, `fetched/arc81_pubmed.txt`); the abstract documents the coupling, not a correction (the correction used is the generic remedy of an independent measurement of the shared term; not verified in the source text). I fetched nothing online.

## 3. Brief
- Claim: Across patients, cardiac output explains at least 25% of the variance in systemic vascular resistance (R-squared of at least 0.25).
- Data keys:
  - `mean_arterial_pressure` (patients,) float: mean arterial pressure of each patient, in mmHg
  - `central_venous_pressure` (patients,) float: central venous pressure of each patient, in mmHg
  - `co_thermodilution` (patients,) float: cardiac output of each patient measured by thermodilution, in L/min
  - `co_fick` (patients,) float: cardiac output of each patient measured by the Fick method from expired-gas oxygen uptake, in L/min
- Sizes: {"patients": 100}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): line 50: `x = cot`
  - R-squared of the regression of systemic vascular resistance SVR = 80 * (MAP - CVP) / co_thermodilution on the same co_thermodilution, compared with 0.25 (`>=`). Parameters: the factor 80; none else numeric in the source. Documented in ARC81 (a variable that contains the other directly).
- **Fixed body, the correction** (`fixed_body.py`): line 50: `x = cof`
  - R-squared of the regression of the same SVR on the independently measured co_fick, compared with the same 0.25 (`>=`). Generic remedy, not stated in the abstract.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Share of variance of calculated resistance explained by an independently measured cardiac output.

## 5. Allowed-guard minimum
2 patients, non-finite values (a zero thermodilution output gives a non-finite resistance), zero variance of resistance or of the cardiac output used.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-036 types ['bool'] max_time_s 0.00011`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
none. The correction is not verified in the source text (abstract only), as the private note says.
