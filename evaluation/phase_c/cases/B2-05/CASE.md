# CASE B2-05

## 1. Identity
Case id B2-05; world id C51; class B-2; subtype L3.1; source key KAP23.

## 2. Source and documenting passage
KAP23 Section 2.4, L3.1 'Temporal leakage' ('data from the future'); Appendix C: shuffled k-fold cross-validation lets the training data contain data from a later date than the test data (quotes as returned by the fetch tool in part 1).

Who read it and how: KAP23 (Kapoor and Narayanan 2023). Read by the part-1 brief author (full text through the fetch tool's summary of https://ar5iv.labs.arxiv.org/html/2207.07048; the wording returned by that tool was not verified word for word). I (part 2) did not re-read it: the only URL I fetched, the VAR06 page, returned a reCAPTCHA page.

## 3. The brief (as in ASSIGNMENT.json)
```json
{
  "id": "C51",
  "claim": "A regression on the 8 weekly drivers explains at least 30% of the variance of weekly demand in later weeks (R-squared of at least 0.30).",
  "data_keys": [
    {
      "key": "drivers",
      "shape": "(weeks, drivers)",
      "dtype": "float",
      "meaning": "8 weather and calendar drivers of each week, weeks in chronological order"
    },
    {
      "key": "demand",
      "shape": "(weeks,)",
      "dtype": "float",
      "meaning": "demand observed in that week"
    }
  ],
  "sizes": "weeks = 400; drivers = 8"
}
```

## 4. Mapping
Faulty: shuffled 5-fold cross-validation (random fold assignment irrespective of time) of an ordinary least-squares regression of demand on the 8 drivers; R-squared (1 - SSE/SST about the mean of the scored weeks) pooled over the held-out weeks. Fixed: the same regression and statistic with chronological evaluation: 6 contiguous blocks, block j (j = 1..5) predicted from a fit on the preceding blocks only; R-squared over the 5 scored blocks. Threshold 0.30.

Estimand line. Faulty: R-squared on weeks surrounded in time by weeks used to fit. Fixed: R-squared on weeks later than all weeks used to fit.

Allowed-guard minimum used. Both: fitting set larger than the number of drivers plus 1; non-finite values give None; zero variance of the scored demand gives None (and fixed: fewer than 2 scored weeks gives None).

## 5. Pre-checks of the fixed criterion (plain Python, scratch scripts in work\; the faulty criterion was never run, only syntax-checked)
n = 100: plus 99, minus 0, control 0, noise 0, zeros None 100. Final, n = 200: plus 195/200 (0.975), minus 0/200, control 0/200, noise 0/200, zeros 200 None.

Number of revisions of the fixed criterion: 0.

## 6. Timing (final fixed criterion)
t = 0.0004 s (mean of 200 calls on plus samples), g = 0.0010 s (mean plus generation), S = 5 (2 worlds + 1 control(s)/relational pair(s) + 2 probes), estimate 2 x 200 x (S + 1) x (t + g) = 3 s (limit 900 s). No size request needed.

## 7. Deviations, problems, skeleton requests
With a linear regression and drivers that do not carry demand information in minus, shuffled folds can hardly leak, so the faulty criterion may behave like the fixed one in the declared worlds (not tested). Linear regression is what the note names.

Skeleton requests: none.

## Designer lines (PREREG_PHASE_C §3; added by the designer after the fidelity audit)

- Overlap with Phase B: yes, Phase B case B2-10.
- Mechanism tag / statistic family (private note): L3.1 / R-squared.
- Allowed-guard minimum (private note): at least 2 weeks in the scored block with non-zero variance of demand (smallest size at which R-squared is defined); fitting block larger than the number of drivers plus 1.
- Size ratio (brief size to source size): source states none.
- The estimand line is in item 4 (criterion author).
