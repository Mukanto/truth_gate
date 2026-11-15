"""Scratch: writes cases/<id>/CASE.md from ASSIGNMENT.json, PRIVATE.json, the pre-check logs and the texts below.
Reads logs only; never runs a case file."""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
PRIV = {r["local_id"]: r for r in json.load(open(ROOT / "PRIVATE.json", encoding="utf-8"))}
LOG1 = (ROOT / "work" / "precheck_fixed_log_run1.txt").read_text(encoding="utf-8")
LOG2 = (ROOT / "work" / "precheck_fixed_log_run2_final.txt").read_text(encoding="utf-8")


def block(log, case):
    m = re.search(r"^" + case + r" .*?(?=^B6-\d\d |\Z)", log, re.S | re.M)
    return m.group(0).rstrip()


def timing(case):
    b = block(LOG2, case)
    m = re.search(r"timing t=([\d.]+) ms\s+g=([\d.]+) ms\s+S=(\d+)\s+estimate=([\d.]+) s", b)
    return m.groups()


READ = {
    "LAZ18": "full text (PMC5902037 via PMC and Europe PMC) by the part 1 author, see LOG.md 'Sources read and how'",
    "NIE11": "abstract only (Europe PMC record, PMID 21878926; full text not open) by the part 1 author, see LOG.md",
    "HUR84": "full PDF text (extracted in memory with pypdf) by the part 1 author, see LOG.md",
    "LAZ10": "full text (Europe PMC XML, PMC2817684) by the part 1 author, see LOG.md",
    "MAK19": "full text (Europe PMC XML, PMC6785265) by the part 1 author, see LOG.md",
}

QUOTE = {
    "B6-01": 'LAZ18, section "Animal experiments": "animals in the same litter are randomised together, the treatment is applied to all animals simultaneously, and it is unreasonable to assume that animals in a womb do not influence each other."',
    "B6-02": 'LAZ18, section "Cell culture experiments": "treatments are applied simultaneously to all cells in a well, not independently to each cell ... Thus, a well, culture dish, or another plastic container is the appropriate EU for cell culture experiments."',
    "B6-03": 'LAZ18, section "Slice preparations and histological samples": "The EU is the animal and the sample size (N) is the number of animals. Multiple histological sections, neurons per section, spines per neuron, and so on, are all subsamples as they have been randomised together ..."',
    "B6-04": 'LAZ18, section on the three criteria of an experimental unit (cages, drinking-water example): "We expect animals in a cage to influence each other on many relevant variables, from behaviour to microbiomes." Housing 2 per cage maximises "the number of cages (which are now the EUs)".',
    "B6-05": 'NIE11, abstract: "researchers conclude that effects differ when one effect is significant (P < 0.05) but the other is not (P > 0.05)."',
    "B6-06": 'NIE11, abstract: "researchers conclude that effects differ when one effect is significant (P < 0.05) but the other is not (P > 0.05)."',
    "B6-07": 'NIE11, abstract: "In theory, a comparison of two experimental effects requires a statistical test on their difference."',
    "B6-08": 'HUR84, section on types of pseudoreplication, p. 205 (sacrificial pseudoreplication): "... where the two or more samples or measurements taken from each experimental unit are treated as independent replicates (Fig. 5B)."',
    "B6-09": 'HUR84, pp. 204-205 (temporal pseudoreplication): "... the multiple samples from each experimental unit are not taken simultaneously but rather sequentially over each of several dates. Dates are then taken to represent replicated treatments and significance tests are applied."',
    "B6-10": 'LAZ10, Introduction/Methods and "How to check reported values": ten rats, three consecutive days of rotarod tests; the reported t28 = 2.1 should have 5 + 5 - 2 = 8 degrees of freedom.',
    "B6-11": 'LAZ10, Background and Table 1: "If multiple observations are taken from each rat, then observations within each rat are not independent and therefore all of the observations cannot be summed to give a total sample size." Table 1 gives the summary-measure analysis as the solution.',
    "B6-12": 'MAK19, section "Interpreting comparisons between two effects without directly comparing them": the intervention is "significant" in one condition and the control "not significant"; "This type of erroneous inference is very common but incorrect." (Figure 1A: two groups of 20, a correlation significant in one and not in the other.)',
}

MAP = {
    "B6-01": ("Faulty: Student two-sample t test (pooled variance, df = 158) on all 160 pup values, each pup a replicate (N = dams x pups); two-sided p < 0.05 and exposed mean higher. Fixed: one value per dam (mean over the pups of the dam, LAZ18 'reduce the data to a single value for each EU'), the same pooled two-sample t test on the 20 dam means (df = 18). The only code difference is the two lines that build x and y (`.ravel()` versus `.mean(axis=1)`).",
              "Fixed: difference between the exposed and control groups in the mean of dam-level mean activity, dam as replicate. Faulty: difference between group means of pup-level activity, pup as replicate."),
    "B6-02": ("Faulty: Welch two-sample t test on the cell-level 0/1 responses (cells as replicates, 1800 values; equivalent to the two-proportion z test of the note to within the t/normal difference at about 1800 df), two-sided p < 0.05 and treated proportion higher. Fixed: proportion of responding cells per well, the same Welch test on the 12 well proportions (LAZ18 'reduce the data to a single value for each EU'). The only code difference is the two lines that build x and y.",
              "Fixed: difference between treated and untreated groups in the mean well-level response proportion, well as replicate. Faulty: difference between group-level pooled cell proportions, cell as replicate."),
    "B6-03": ("Faulty: ordinary least squares slope of all 1200 neuron-level spine densities on the dose of the animal (dose repeated for the 100 neurons of an animal), slope t test with df = 1198, two-sided p < 0.05 and slope positive. Fixed: spine density averaged over sections and neurons per animal, slope of the 12 animal means on dose, t test with df = 10. The only code difference is the two lines that build x and y.",
              "Fixed: slope of animal-level mean spine density on dose, animal as replicate. Faulty: slope of neuron-level spine density on dose, neuron as replicate."),
    "B6-04": ("Faulty: Welch two-sample t test on all 80 animal-level weight gains, animals as replicates, two-sided p < 0.05 and treated mean lower. Fixed: mean weight gain per cage (2 animals), the same Welch test on the 40 cage means (cage as experimental unit). The only code difference is the two lines that build x and y.",
              "Fixed: difference in group means of cage-level mean weight gain, cage as replicate. Faulty: difference in group means of animal-level weight gain, animal as replicate."),
    "B6-05": ("Faulty: within-group paired t tests of post minus pre (one-sample t test of the change scores) in the trained group and in the control group; the claim is taken to hold when the trained group's mean change is positive with p < 0.05 and the control group's change has p >= 0.05 (the NIE11 'significant here, not there' rule). Fixed: two-sample (pooled) t test of the difference between the groups' mean change scores, two-sided p < 0.05 and trained mean change larger (the test of the interaction).",
              "Fixed: difference between groups in mean change (post minus pre). Faulty: the pair of within-group mean changes, each tested against zero, with the decision based on the pattern of their significance."),
    "B6-06": ("Faulty: per-subject least-squares slope of reaction time on session (sessions in order), one-sample t test of the slopes within the healthy group and within the patient group; holds when the healthy mean slope is negative with p < 0.05 and the patient group's p >= 0.05. Fixed: pooled two-sample t test of the per-subject slopes, healthy versus patient, two-sided p < 0.05 and the healthy mean slope more negative. The per-subject slope step is identical in the twins.",
              "Fixed: difference between groups in the mean per-subject slope of reaction time on session. Faulty: the two within-group mean slopes, each tested against zero, compared by the pattern of significance."),
    "B6-07": ("Faulty: for each region the one-sample t test of the subject-wise task-minus-rest signal change against zero; holds when region A's mean effect is positive with p < 0.05 and region B's effect has p >= 0.05. Fixed: paired t test of the within-subject difference of the two signal changes (one-sample t on (task_a - rest_a) - (task_b - rest_b)), two-sided p < 0.05 and the mean difference positive.",
              "Fixed: mean across subjects of the within-subject difference between the effect in region A and the effect in region B. Faulty: the two region-wise mean effects, each tested against zero, compared by the pattern of significance."),
    "B6-08": ("Faulty: Welch two-sample t test on all 80 sample densities, samples as replicates, two-sided p < 0.05 and treated mean lower. Fixed: mean density per tank, the same Welch test on the 8 tank means (tank as experimental unit). The only code difference is the two lines that build x and y.",
              "Fixed: difference in group means of tank-level mean density, tank as replicate. Faulty: difference in group means of sample-level density, sample as replicate."),
    "B6-09": ("Faulty: two-sided Mann-Whitney U test (normal approximation with tie correction and continuity correction) on all 144 plot-by-date abundances, each a replicate of its treatment. Fixed: abundance averaged over dates per plot, the same Mann-Whitney test on the 12 plot means. Holds when the treated rank sum is higher and |z| exceeds the two-sided 5% critical value 1.959963984540054. The only code difference is the two lines that build x and y.",
              "Fixed: location shift (Mann-Whitney probability) of plot-level time-averaged abundance between treated and control plots, plot as replicate. Faulty: the same shift tested on plot-by-date observations, date-sample as replicate."),
    "B6-10": ("Faulty: two-tailed pooled two-sample t test on all 30 rat-by-day latencies (df 28, as in the LAZ10 example), treated mean higher, p < 0.05. Fixed: mean latency over the 3 days per rat (LAZ10 summary-measure analysis), the same pooled t test on the 10 rat means (df 8). The only code difference is the two lines that build x and y.",
               "Fixed: difference between group means of rat-level mean latency, rat as replicate. Faulty: difference between group means of rat-by-day latency, observation as replicate."),
    "B6-11": ("Faulty: Pearson correlation over all 160 subject-by-day pairs with its t test on df = 158 (each pair a replicate), two-sided p < 0.05 and r positive. Fixed: mean heart rate and mean cortisol per subject over the days, Pearson correlation of the 16 subject means with its t test on df = 14. The only code difference is the two lines that build x and y.",
               "Fixed: between-subject Pearson correlation of subject-level means. Faulty: Pearson correlation over subject-by-day observations (mixing within-subject and between-subject variation), tested with N = subjects x days."),
    "B6-12": ("Faulty: Pearson correlation and its t test (df = n - 2) separately in group A and in group B; holds when group A's correlation is positive with p < 0.05 and group B's has p >= 0.05. Fixed: Fisher z test of the difference of the two correlations, z = (atanh r_A - atanh r_B) / sqrt(1/(n_A - 3) + 1/(n_B - 3)), two-sided p < 0.05 (|z| > 1.959963984540054) and r_A > r_B. The two group correlations are computed by the same code in the twins.",
               "Fixed: difference between group A's and group B's Pearson correlations. Faulty: the two group-wise correlations each tested against zero, compared by the pattern of significance."),
}

GUARDS = {
    "B6-01": "2 dams per group; non-finite values; zero pooled variance (zero standard error).",
    "B6-02": "2 wells per group, at least 1 cell per well; non-finite values; zero standard error (both groups without variation).",
    "B6-03": "3 animals; non-finite values; zero variance of dose; zero residual variance.",
    "B6-04": "2 cages per group; non-finite values; zero standard error.",
    "B6-05": "2 subjects per group; non-finite values; zero variance (of the change scores in the pooled test; of a group's change scores in the faulty one-sample tests).",
    "B6-06": "2 subjects per group and 2 sessions; non-finite values; zero variance of the slopes (pooled, or within a group for the faulty one-sample tests).",
    "B6-07": "2 subjects; non-finite values; zero variance (of the difference in the fixed criterion; of a region's effect in the faulty one).",
    "B6-08": "2 tanks per group; non-finite values; zero standard error.",
    "B6-09": "1 plot per group (the rank-sum statistic is defined from 1 per group); non-finite values; zero rank variance (all values equal).",
    "B6-10": "2 rats per group; non-finite values; zero pooled variance.",
    "B6-11": "3 subjects; non-finite values; zero variance of either variable.",
    "B6-12": "4 participants per group (Fisher z standard error needs n - 3 > 0; the same guard in the faulty twin); non-finite values; zero variance of either score within a group.",
}

EXTRA_DEV = {
    "B6-02": "The note names a two-proportion z test for the faulty criterion; the faulty criterion here applies the same Welch t function as the fixed one to the cell-level 0/1 responses, so that the twins differ only in the unit (cell versus well). The two tests are numerically near-identical at 1800 values. The error (cells as replicates, N = wells x cells) and every parameter (alpha 0.05, two-sided, treated higher) are those of the note.",
    "B6-09": "The note's guard minimum 'at least 2 plots per group' is lowered to 1 plot per group, because PREREG_PHASE_C section 2 allows no more than the smallest size at which the statistic is defined (the rank-sum statistic exists from 1 per group). Never reached in the skeleton (6 plots per group). Both twins use the normal approximation with tie and continuity corrections (6 versus 6 plot means in the fixed criterion).",
    "B6-12": "The faulty twin uses the same 4-per-group guard as the fixed one (the note's 'same guards in both twins'), although its own Pearson tests need only 3. Never reached in the skeleton (20 per group).",
    "B6-05": "The faulty rule does not constrain the direction of the control group's change (only p >= 0.05), as NIE11 describes the pattern.",
    "B6-06": "The faulty rule does not constrain the direction of the patient group's slope (only p >= 0.05).",
    "B6-07": "The faulty rule does not constrain the direction of region B's effect (only p >= 0.05).",
}

SKEL_OBS = {
    "B6-12": "Observation on the skeleton (no change requested): the fixed criterion holds under the declared control 'permute_group_labels' in 50/1000 samples (0.050), above the one-sided 0.025 expected for a pure null; the permuted groups mix the two correlation structures of plus, so this may reflect the skeleton's control; recorded as is.",
    "B6-07": "Observation: the declared control (region labels swapped in half the subjects) makes the fixed criterion hold in 8/1000 samples (0.008); plus 0.902, minus 0.033.",
}

HELPER = "The p value of Student's t is computed with a numpy-only incomplete-beta helper written inside the criterion body (no new import); it was tested against `scipy.stats.t.sf` on 2238 points (largest relative error 3.9e-11, `work/helper_test_log.txt`)."
CONST = "Two-sided 5% normal critical value used as a constant: 1.959963984540054."
PNOTE = {c: "No randomness is used by either criterion (no `rng`); both are deterministic. " + HELPER for c in PRIV}
PNOTE["B6-09"] = "No randomness is used by either criterion (no `rng`); both are deterministic. The test is a z test (normal approximation), so no t-distribution helper is needed; " + CONST
PNOTE["B6-12"] = "No randomness is used by either criterion (no `rng`); both are deterministic. The faulty criterion uses the numpy-only Student t helper (tested as below); the fixed criterion is a z test. " + HELPER + " " + CONST
PNOTE["B6-02"] = PNOTE["B6-02"]

for case in sorted(PRIV):
    a = json.load(open(ROOT / "cases" / case / "ASSIGNMENT.json", encoding="utf-8"))
    pr = PRIV[case]
    t, g, S, est = timing(case)
    br = a["brief"]
    keys = "\n".join(f"  * `{k['key']}`, shape {k['shape']}, {k['dtype']}: {k['meaning']}" for k in br["data_keys"])
    md = f"""# {case} (world {a['world_id']})

## 1. Identification
Case id {case}; world id {a['world_id']}; class {a['class']}; subtype {a['subtype']}; source key {a['source']}; mechanism tag `{pr['mechanism_tag']}`; statistic family `{pr['statistic_family']}`.

## 2. Source and documenting passage
{QUOTE[case]}

Read by: {READ[a['source']]}. The part 2 author did not fetch any URL for this case (the private note's passage was used; no source was re-read).

## 3. The brief (as in ASSIGNMENT.json)
Claim: {br['claim']}

Data keys:
{keys}

Sizes: {br['sizes']}

## 4. Mapping
{MAP[case][0]}

Estimand line. {MAP[case][1]}

Allowed-guard minimum (same in both twins): {GUARDS[case]}

{PNOTE[case]}

## 5. Pre-checks of the fixed criterion (plain Python, never Truth_Gate; the faulty criterion was never run)
Number of revisions of the fixed criterion: 0. The twin check `work/verify_twins.py` (text and AST only) confirmed that both files equal the skeleton outside the body, that the body reads no module-level name except `np`, and that it has no import.

Run 1 (400 samples per stream, seed 20261115):
```
{block(LOG1, case)}
```
Run 2, final structure (1000 samples per stream, seed 20261115):
```
{block(LOG2, case)}
```
Each line gives the share of samples on which the fixed criterion returned True (None counted separately) on plus, minus, the declared control applied to plus samples, a noise probe (normal values, fair coin for bool), an all-zero probe (20 samples) and, where declared, the shuffle probe; the scipy line counts disagreements between the fixed criterion and an independent scipy implementation of the same decision on plus and minus samples. The noise and zero probes were built by hand from the description in `agent_docs/GATE.md`.

## 6. Timing (final fixed criterion)
t = {t} ms (mean of 100 calls on plus samples); g = {g} ms (mean of 100 plus generations); S = {S} (worlds + controls + premises + relational pairs, plus 2); estimate 2 x 200 x (S + 1) x (t + g) = {est} s (limit 900 s). No timing remedy needed.

## 7. Deviations, problems, skeleton requests
{EXTRA_DEV.get(case, 'No deviation from the private note beyond the points above.')}
{SKEL_OBS.get(case, '')}
Skeleton requests: none. SIZE REQUEST: none.
"""
    (ROOT / "cases" / case / "CASE.md").write_text(md, encoding="utf-8")
    print("CASE.md", case, t, g, S, est)
