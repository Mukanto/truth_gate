"""Writes CASE.md for each case from BRIEFS/PRIVATE (text only)."""
import json
import os

H = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
briefs = {b['local_id']: b for b in json.load(open(os.path.join(H, 'BRIEFS.json'), encoding='utf-8'))}
priv = {b['local_id']: b for b in json.load(open(os.path.join(H, 'PRIVATE.json'), encoding='utf-8'))}
ids = json.load(open(os.path.join(H, 'CASE_IDS.json'), encoding='utf-8'))

CLASS = {k: ('B-1' if k in ('DEC-01', 'DEC-02', 'DEC-03', 'DEC-04', 'DEC-R1', 'DEC-R2') else 'B-6') for k in ids}

NOREAD = '; I did not re-read the source and fetched no URL'
PASSAGE = {
    'DEC-01': ('KRI09', '"Nonindependent selective analysis is incorrect and should not be acceptable in neuroscientific publications." Also the regional-activation simulation (ROI chosen by contrast A-D, contrast A-B with true value zero tested on the same data, 20 of 100 runs significant at p<0.05).', 'read by the brief author in the PMC full text through a summarising fetch (WebFetch)' + NOREAD),
    'DEC-02': ('VUL09', 'Abstract: more than half of 55 surveyed articles computed correlations voxel by voxel, then averaged only the voxels above a threshold; the reported correlations exceed what the reliabilities of the measures allow.', 'read by the brief author in the abstract through Europe PMC' + NOREAD),
    'DEC-03': ('MOR03', '"Any intervention aimed at a group or characteristic that is very different from the average will appear to be successful because of regression to the mean." (SOURCES_D)', 'read by the brief author in the PMC full text through a summarising fetch' + NOREAD),
    'DEC-04': ('BAR05', 'Abstract: the effect of regression to the mean "becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value".', 'read by the brief author in the publisher abstract only' + NOREAD),
    'DEC-05': ('NIE11', 'SOURCES_D: a difference between two effects claimed because one is significant and the other is not. Abstract (Europe PMC): in a review of 513 articles from five journals, 78 used the correct method and 79 the incorrect one.', 'read by the brief author in the abstract through Europe PMC' + NOREAD),
    'DEC-06': ('HUR84', 'Abstract as reproduced in search summaries: pseudoreplication is the use of inferential statistics to test for treatment effects where treatments are not replicated or replicates are not statistically independent.', 'read by the brief author as the abstract reproduced in search summaries (the full text is a scanned PDF and was not readable)' + NOREAD),
    'DEC-07': ('LAZ10', '"clearly the rat that the observation came from partly determines what that value is." (hierarchical example: 2 rats x 100 CA3 cells = 200 data points, only 2 rats are independent units)', 'read by the brief author in the Europe PMC full-text XML (first 100000 of 166051 characters)' + NOREAD),
    'DEC-08': ('LAZ18', '"If treatments are randomly and independently applied to an entity other than the individual animal, then the sample size is not the number of animals." (Animal experiments section)', 'read by the brief author in the PMC full text through a summarising fetch' + NOREAD),
    'DEC-R1': ('KRI10', '"The effect-size statistics need to be independent of the selection criterion" (PMC full text; a design in which half the data choose signal-carrying voxels and the other half estimate the signal).', 'read by the brief author in the PMC full text through a summarising fetch' + NOREAD),
    'DEC-R2': ('MAK19', '"circular analysis recruits the noise (inherent to any empirical data) to inflate the statistical outcome" (section on circular analysis: neurons binned by baseline activity, a significant interaction found although there is no overall change).', 'read by the brief author in the PMC full text (first 100000 of 204772 characters)' + NOREAD),
    'DEC-R3': ('MAK19', '"one should not infer that one correlation is greater than the other." (section on comparing two effects without a direct test: groups of 20 participants, an effect significant in one group but not the other, equal means, higher variance in one group)', 'read by the brief author in the PMC full text (first 100000 of 204772 characters)' + NOREAD),
    'DEC-R4': ('HUR84', 'Abstract as reproduced in search summaries; temporal pseudoreplication (repeated samples through time from the same unit) as described in secondary summaries of the paper.', 'read by the brief author as the abstract in search summaries and secondary summaries (the full text was not readable)' + NOREAD),
}

SF = ('The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta '
      'function (Lanczos log-gamma, continued fraction), because a body may import only numpy. ')

M = {}
M['DEC-01'] = dict(
    mapping=('Faulty (`D-061/faulty_body.py`): lines 116-125 carry the error. Lines 116-120 choose the voxels (one-sided one-sample t test of A - D across all 10 runs, df = 9, p < 0.001, the uncorrected primary threshold of the source\'s Example 1; the `0.001` is on line 120). Lines 123-125 then compute the proportion with mean A > mean B over the same 10 runs and compare it with 0.70. Selection and estimation use the same data. Parameters: p < 0.001, 10 runs, threshold 0.70 (claim); documented in the private note.\n\n'
             'Fixed (`D-061/fixed_body.py`): lines 116-132. The runs are split into even- and odd-indexed runs (line 116); voxels are chosen on one half (lines 121-125, t test with df = 4, same p < 0.001) and the proportion A > B is computed on the other half (lines 126-129); the two roles are swapped by the loop (line 118) and the two proportions averaged (line 132). Same helpers, same threshold, same proportion statistic.\n\n'
             'Estimand: the population proportion of voxels with expected A > expected B among voxels with expected A > expected D, estimated on runs independent of the choice of voxels.'),
    guard='1 voxel kept (non-empty selection). Also: non-finite values; zero variance of A - D in some voxel across the runs used (the t statistic is undefined). In the fixed body a direction with an empty selection is skipped and the other direction alone is used; None only if neither direction keeps a voxel.',
    dev='Runs are split by parity (even/odd), the form the source\'s correction takes, rather than the example "runs 0-4 / 5-9" of the private note (both are named there). "None if no voxel is kept in either direction" is read as: no voxel kept in either of the two directions (one empty direction is skipped, not a reason for None). The critical t is found by bisection of the hand-written t tail and equals p < 0.001. ' + SF + 'Problems: none.')

M['DEC-02'] = dict(
    mapping=('Faulty (`D-028/faulty_body.py`): lines 33-39 carry the error. Pearson r of every voxel with the trait over all 20 subjects (line 33), the 20 voxels with the largest r are kept (line 36; 20 is the claim\'s number), and their mean r, computed in the same subjects, is compared with 0.5 (line 39). Documented in the private note (VUL09 abstract: voxels thresholded on the correlation, then the correlations of the selected voxels averaged).\n\n'
             'Fixed (`D-028/fixed_body.py`): lines 31-49. Subjects are split into two halves (line 32); the top 20 voxels are chosen on one half (lines 39-42) and their mean r computed on the other (line 45); the halves are swapped by the loop (line 36) and the two mean r values averaged through Fisher z and back-transformed (lines 48-49), then compared with 0.5. Same helper `_corr_cols`, same k = 20, same threshold.\n\n'
             'Estimand: the mean population correlation with the trait of the 20 voxels chosen without using the subjects on which the correlation is estimated.'),
    guard='1 voxel selected; also non-finite values and zero variance (a voxel or the trait constant in the subjects used; correlation undefined). Fewer than 2 subjects (fewer than 2 per half in the fixed body) is treated as too small for a correlation.',
    dev='Fisher z is applied to the per-half mean r (the arithmetic mean over the 20 voxels of each half) and the two half values are averaged in z; the private note ("compute their mean r on the other 10; swap the halves and average (Fisher z averaged, back-transformed)") allows this and another reading (z-averaging all 40 voxel correlations); I kept the structure of the faulty body (mean r of 20 voxels). Halves are even/odd subject indices. Problems: none.')

M['DEC-03'] = dict(
    mapping=('Faulty (`D-047/faulty_body.py`): line 28 carries the error: the change of flagged patients is measured from the flagging measurement itself (`s[flag] - w[flag]`, screening minus week 12). Line 25 flags patients with screening >= 60 (the claim\'s threshold); line 29 compares the proportion with change >= 10 against 0.5. Documented in the private note (MOR03: groups far from the average improve by regression to the mean).\n\n'
             'Fixed (`D-047/fixed_body.py`): line 28 only: `e[flag] - w[flag]`, the entry score (a second pre-treatment measurement, not used for flagging) minus week 12. Everything else is identical (the flag is still the screening score).\n\n'
             'Estimand: the share of the flagged patients whose score fell by 10 or more from an independent pre-treatment measurement (the change after treatment among those flagged).'),
    guard='1 flagged patient (non-empty selection); non-finite values.',
    dev='none. Problems: none.')

M['DEC-04'] = dict(
    mapping=('Faulty (`D-069/faulty_body.py`): lines 27-34 carry the error. Thirds are cut among the treated patients only (line 29, percentiles 100/3 and 200/3 of the treated patients\' baselines; the private note says 33rd and 67th), and the top-third minus bottom-third mean reduction of the treated patients (reduction = baseline - follow-up, line 26) is compared with 3 mmHg (line 34), so the movement of extreme baselines toward the mean enters the contrast and there is no untreated reference. Documented in the private note (BAR05 abstract).\n\n'
             'Fixed (`D-069/fixed_body.py`): lines 27-37. Thirds over all patients (line 29), four cells (top/bottom third x treated/untreated, line 32), the drug-attributable reduction (treated minus untreated mean reduction) in the top and in the bottom third (lines 35-36), and the top-minus-bottom difference of these compared with 3 mmHg (line 37).\n\n'
             'Estimand: the difference between the top and bottom baseline thirds of the drug-attributable reduction (treated minus untreated), a treatment-by-baseline contrast.'),
    guard='1 patient in each cell needed (faulty: one in each of the treated top and bottom thirds; fixed: one in each of the four cells); non-finite values.',
    dev='"Thirds" are cut at the 100/3 and 200/3 percentiles (linear interpolation) with membership `<=` the lower and `>=` the upper cut; the private note says 33rd and 67th percentile, which I read as thirds. Problems: none.')

M['DEC-05'] = dict(
    mapping=('Faulty (`D-032/faulty_body.py`): lines 43-47 carry the error (with the helper `_z_pooled`, line 9): a pooled-variance two-sample z test of the drug-minus-vehicle difference in responder proportion within carriers and within non-carriers separately, each one-sided at 0.05 (z > 1.6448536269514722); the claim is declared supported when the carrier effect is significant and the non-carrier effect is not (line 47). Documented in the private note and in NIE11 (a difference between effects claimed because one is significant and the other is not).\n\n'
             'Fixed (`D-032/fixed_body.py`): lines 35-44: one one-sided z test at 0.05 of the difference of the two differences (carriers minus non-carriers), standard error from the four cell proportions (lines 39-43). Same critical value 1.6448536269514722.\n\n'
             'Estimand: the difference between the carrier effect and the non-carrier effect on the proportion scale.'),
    guard='1 participant in each of the four (carrier, drug) cells; zero variance (faulty: pooled variance zero in a stratum; fixed: the standard error is zero).',
    dev='The constant 1.6448536269514722 is the 0.95 quantile of the standard normal (the claim\'s 0.05 one-sided level); no numeric tail function is needed. Problems: none.')

M['DEC-06'] = dict(
    mapping=('Faulty (`D-012/faulty_body.py`): lines 20-35 carry the error: all 300 quadrats are pooled and treated as independent (lines 22-31); the difference of occupied proportions (fenced minus open, line 34) must be >= 0.10 and the pooled-variance two-proportion z test one-sided at 0.05 (z > 1.6448536269514722) significant (line 35). Parameters 0.10 and 0.05 come from the claim; the intra-plot correlation of 0.3 and the design effect are in the private note and are not used by the criterion. Documented in the private note (HUR84: replicates not statistically independent).\n\n'
             'Fixed (`D-012/fixed_body.py`): lines 108-118: occupancy per plot (line 110), Welch t test one-sided at 0.05 on the plot occupancies (helper `_welch`, defined at line 78), and the same rule (difference of mean plot occupancies >= 0.10 and p < 0.05, line 118).\n\n'
             'Estimand: the difference of mean plot occupancy (fenced minus open) with plots as replicates.'),
    guard='2 plots per group (fixed); at least one unit per group (faulty); zero variance (faulty: pooled proportion 0 or 1; fixed: both groups have zero variance, so the standard error is zero).',
    dev='"A zero variance" is read as a zero standard error of the difference (both groups constant); a single constant group with a varying other group still has a defined Welch statistic. ' + SF + 'Problems: none.')

M['DEC-07'] = dict(
    mapping=('Faulty (`D-046/faulty_body.py`): line 113 carries the error: the dose of each animal is repeated for each of its cells and the one-sided t test of the least-squares slope uses all 1000 cell values as replicates (df = 998). Helper `_slope_p` (shared, line 78) does the regression; line 116 applies p < 0.05. Documented in the private note and LAZ10 (the animal a cell comes from partly determines the value; 2 rats x 100 cells).\n\n'
             'Fixed (`D-046/fixed_body.py`): line 113 only: `_slope_p(x, y.mean(axis=1))`, the slope of the animal mean response on dose over the 10 animals (df = 8). Everything else is identical.\n\n'
             'Estimand: the slope of the animal mean response on dose with animals as replicates (the same expected slope in a balanced design).'),
    guard='3 units (cells in the faulty body, animals in the fixed body); non-finite values; zero variance of dose, or a zero residual variance (standard error zero).',
    dev=SF + 'The zero-residual guard (standard error zero) is my reading of "zero variance" for the test statistic. Problems: none.')

M['DEC-08'] = dict(
    mapping=('Faulty (`D-016/faulty_body.py`): line 112 carries the error: each dam\'s exposure is repeated for each of her pups and the Pearson correlation with the 56 pup scores is tested one-sided with df = 54 (`t = r sqrt(54/(1-r^2))`, helper `_corr_p`, shared, line 78). Line 115 applies p < 0.05. Documented in the private note and LAZ18 (the sample size is not the number of animals when treatment is applied to the litter).\n\n'
             'Fixed (`D-016/fixed_body.py`): line 112 only: `_corr_p(x, y.mean(axis=1))`, the correlation of exposure with the dam\'s mean pup score over the 14 dams (df = 12).\n\n'
             'Estimand: the correlation of exposure with litter mean score, dams as replicates.'),
    guard='3 units (pups in the faulty body, dams in the fixed body); non-finite values; zero variance of exposure or of the scores.',
    dev=SF + 'For a perfect correlation (1 - r^2 = 0) the helper takes t as infinite instead of dividing by zero. Problems: none.')

M['DEC-R1'] = dict(
    mapping=('Faulty (`D-033/faulty_body.py`): lines 33-39 carry the error: Pearson r of every voxel with intensity over all 60 trials (line 33), the 25 voxels with the largest r kept (line 36; 25 is the claim\'s number), their mean r from the same trials compared with 0.25 (line 39). Documented in the private note (KRI10: effect-size statistics must be independent of the selection criterion).\n\n'
             'Fixed (`D-033/fixed_body.py`): lines 31-49: trials split into even- and odd-indexed halves (line 32); the 25 voxels chosen on one half (lines 39-42), their mean r computed on the other (line 45), roles swapped (line 36), the two mean r averaged through Fisher z (lines 48-49) and compared with 0.25.\n\n'
             'Estimand: the mean population correlation with intensity of the 25 voxels chosen without the trials used for estimating it.'),
    guard='1 voxel selected; non-finite values; zero variance (a voxel or the intensity constant on the trials used). Fewer than 2 trials (fewer than 2 per half in the fixed body) is too small.',
    dev='Same readings as D-028: Fisher z on the per-half mean r; even/odd trial halves ("odd-numbered trials" in the note; the swap makes the base of the index irrelevant). Problems: none.')

M['DEC-R2'] = dict(
    mapping=('Faulty (`D-030/faulty_body.py`): lines 22-28 carry the error: one estimate of the baseline (the mean of all pre trials, line 22) both assigns the neuron to the below-8-Hz or at-least-8-Hz bin (line 24) and is the reference of the change (line 23, mean post > mean pre); the difference of the proportions of rising neurons (low bin minus high bin) is compared with 0.20 (line 28). Documented in the private note (MAK19: circular analysis with neurons binned by baseline).\n\n'
             'Fixed (`D-030/fixed_body.py`): lines 22-35: the pre trials are split into even- and odd-indexed halves (line 24); the bin comes from one half (line 28), the change is the mean post minus the mean of the other half (line 29), the same proportions and rule; the roles are swapped by the loop (line 27) and the two differences averaged (line 35).\n\n'
             'Estimand: the same difference of proportions with the bin assigned by one baseline estimate and the change measured from an independent one.'),
    guard='A non-empty bin (below 8 Hz and at least 8 Hz) is needed in both directions of the fixed body; non-finite values; at least 2 pre trials.',
    dev='"None if a bin is empty" is applied to either direction of the fixed body. "Even-numbered" and "odd-numbered" trials are the two parity classes of the trial index; the swap makes the base of the index irrelevant. Problems: none.')

M['DEC-R3'] = dict(
    mapping=('Faulty (`D-052/faulty_body.py`): lines 115-119 carry the error (helper `_t1_p`, line 78): a one-sample one-sided t test (mean improvement > 0, 0.05) in the young and in the old, and the claim is declared supported when the young test is significant and the old test is not (line 119). Documented in the private note and MAK19 (one effect significant in one group but not the other, no direct test of the difference).\n\n'
             'Fixed (`D-052/fixed_body.py`): lines 118-121: a Welch two-sample one-sided t test of the improvement (young minus old) at 0.05 (helper `_welch`, line 78), supported when p < 0.05.\n\n'
             'Estimand: the difference in mean improvement between young and old.'),
    guard='2 participants per group; non-finite values; zero variance (faulty: a group with zero standard deviation; fixed: standard error zero).',
    dev=SF + 'Problems: none.')

M['DEC-R4'] = dict(
    mapping=('Faulty (`D-021/faulty_body.py`): lines 20-35 carry the error: all 96 plot-date records are pooled and treated as independent; the difference of occupied proportions (fenced minus open) must be >= 0.15 and the pooled two-proportion z test one-sided at 0.05 (z > 1.6448536269514722) significant (line 35). Documented in the private note (HUR84: temporal pseudoreplication).\n\n'
             'Fixed (`D-021/fixed_body.py`): lines 108-118: occupancy per plot as the mean over its 12 dates (line 110), Welch t test one-sided at 0.05 on the plot occupancies (helper `_welch`, line 78), difference >= 0.15 and p < 0.05 (line 118).\n\n'
             'Estimand: the difference of mean plot occupancy with plots as replicates.'),
    guard='2 plots per group (fixed); at least one record per group (faulty); zero variance (faulty: pooled proportion 0 or 1; fixed: standard error zero).',
    dev='Same reading of "zero variance" as D-012. ' + SF + 'Problems: none.')

RUNS = {
    'DEC-01': 'self-generated array (1500, 10, 4) with 600 voxels whose A is shifted by 1.5 and Gaussian noise: True; pure-noise array: False; per run 3 timing calls plus 1 repeat call, 3.0 and 4.3 ms per call; repeated calls gave equal answers.',
    'DEC-02': 'self-generated Gaussian arrays (20, 1000) and (20,), null data: False; 0.4 ms per call (3 calls + 1 repeat, equal).',
    'DEC-03': 'self-generated latent-level data (600 patients): False; below 0.1 ms per call (3 calls + 1 repeat, equal).',
    'DEC-04': 'self-generated latent-level data with a drug effect of 5 mmHg (900 patients): False; 0.2 ms per call (3 calls + 1 repeat, equal).',
    'DEC-05': 'self-generated Bernoulli data (240 participants, drug effect 0.15 in both strata): False; below 0.1 ms per call (3 calls + 1 repeat, equal).',
    'DEC-06': 'self-generated Bernoulli occupancy (10 plots, 30 quadrats, 5 fenced): False; 0.1 ms per call (3 calls + 1 repeat, equal); the Welch p-value of `_welch` matched scipy.stats.ttest_ind (Welch, alternative greater) to 4e-16.',
    'DEC-07': 'self-generated random-intercept data with slope 0.2 (10 animals, 100 cells): True; 0.1 ms per call (3 calls + 1 repeat, equal); the slope p-value of `_slope_p` matched scipy.stats.linregress (alternative greater) to better than 1e-15.',
    'DEC-08': 'self-generated random-intercept data (14 dams, 4 pups): False; 0.1 ms per call (3 calls + 1 repeat, equal); the correlation p-value of `_corr_p` matched scipy.stats.pearsonr (alternative greater) to 1.3e-15.',
    'DEC-R1': 'self-generated Gaussian arrays (1000, 60) and (60,), null data: False; 0.7 ms per call (3 calls + 1 repeat, equal).',
    'DEC-R2': 'self-generated gamma-rate data (400 neurons, 40 trials): False; 0.2 ms per call (3 calls + 1 repeat, equal).',
    'DEC-R3': 'self-generated data (40 participants, 20 young): False; 0.1 ms per call (3 calls + 1 repeat, equal).',
    'DEC-R4': 'self-generated Bernoulli presence (8 plots, 12 dates, 4 fenced): False; 0.1 ms per call (3 calls + 1 repeat, equal).',
}
COMMON_RUNS = (' Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to '
               'scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. '
               'Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, '
               'non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. '
               'The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.')

for lid, cid in ids.items():
    b = briefs[lid]
    p = priv[lid]
    src, passage, how = PASSAGE[lid]
    m = M[lid]
    keys = '\n'.join('  - `%s`, %s, %s: %s' % (k['key'], k['shape'], k['dtype'], k['meaning']) for k in b['data_keys'])
    reserve = ' Reserve case.' if lid.startswith('DEC-R') else ''
    txt = """# {cid} ({lid})

## 1. Case
- Case id: {cid} (local id {lid}); class {cls}; tag (mechanism): {tag}; statistic family: {fam}; subtype: {sub}.{reserve}

## 2. Source
- Source key: {src}. Documenting passage: {passage}
- Who read it and how: {how}.

## 3. Brief
Claim: {claim}

Data keys:
{keys}

Sizes: {sizes}

## 4. Mapping
{mapping}

## 5. Allowed-guard minimum used
Private note minimum: {gmin}. Used: {guard}

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: {runs}{common}

## 7. Deviations from the private note and problems
{dev}
""".format(cid=cid, lid=lid, cls=CLASS[lid], tag=p['mechanism_tag'], fam=p['statistic_family'], sub=p['subtype'],
           reserve=reserve, src=src, passage=passage, how=how, claim=b['claim'], keys=keys,
           sizes=json.dumps(b['sizes']), mapping=m['mapping'], gmin=p['guard_minimum'], guard=m['guard'],
           runs=RUNS[lid], common=COMMON_RUNS, dev=m['dev'])
    path = os.path.join(H, 'cases', cid, 'CASE.md')
    open(path, 'w', encoding='utf-8', newline='\n').write(txt)
    print('wrote', path)
