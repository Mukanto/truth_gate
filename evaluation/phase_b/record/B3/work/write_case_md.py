"""Writes CASE.md for each B-3 case (run last, after criteria and pre-checks are final)."""
import json
import sys

ROOT = r"C:\Users\user\AppData\Local\Temp\claude\e3156104bf704008\a94a39de-e61e-4069-8597-c7836ecd2de0\scratchpad\phase_b\B3\cases"

Q_ARC1 = ("ARC81, Europe PMC abstract (PMID 7212790): \"Type 2 coupling is the functional relationship between two calculated variables "
          "which have one or more common component variables.\" \"The common problem in each type of mathematic coupling is that one variable "
          "either directly or indirectly contains the whole or components of the second variable.\"")
Q_ARC3 = ("ARC81, Europe PMC abstract (PMID 7212790): \"Type 3, the most common type of mathematic coupling, is direct algebraic coupling "
          "between two variables, when one or more of the variables is derived and/or calculated.\"")
Q_ARC4 = ("ARC81, Europe PMC abstract (PMID 7212790): \"Type 1 coupling involves directional changes in two variables which are mathematically "
          "coupled.\" (together with the Type 2 sentence on common component variables)")
Q_ARC_READ = ("The earlier author read the abstract in full on Europe PMC; the full text was not read by anyone. The clinical settings "
              "(Fick VO2/DO2, SVR and cardiac output, right-ventricular volume and ejection fraction, dobutamine) are applications of "
              "the documented principle recalled from background knowledge, not quotations of the abstract.")
Q_PEA_A = ("PEA97 p. 490-491 (archive.org OCR copy of Proc. R. Soc. 60:489-498): \"Form the proper fractions x/y and z/y for each triplet, "
           "and correlation will be found between these indices.\" For femur/humerus and tibia/humerus: \"a correlation of about 0.4 to 0.5 "
           "between these indices had the bones been sorted absolutely at random.\"")
Q_PEA_B = ("PEA97, Proposition III (OCR copy; section (4) 'To find the coefficient of correlation of two indices'): the OCR text reads "
           "\"The particular case that if likely to occur is when u and v are indices with the same denominator\" (sic, OCR 'if' for 'is'); "
           "the formula is given for x1/x3 and x2/x3.")
Q_PEA_READ = ("The earlier author read the full text of Pearson 1897 via the archive.org OCR copy (saved in src/pea.txt; I re-checked the "
              "quoted lines there). The settings other than skeletal indices are later applications of Proposition III recalled from "
              "background knowledge, not in Pearson 1897.")
Q_KRO = ("KRO93, abstract (IDEAS/RePEc): \"The consequences of using a single ratio as either the dependent or one of the independent variables "
         "in a multiple-regression analysis are described. It is shown that the use of ratios in regression analyses can lead to incorrect or "
         "misleading inferences.\"")
Q_KRO_READ = ("The earlier author read the abstract in full; the JSTOR full text was not read by anyone. The specific mechanisms (predictor "
              "correlated with the denominator, outcome related to the denominator) and the correction used here (ratio-free regression "
              "with the denominator as a covariate) are recalled from background knowledge of Kronmal's argument.")

CASES = {}

CASES["B3-01"] = dict(
    q=Q_ARC1, read=Q_ARC_READ, rev=0,
    mapping=("Faulty: oxygen consumption is obtained by the Fick calculation VO2 = CO x Hb x 13.4 x (SaO2 - SvO2) (13.4 = 1.34 mL O2 per g Hb "
             "x 10; the standard constant) and Pearson-correlated with delivery DO2 = CO x Hb x 13.4 x SaO2, threshold r >= 0.5 as in the brief. "
             "The two derived variables contain the same measured components (cardiac output, haemoglobin, SaO2) and so share their "
             "measurement errors: the type 2 coupling of ARC81 (common component variables). Fixed: the same Pearson statistic and threshold, "
             "with consumption taken from the independently measured expired-gas value vo2_expired, whose error is not shared with the "
             "delivery terms (the correction named in the earlier author's note); the Fick lines are the only thing removed."),
    pre=("200 plus samples: holds 190 (0.950). 200 minus: 0 (0.000). Control permute_vo2_expired on plus: 0/200. Noise probe (i.i.d. N(0,1), "
         "same shapes): 0/200. Zeros probe: 5/5 UNDEFINED (None, zero variance guard). Deterministic: yes."),
    dev="None.", rate="")

CASES["B3-02"] = dict(
    q=Q_ARC3, read=Q_ARC_READ, rev=1,
    mapping=("Faulty: SVR = 80 x (MAP - CVP) / CO_thermodilution, then Spearman rank correlation of SVR with the same thermodilution output "
             "(threshold <= -0.4). The output measured with error appears in the denominator of the derived variable and again as the "
             "other variable (ARC81 type 3, direct algebraic coupling), so error in CO produces a negative association by itself. Fixed: "
             "same SVR (from thermodilution CO), same Spearman statistic and threshold, correlated with the separately measured Doppler "
             "output co_doppler, whose error is independent."),
    pre=("200 plus: holds 198 (0.990). 200 minus: 0. Control permute_resistance: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. "
         "Deterministic: yes."),
    dev=("One revision after the first pre-check: the division is wrapped in np.errstate (RuntimeWarning on 0/0 in the zeros probe). "
         "No change of values or decisions (rates identical before and after)."), rate="")

CASES["B3-03"] = dict(
    q=Q_ARC3, read=Q_ARC_READ, rev=1,
    mapping=("Faulty: end-diastolic volume index computed as stroke volume index / rvef (both from the thermodilution catheter), then the "
             "standardised slope (both z-scored) of that volume on rvef, threshold <= -0.4. The volume contains the ejection fraction as its "
             "denominator and so shares its measurement error with the regressor (ARC81 type 3). Fixed: the same standardised slope and "
             "threshold using the radionuclide end-diastolic volume index, an independent measurement. The brief does not name which volume "
             "key the criterion must use; the faulty criterion uses the derived one, the fixed the independent one."),
    pre=("200 plus: holds 170 (0.850). 200 minus: 1 (0.005). Control permute_radionuclide_volume: 2/200 (0.010). Noise probe: 1/200 "
         "(0.005). Zeros probe: 5/5 UNDEFINED. Deterministic: yes."),
    dev="One revision: np.errstate around the division (see B3-02); no change in values.", rate="")

CASES["B3-04"] = dict(
    q=Q_ARC4, read=Q_ARC_READ, rev=0,
    mapping=("Faulty: per patient, change in consumption (Fick, from CO, Hb, SaO2, SvO2) and change in delivery (from CO, Hb, SaO2) between "
             "before and during infusion; R squared of the simple regression of the first on the second, threshold >= 0.25. The two change "
             "scores contain the same changes in cardiac output, haemoglobin and saturation (ARC81 type 1 and type 2 coupling of changes). "
             "Fixed: same R squared and threshold with the change in the independently measured vo2_expired in place of the Fick change."),
    pre=("200 plus: holds 180 (0.900). 200 minus: 2 (0.010). Control permute_vo2_expired: 3/200 (0.015). Noise probe: 2/200 (0.010). "
         "Zeros probe: 5/5 UNDEFINED. Deterministic: yes."),
    dev="None.", rate="")

CASES["B3-05"] = dict(
    q=Q_PEA_A, read=Q_PEA_READ, rev=1,
    mapping=("Faulty: Pearson correlation between femur/vertebral-column-length and tibia/vertebral-column-length, threshold >= 0.4. With "
             "independent absolute lengths and a varying common denominator the index correlation is about 0.4 to 0.5 at equal coefficients "
             "of variation (documented in Pearson 1897; here the humerus of the paper is replaced by the vertebral column, same structure). "
             "Fixed: Pearson partial correlation of femur and tibia lengths holding vertebral column length fixed (the partial correlation "
             "is the standard correction), same threshold 0.4. Scale: raw values, as in the faulty criterion."),
    pre=("200 plus: holds 200 (1.000). 200 minus: 34 (0.170). Control permute_tibia: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. "
         "Deterministic: yes."),
    dev=("One revision: np.errstate around the divisions (no change in values). Observation, not a change: in minus the fixed criterion "
         "holds in 17% of samples. The skeleton keeps a shared body-size factor and a noisy shared column length in minus, so even the "
         "partial correlation leaves a residual correlation (mean partial correlation 0.317, sd 0.083 over 400 minus samples, descriptive script "
         "work/estimates_fixed_stats.py), not far below the 0.4 threshold. Not bent."),
    rate="")

CASES["B3-06"] = dict(
    q=Q_PEA_B, read=Q_PEA_READ, rev=1,
    mapping=("Faulty: Spearman rank correlation of per-capita emissions (total / population) with per-capita GDP (total / population), "
             "threshold >= 0.5. Both indices share the population denominator (Pearson's Proposition III; the per-capita economic setting is "
             "a later application). Fixed: Spearman partial correlation (partial correlation of the ranks) of the two totals holding the "
             "rank of population fixed, same threshold 0.5. The earlier note proposed logs; ranks are used instead because logs of N(0,1) "
             "noise-probe data are undefined and would make the fixed criterion UNDEFINED under the probe."),
    pre=("200 plus: holds 200 (1.000). 200 minus: 0. Control permute_per_capita_emissions: 0/200. Noise probe: 0/200. Zeros probe: 5/5 "
         "UNDEFINED. Deterministic: yes."),
    dev=("One revision: np.errstate around the divisions. Deviation from the note: ranks instead of logs for the partial correlation (reason above)."),
    rate="")

CASES["B3-07"] = dict(
    q=Q_PEA_B, read=Q_PEA_READ, rev=1,
    mapping=("Faulty: standardised slope (both z-scored) of yield per hectare on fertilizer per hectare, threshold >= 0.3, both ratios built from "
             "totals divided by the same recorded area (shared denominator and its recorded error; Pearson's Proposition III applied to a "
             "regression). Fixed: standardised partial coefficient of fertilizer_total in the regression of yield_total on fertilizer_total "
             "and farm_area (all three z-scored, ordinary least squares with intercept), threshold 0.3: the ratio-free form with the "
             "denominator as covariate, in raw units as the faulty criterion."),
    pre=("200 plus: holds 145 (0.725). 200 minus: 31 (0.155). Control permute_yield_per_hectare: 13/200 (0.065). Noise probe: 0/200. Zeros "
         "probe: 5/5 UNDEFINED. Deterministic: yes."),
    dev=("One revision: np.errstate around the divisions. Observation, not a change: the fixed criterion fails in 27% of plus samples and "
         "holds in 15.5% of minus samples. The skeleton records the area with a 15% error, so the total fertilizer acts as a second proxy of the "
         "true area and the coefficient keeps a positive residual in minus; the fixed statistic over 400 samples has mean 0.390 (sd 0.148) in plus and 0.078 (sd 0.175) in minus "
         "(work/estimates_fixed_stats.py), against the 0.3 threshold. Not bent."),
    rate="")

CASES["B3-08"] = dict(
    q=Q_PEA_B, read=Q_PEA_READ, rev=1,
    mapping=("Faulty: R squared of the simple regression of peak power per kg on maximal oxygen uptake per kg, threshold >= 0.25; both "
             "ratios share the body-mass denominator and both fall with body size (Pearson's Proposition III; the body-mass setting is a "
             "later application). Fixed: squared partial correlation of peak_power and vo2max holding body_mass fixed, same threshold 0.25 "
             "and the same unsigned R squared."),
    pre=("200 plus: holds 113 (0.565). 200 minus: 3 (0.015). Control permute_power_per_kg: 3/200 (0.015). Noise probe: 0/200. Zeros probe: "
         "5/5 UNDEFINED. Deterministic: yes."),
    dev=("One revision: np.errstate around the divisions. Observation, not a change: the fixed criterion fails in 43% of plus samples. In "
         "the skeleton the size-independent correlation in plus is 0.5, so the squared partial correlation has mean 0.267 (sd 0.138 over 400 samples), "
         "about at the threshold; many samples fall below it. Not bent."),
    rate="")

CASES["B3-09"] = dict(
    q=Q_KRO, read=Q_KRO_READ, rev=1,
    mapping=("Faulty: standardised slope of infections per admission on beds (z-scored), threshold <= -0.3: a ratio as the dependent variable "
             "whose denominator (admissions) is proportional to the predictor, the situation Kronmal's abstract describes as leading to "
             "misleading inferences. Fixed: standardised coefficient of beds in the regression of infections on beds with admissions as a "
             "covariate (all z-scored), threshold <= -0.3: the ratio-free form."),
    pre=("200 plus: holds 99 (0.495). 200 minus: 33 (0.165). Control permute_beds: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. "
         "Deterministic: yes."),
    dev=("One revision: np.errstate around the division. Observation, not a change: the fixed criterion fails in about half of plus and "
         "holds in 16.5% of minus. In the skeleton admissions are almost proportional to beds (log error 0.15), so the two covariates are "
         "highly collinear and the standardised coefficient of beds is very variable: mean -0.363 (sd 0.372) in plus and 0.008 (sd 0.316) in "
         "minus over 400 samples (work/estimates_fixed_stats.py), against a threshold of -0.3. Not bent."),
    rate="")

CASES["B3-10"] = dict(
    q=Q_KRO, read=Q_KRO_READ, rev=1,
    mapping=("Faulty: standardised slope of systolic pressure on heart weight / body weight (z-scored), threshold >= 0.3: a ratio as predictor "
             "whose denominator (body weight) itself drives the outcome, so the ratio carries the body-weight effect (Kronmal 1993, ratio as "
             "an independent variable). Fixed: standardised coefficient of heart_weight in the regression of pressure on heart weight with "
             "body weight as a covariate, threshold >= 0.3."),
    pre=("200 plus: holds 200 (1.000). 200 minus: 5 (0.025). Control permute_relative_heart_weight: 7/200 (0.035). Noise probe: 3/200 "
         "(0.015). Zeros probe: 5/5 UNDEFINED. Deterministic: yes."),
    dev="One revision: np.errstate around the division; no change in values.", rate="")

CASES["B3-11"] = dict(
    q=Q_KRO, read=Q_KRO_READ, rev=1,
    mapping=("Faulty: Spearman correlation of occupants with energy use per square metre, threshold <= -0.3: a ratio with the floor-area "
             "denominator as outcome, while occupants grow with floor area (Kronmal 1993, ratio as dependent variable; the Spearman form and "
             "the building setting are this project's application). Fixed: Spearman partial correlation (partial correlation of the ranks) of "
             "energy_use and occupants holding floor_area fixed, same threshold -0.3."),
    pre=("200 plus: holds 1 (0.005). 200 minus: 0. Control permute_occupants: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. "
         "Deterministic: yes."),
    dev=("One revision: np.errstate around the division. Deviation from the note: ranks instead of logs (logs undefined on noise-probe data). "
         "Observation, not a change: the fixed criterion almost never holds in plus. In the skeleton the direct occupant effect on "
         "intensity is -0.12 log units per sd, so the partial rank correlation after holding area fixed has mean -0.125 (sd 0.090 over 400 plus "
         "samples; work/estimates_fixed_stats.py), well short of -0.3; most of the faulty statistic's strength in plus comes from the area-driven scale effect and the occupants-area "
         "link, which the skeleton also keeps in minus. This is the largest skeleton-side limit in the set: the correction cannot hold in plus. "
         "No skeleton request filed (the criterion could be written); the designer may want to know."),
    rate="")

CASES["B3-12"] = dict(
    q=Q_KRO, read=Q_KRO_READ, rev=1,
    mapping=("Faulty: R squared of the simple regression of the turnover rate (leavers / headcount) on payroll, threshold >= 0.1: ratio outcome "
             "whose denominator (headcount) grows with the predictor (Kronmal 1993; the firm setting and R squared are this project's "
             "application). Fixed: partial R squared of payroll in the regression of leavers on payroll and headcount (squared partial "
             "correlation of leavers and payroll holding headcount fixed), threshold >= 0.1."),
    pre=("200 plus: holds 1 (0.005). 200 minus: 7 (0.035). Control permute_payroll: 0/200. Noise probe: 0/200. Zeros probe: 5/5 UNDEFINED. "
         "Deterministic: yes."),
    dev=("One revision: np.errstate around the division. Observation, not a change: the fixed criterion almost never holds in plus. In the "
         "skeleton the true rate depends on headcount only, and payroll is headcount x a wage that is independent of the rate, so payroll "
         "carries no information about leavers beyond headcount even in plus (partial R squared mean 0.012, sd 0.020 over 400 plus samples); the claim is true in plus only through the denominator. "
         "No correction in Kronmal's ratio-free form can hold in plus. No skeleton request filed (the criterion could be written); the "
         "designer may want to know."),
    rate="")

TIMING = {
    "B3-01": (0.040, 0.053), "B3-02": (0.083, 0.032), "B3-03": (0.053, 0.028), "B3-04": (0.044, 0.073),
    "B3-05": (0.086, 0.026), "B3-06": (0.151, 0.023), "B3-07": (0.072, 0.021), "B3-08": (0.088, 0.023),
    "B3-09": (0.072, 0.035), "B3-10": (0.071, 0.018), "B3-11": (0.213, 0.039), "B3-12": (0.098, 0.048),
}
S = 5  # 2 worlds + 1 control + 0 premises + 0 relational + 2 probes

cases = sys.argv[1:] or sorted(CASES)
for c in cases:
    info = CASES[c]
    a = json.load(open(f"{ROOT}\\{c}\\ASSIGNMENT.json", encoding="utf-8"))
    t, g = TIMING[c]
    est = 2 * 200 * (S + 1) * ((t + g) / 1000.0)
    brief = json.dumps(a["brief"], indent=2, ensure_ascii=False)
    text = f"""# {c} ({a['world_id']})

## 1. Identity
Case id {c}, world id {a['world_id']}, class {a['class']}, subtype: none (B-2 subtypes only), source key {a['source']}.

## 2. Source and documenting passage
{info['q']}

Who read it, and how: {info['read']}

## 3. Brief (exactly as in ASSIGNMENT.json)
Claim: {a['brief']['claim']}

```json
{brief}
```

## 4. Mapping of the faulty and the fixed criterion
{info['mapping']}

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate, never the faulty file)
{info['pre']} Samples drawn with numpy default_rng seeds (plus 1000.., minus 5000.., control 9000.., noise 13000..); script
work/precheck_fixed.py. Number of revisions of the fixed criterion: {info['rev']}.

## 6. Timing
t = {t:.3f} ms (mean of 50 calls on plus samples), g = {g:.3f} ms (mean of 50 plus generations), S = {S} (2 worlds + 1 control + 0 premises
+ 0 relational pairs + 2 probes); estimate 2 x 200 x (S + 1) x (t + g) = {est:.2f} s (limit 900 s).

## 7. Deviations from the private note, problems, skeleton requests
{info['dev']} Skeleton requests: none.
"""
    with open(f"{ROOT}\\{c}\\CASE.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote", c)
