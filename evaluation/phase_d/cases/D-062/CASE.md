# CASE D-062 (author-local id B3A-05)

## 1. Case
- Case id: D-062 (brief author's local id B3A-05)
- Class: B-3, coupling by construction (half A)
- Tag: ratio-shared-denominator; statistic family: proportion; role pair (PEA97 pair 2 of 3)

## 2. Source and documenting passage
- Source key: PEA97
- Passage: 'The particular case that is likely to occur is when u and v are indices with the same denominator for the correlation of the indices seems at first sight a very plausible measure of organic correlation.' (abstract, OpenAlex OCR text)
- Read: Read by the brief author in the abstract (OpenAlex OCR text, `fetched/pea97.json`); the abstract is the whole readable text. I fetched nothing online.

## 3. Brief
- Claim: In at least 60% of the species, femur length and humerus length are positively associated after accounting for body length: within the species, the partial correlation between femur length and humerus length, given body length, is at least 0.2.
- Data keys:
  - `femur` (species, individuals) float: femur length of each individual sampled in each species, in mm
  - `humerus` (species, individuals) float: humerus length of each individual sampled in each species, in mm
  - `body_length` (species, individuals) float: head-and-body length of each individual sampled in each species, in mm
- Sizes: {"species": 12, "individuals": 30}

## 4. Mapping
- **Faulty body, the error** (`faulty_body.py`): lines 72-74: `with np.errstate(divide='ignore', invalid='ignore'):` ... `b = ys / zs`; line 79: `r = _corr(a, b)`
  - Within each species the Pearson correlation between femur/body_length and humerus/body_length (common denominator); the share of species with correlation >= 0.2 compared with 0.6 (`>=`). Parameters: none numeric in the source; both thresholds are the claim's. Documented in PEA97 (passage above).
- **Fixed body, the correction** (`fixed_body.py`): line 72: `a = xs`; line 73: `b = ys`; line 78: `r = _partial_corr(a, b, zs)`
  - Within each species the partial correlation of femur and humerus given body_length (`_partial_corr`), same per-species threshold 0.2 and share threshold 0.6.
- Everything else (loading, finite and size guards, zero-variance guards, the comparison and its threshold, return values) is identical in the two files; the diff between them is only the lines above (checked with `diff`).
- **Estimand:** Share of species in which the association of the two bones, net of body length, reaches 0.2.

## 5. Allowed-guard minimum
Per species: fewer than 3 individuals (the array has fewer than 3 columns: None), non-finite value, zero variance: the species is not counted; None when no species can be counted (or there are no species). The share is taken over the counted species. Private note: same, with 4 individuals.

## 6. Runs of the fixed body
Fixed body only (the faulty body was never run): (1) form check `work/check_form.py` (AST, nothing executed), OK. (2) Smoke run, `work/run_fixed.py`: 3 independent random arrays with the brief's keys, shapes and dtypes; result types and maximum time below. (3) Direction run: one array built so that the fixed estimand clearly meets the claim and one that clearly does not (to confirm signs and direction, not a rate): output True and False respectively. Output saved in `work/run_fixed_output.txt`.
- Smoke result (3 arrays): `D-062 types ['bool'] max_time_s 0.00111`
- Fixed-body revisions: 0

## 7. Deviations from the private note, and problems
Minimum 3 individuals per species instead of 4 (partial correlation is defined at 3). The share's denominator is the number of counted species (as in the note).
