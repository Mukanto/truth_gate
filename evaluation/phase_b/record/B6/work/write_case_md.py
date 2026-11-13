# Writes CASE.md for each case (last step per case). Text only; runs no criterion.
import json, os, re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
pre_lines = {l.split()[0]: l.strip() for l in open(os.path.join(ROOT, "work", "precheck_fixed_output.txt"), encoding="utf-8") if l.strip()}
priv = {p["local_id"]: p for p in json.load(open(os.path.join(ROOT, "PRIVATE.json"), encoding="utf-8"))}

READ = {
    "NIE11": "Read in full by the earlier author (author-hosted PDF, whole text); I re-checked the quoted sentence against the saved extract src/nie.txt and src/nie2.txt.",
    "HUR84": "Read in full by the earlier author (UBC PDF, pdftotext, two-column order scrambled; passage located by keyword); I re-checked the quoted sentence against the saved extract src/hur.txt.",
    "LAZ10": "Read in full by the earlier author (Europe PMC full text XML PMC2817684); I re-checked the quoted sentence against the saved extract src/laz.txt.",
    "MAK19": "Read in full by the earlier author (Europe PMC full text XML PMC6785265, the cited section); I re-checked the quoted sentence against the saved extract src/mak.txt.",
}

PASSAGE = {
    "B6-01": 'NIE11 (Nieuwenhuis et al. 2011, Nat Neurosci 14:1105), p. 1105: "To support this claim, they needed to report a statistically significant interaction (between amount of training and type of mice), but instead they reported that one effect was statistically significant, whereas the other effect was not." (Fig. 1b; MAK19 Fig. 1B uses 20 per group.)',
    "B6-02": 'NIE11, p. 1105: "Similarly, claims about differences in activation across brain regions must be supported by a significant interaction between brain region and the factor underlying the contrast of interest." (drug versus placebo is among the comparisons the text lists; Fig. 1d, repeated measures.)',
    "B6-03": 'NIE11, p. 1105: "A fictive example would be \'Hippocampal firing synchrony correlated with memory performance in the placebo condition (r = 0.43, P = 0.01), but not in the drug condition (r = 0.19, P = 0.21)\'." (MAK19 Fig. 1A: correlations in two groups of 20.)',
    "B6-04": 'HUR84 (Hurlbert 1984, Ecol Monogr 54:187), section "Sacrificial pseudoreplication": "...where the data for replicates are pooled prior to statistical analysis ... or where the two or more samples or measurements taken from each experimental unit are treated as independent replicates (Fig. 5B)." (the aquaria example has four treated and four control units.)',
    "B6-05": 'HUR84, same passage as B6-04 (several samples from each experimental unit treated as independent replicates; the tanks are the units that receive the treatment). HUR84 does not discuss regression on a dose; the unit-of-treatment logic is carried over (extension flagged by the earlier author).',
    "B6-06": 'HUR84, section "Temporal pseudoreplication": "This differs from simple pseudoreplication only in that the multiple samples from each experimental unit are not taken simultaneously but rather sequentially over each of several dates (Fig. 5C). Dates are then taken to represent replicated treatments ..."',
    "B6-07": 'LAZ10 (Lazic 2010, BMC Neurosci 11:5), section on hierarchical data: "Consider an experiment with two experimental conditions (treatment vs. control), with one rat in each condition. The outcome variable is the number of synapses on cells in the CA3 region of the hippocampus, and 100 cells are examined in each rat." (cells within animals; the animal is the unit of replication. Type I error rate rises with the intraclass correlation, e.g. alpha 0.37 at n = 10 per group, IC = 0.30.)',
    "B6-08": 'LAZ10 abstract: "Pseudoreplication occurs when observations are not statistically independent, but treated as if they are." Also MAK19, "Inflating the units of analysis" (pooled measures across participants). The pooled trial-level correlation is an extension of the documented setting (flagged by the earlier author).',
    "B6-09": 'LAZ10, hierarchical data and Fig. 1 example: the first (incorrect) interval "uses all 20 data points and does not account for the hierarchical nature of the data"; the correct analysis uses "the mean of the ten values for each rat". The paired drug-versus-vehicle design is a paired extension of the between-group examples (flagged by the earlier author).',
    "B6-10": 'MAK19 (Makin and Orban de Xivry 2019, eLife 8:e48175), section "Interpreting comparisons between two effects without directly comparing them": "Researchers often base their conclusions regarding the impact of an intervention (such as a pre- vs. post-intervention difference or a correlation between two variables) by noting that the intervention yields a significant effect in the experimental condition or group, whereas the corresponding effect in the control condition or group is not significant." (regression slopes of the same participants in two conditions: extension flagged by the earlier author.)',
    "B6-11": 'MAK19, section "Inflating the units of analysis": "If the researchers combine the pre and post measures across participants, they will end up with df = 18, the critical R value is now 0.44, rendering it easier to observe a statistically significant effect." (10 participants, pre-post design, correct df = 8.)',
    "B6-12": 'MAK19, section "Interpreting comparisons between two effects without directly comparing them": "A similar issue occurs when estimating the effect of an intervention measured in two different groups: the intervention could yield a significant effect in one group but not in the other." (Fig. 1B, n = 20 per group; the 3-session per-participant slope and 14 per group are a small extension flagged by the earlier author.)',
}

MAPPING = {
    "B6-01": 'Faulty: two separate one-sample t-tests (two-sided, alpha 0.05) on the per-participant gains (post - pre), one per group; the claim "holds" when the trained gain is significantly positive, the untrained gain is not significant, and the trained mean gain is larger. This is the "significant in one group, not in the other" rule that NIE11 documents (Fig. 1b); alpha 0.05 is the level stated in the brief and the usual level in the source. Fixed: the direct interaction test NIE11 asks for, a Welch t-test on the gains of the two groups (two-sided 0.05, trained larger), the same data and the same alpha.',
    "B6-02": 'Faulty: separate paired (one-sample on the difference) t-tests of drug minus placebo in the visual and in the auditory region (two-sided 0.05); the claim holds when the visual effect is significantly positive, the auditory effect is not significant and the visual mean effect is larger (the "significant here, not there" rule of NIE11, brain-region example). Fixed: one paired t-test on the difference of differences ((vis_drug - vis_pl) - (aud_drug - aud_pl)) across the 16 participants, two-sided 0.05, visual larger (the region by drug interaction NIE11 requires).',
    "B6-03": 'Faulty: Pearson correlation tested separately in each group (one-sided 0.05, the level in the brief); the claim holds when the correlation is significantly positive in the older group, not significant in the younger group, and larger in the older group (the NIE11 correlation example "significant in one condition but not in the other"). Fixed: Fisher z test of the difference between two independent correlations, z = (z_old - z_young)/sqrt(1/(n_old-3) + 1/(n_young-3)), one-sided 0.05 (critical z 1.6448536269514722).',
    "B6-04": 'Faulty: the 40 water samples of each treatment are pooled (80 values in all) and compared with a two-sample Student t-test (two-sided 0.05, direction fertilised higher), so the samples are treated as independent replicates: HUR84 "simple pseudoreplication" (Fig. 5B), with the typical layout of 4 units per treatment (the aquaria example). Fixed: samples are averaged within pond and the same t-test is applied to the 4 versus 4 pond means (df 6), the experimental units.',
    "B6-05": 'Faulty: ordinary least-squares regression of all 96 mussel growth values on the tank dose repeated for each mussel (df 94), one-sided 0.05 on a positive slope; the individual mussels are treated as independent replicates although the dose is applied to tanks (HUR84 pseudoreplication; regression on a dose is an extension of the documented ANOVA/t-test setting, flagged in the private note). Fixed: regression of the 12 tank means on the dose (df 10), same slope test and level.',
    "B6-06": 'Faulty: all 72 plot-by-survey values per treatment are pooled and compared with a two-sample Student t-test (two-sided 0.05, mown higher), so the repeated surveys of the same plot count as replicates: HUR84 "temporal pseudoreplication". Fixed: surveys are averaged within plot and the same t-test is applied to the 6 versus 6 plot means (df 10).',
    "B6-07": 'Faulty: the 120 cells per genotype are treated as independent units in a two-sample Student t-test (two-sided 0.05, knockout higher), ignoring that cells share an animal: LAZ10 hierarchical data / pseudoreplication (the animal is the experimental unit); 6 animals x 20 cells within the range of the source examples. Fixed: cells are averaged within animal and the same t-test is applied to the 6 versus 6 animal means (df 10), one of the corrections LAZ10 gives (averaging; a mixed model is the other).',
    "B6-08": 'Faulty: the Pearson correlation of all 300 trials of the 12 participants pooled (df 298), one-sided 0.05; repeated observations of the same participants are counted as independent (LAZ10 abstract, "multiple observations on the same subjects"; MAK19 pooled correlation). Fixed: one Pearson correlation per participant (25 trials), Fisher z transform, one-sample t-test of the 12 z values against zero (df 11), one-sided 0.05, the participant being the unit.',
    "B6-09": 'Faulty: a paired t-test (two-sided 0.05, drug higher) over all 200 (animal, cell index) pairs, df 199, so the cells of one animal count as independent pairs (LAZ10 Fig. 1, "uses all 20 data points"). Fixed: the mean amplitude per animal and condition, then a paired t-test across the 8 animals (df 7), the same test and level (LAZ10: "the mean of the ten values for each rat are calculated first").',
    "B6-10": 'Faulty: the least-squares slope of reaction time on contrast is tested separately in each condition (two-sided 0.05); the claim holds when the attended slope is significantly negative (reaction time falls with contrast; "steeper" = more negative), the unattended slope is not significant, and the attended slope is the steeper (MAK19 "significant effect in the experimental condition, not in the control condition", applied to a regression slope). Fixed: the slope of the per-participant difference rt_attended - rt_unattended on contrast, two-sided 0.05, negative (the slope-difference test).',
    "B6-11": 'Faulty: the Pearson correlation over all 20 pooled participant-by-session measurements (df 18), one-sided 0.05; MAK19 documents exactly this pooling (10 participants, pre and post measures combined, df = 18 instead of 8). Fixed: sessions are averaged within participant and the correlation is computed over the 10 participant means (df 8), one-sided 0.05.',
    "B6-12": 'Faulty: a least-squares slope across the 3 sessions is computed for each participant, then one one-sample t-test per group (two-sided 0.05); the claim holds when the trained slopes are significantly positive, the control slopes are not significant, and the trained mean slope is larger (MAK19, "a significant effect in one group but not in the other"). Fixed: a Welch two-sample t-test of the per-participant slopes of the two groups (two-sided 0.05, trained larger), the direct group comparison.',
}

DEV = {
    "B6-01": "none",
    "B6-02": "none. The private note did not state a direction check; I added the direction (visual mean effect larger) to the faulty criterion and the sign (visual larger) to the fixed one, because the claim is directional.",
    "B6-03": "none.",
    "B6-04": "No log transform in either twin (the claim is about mean biomass and the private note says t-test on pond means). The fixed criterion has limited power in plus (see pre-check); recorded, not changed. Two-sample test: Student pooled variance in both twins.",
    "B6-05": "none. Extension of the documented setting is flagged in the private note (regression on a dose). In the pre-check the fixed criterion holds in 10/200 (5%) of minus samples and 14/200 (7%) under the control, close to the nominal one-sided 0.05 and within sampling noise for 200 samples; recorded, not changed.",
    "B6-06": "none.",
    "B6-07": "No log transform in either twin (the claim is about mean firing rates). The fixed criterion has limited power in plus (see pre-check); recorded, not changed.",
    "B6-08": "No skeleton request, but a problem for the clean pass is recorded: the fixed criterion holds in 27% of minus samples (54/200). I diagnosed this with a plain-Python check of the world function (work/diag_b608.py): the skeleton's minus world keeps a shared linear trial drift in both measures (the world author's \"fatigue drift\"), which gives a real within-participant correlation of about 0.065 (mean of the 12 within-participant correlations over 400 minus samples; 0.002 once the known drift terms are subtracted). The documented correction (analyse at the participant level) detects it legitimately; I did not detrend, because detrending is not part of the documented correction and would change the criterion. The fixed criterion is therefore expected to hold often in minus and may be flagged (K2_NO_SEPARATION or HIGH_RATE on minus-related streams); this is a skeleton property, not a criterion error.",
    "B6-09": "none. Raw amplitudes (the claim is about mean amplitude); extension of the documented between-group setting to a paired design is flagged in the private note.",
    "B6-10": "Sign convention for \"steeper\" (more negative slope, reaction time falling with contrast) follows the private note; the brief does not state the sign.",
    "B6-11": "none. The brief was revised by the earlier author to 10 participants x 2 sessions to match MAK19.",
    "B6-12": "Per-participant slope is the ordinary least-squares slope over the three sessions (time index 0, 1, 2); the private note did not specify the estimator.",
}


def main():
    for i in range(1, 13):
        cid = "B6-%02d" % i
        folder = os.path.join(ROOT, "cases", cid)
        a = json.load(open(os.path.join(folder, "ASSIGNMENT.json"), encoding="utf-8"))
        src = priv[cid]["source"].split()[0]
        pl = pre_lines[cid]
        # parse numbers from the pre-check line
        m = {k: v + ' (undefined ' + u + ')' for k, v, u in re.findall(r'(plus|minus|noise N\(0,1\)|zeros)=(\d+/\d+)\(und (\d+)\)', pl)}
        ctl = re.search(r"control\(([^)]*)\)=(\d+/\d+)", pl)
        tm = re.search(r"t=([\d.]+)ms g=([\d.]+)ms S=(\d+) est=([\d.]+)s", pl)
        brief = a["brief"]
        keys = "\n".join("  - `%s` %s, %s: %s" % (k["key"], k["shape"], k["dtype"], k["meaning"]) for k in brief["data_keys"])
        text = f"""# {cid}

1. **Case**: {cid}; world id {a['world_id']}; class {a['class']}; subtype {a['subtype'] or '(none)'}; source assigned by the designer: {a['source']}.

2. **Source and documenting passage**: {src}. {PASSAGE[cid]}
   Reading: {READ[src]}

3. **Brief exactly as in `ASSIGNMENT.json`**:
   - id: {brief['id']}
   - claim: {brief['claim']}
   - data keys:
{keys}
   - sizes: {brief['sizes']}

4. **Mapping of the twins to the documented error**: {MAPPING[cid]} The two twins differ only inside the body of `criterion`; the statistical helpers (a Lanczos log-gamma, a continued-fraction regularised incomplete beta and the t-distribution p-values built on them, written in numpy because scipy is not available; checked against numerical integration of the t density, maximum relative difference 1.2e-12 over df 1 to 298, `work/test_helpers.py`) and the guards are identical in both. Guards return None only for non-finite values, too few values or a zero variance. No randomness is used; the criterion is deterministic.

5. **Pre-checks of the fixed criterion** (plain Python, `work/precheck_fixed.py`, output in `work/precheck_fixed_output.txt`; fixed twin only, 200 samples per stream unless stated): holds in plus {m['plus']}, in minus {m['minus']}; on the declared control ({ctl.group(1)} applied to plus samples) {ctl.group(2)}; on i.i.d. N(0,1) noise of the same shapes {m['noise N(0,1)']}; on all-zero data (20 samples, guard) {m['zeros']}. Repeatability: two calls on the same data agree. Revisions of the fixed criterion: 0 (first version kept).

6. **Timing** (fixed criterion, mean of 100 calls on plus samples; g mean of 200 plus generations): t = {tm.group(1)} ms, g = {tm.group(2)} ms, S = {tm.group(3)} (2 worlds + 1 control + 0 premises + 0 relational pairs + 2 probes). Estimate 2 x 200 x (S + 1) x (t + g) = {tm.group(4)} s (limit 900 s).

7. **Deviations from the private note, problems, skeleton requests**: {DEV[cid]}
"""
        with open(os.path.join(folder, "CASE.md"), "w", encoding="utf-8") as f:
            f.write(text)
        print("CASE.md", cid)


main()
