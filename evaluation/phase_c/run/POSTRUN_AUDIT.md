# Phase C: post-run blind audit (PREREG_PHASE_C §7, as PB §7)

Auditor: a fresh agent that wrote no brief, world, criterion, case or audit of this evaluation. I read only the copies in
this task folder. I did not run the gate and started no other agent. Small Python scripts (`py -I`) in `scratch\` read
the certificates and printed numbers.

**What was checked before answering.**
* All 209 files of `FREEZE_CASES.json` in `phase_c\` match their SHA-256 values. The `module_sha256` of all 208
  certificates (0.5.0 and 0.4.1) matches the frozen `faulty.py` / `fixed.py`. Every certificate has exactly one component
  and no load error.
* Recomputed from the certificates and `EXPECTED_FLAGS.json`, per pair and version: the expected flags present, the
  detection (NOT_FALSIFIABLE and at least one expected flag) and the clean pass (FALSIFIABLE or WEAK). All of these agree
  with `run\RESULTS.json`.
* Rates below are HOLDS counts out of 200 samples per stream from the **0.5.0** certificates, written "faulty vs fixed".
  At n = 200 with these Bonferroni levels a stream is flagged from about 18 to 20 holds.

**How the three questions were applied.**
* (i) "yes" when the flag(s) that made the detection are absent from the fixed twin, or come from a markedly different
  rate. A "yes" is marked **qualified** when the fixed twin is itself NOT_FALSIFIABLE with expected flags. In that case
  the pair would also count as detected with a correct criterion, and the error shows only in the rate difference (or in
  one flag the fixed twin lacks).
* (ii) "yes" when the failure of the fixed twin comes from structure the skeleton keeps. "no" when it does not come from
  the skeleton. In every "no" below, the documented correction itself is faithful. The cause is the claim's own decision
  rule or statistic, which the fixed criterion must keep: a threshold without a test at the brief's size, or a ratio index
  on the gate's noise probe.
* (iii) "yes" only for a sign beyond I-4 (the world author infers the error from the form of the claim) and I-6 (B-3
  claims name the adjusted-for quantity). The sign found here is of one kind: a data key that no part of the claim uses and
  only the faulty statistic reads, around which the world author built structure.

## Per pair

### B-1

#### B1-01 (B-1, MOR03; world C33; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty NOT_FALSIFIABLE on K2_HIGH_SIZE, K2_FAILS_UNREACHABLE, K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS and HIGH_RATE:control:permute_active (minus 200/200, control 200/200). Fixed twin on the same worlds: minus 0/200, control 0/200, no expected flag. The within-arm fall of the active arm keeps the placebo-course fall (4 points in both worlds, above the claim's 3) and the regression of the selected starters; the arm contrast of the fixed twin removes both.
* **(ii) n/a.** Clean pass (WEAK; plus 199/200, minus 0/200).
* **(iii) no.** No world log (batch 03). The brief states the claim's cut (start index >= 20) and three keys; the skeleton gives both arms a placebo course and occasion error (MEASUREMENT_SD 3), ordinary trial structure. Nothing beyond I-4.

#### B1-02 (B-1, MOR03; world C43; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty flags K2_NO_SEPARATION, K4_CONTROL_ALSO_HOLDS and K5_HOLDS_ON_NOISE arise because the faulty twin holds in plus only 10/200 (minus 0, control 0, noise 1/200); the fixed twin holds in plus 200/200 and carries none of them. They follow from the planted error (one 12-month reading both defines the group and starts the second-year change), but as lost power, not as holding where the claim is false. The 'generic' label rests on K5_HOLDS_ON_NOISE with the noise probe holding on 1/200.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200, minus 7/200).
* **(iii) no.** No world log. The two 12-month scans are named in the claim itself (the estimand needs them); the skeleton gives every scan an independent precision error (SCAN_CV 0.015). Not beyond the claim.

#### B1-03 (B-1, MOR03; world C50; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 65/200), HIGH_RATE:control and K4 (swap of readings 2 and 3: 189/200). Fixed: minus 0/200, control 0/200, no flag. Selecting on reading 2 makes the 2-to-3 fall carry regression to the mean; selecting on reading 1 does not.
* **(ii) n/a.** Clean pass (WEAK; plus 197/200).
* **(iii) no.** Log C50 (P) states the reading 1-to-2 regression in both worlds (I-4). The three readings and the screening cut are in the claim. Nothing beyond I-4.

#### B1-04 (B-1, KRI10; world C05; awareness C)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Detected only through the noise probe (HIGH_RATE:probe:noise, K5_HOLDS_ON_NOISE; faulty 200/200 on noise); fixed 0/200 on noise and no expected flag. The declared streams did not show the error (faulty minus 0/200, control 0/200).
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C05 read C by both readers. The brief names the faces-versus-houses region only as the estimand requires.

#### B1-05 (B-1, KRI10; world C36; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: HIGH_RATE on both controls (93/200 and 199/200), noise 136/200, K2_HIGH_SIZE (minus 99/200, 101 abstentions), K4. Fixed: 6, 17, 8 and 4/200, no expected flag. Voxels selected and tested on the same 40 participants versus a split by participants.
* **(ii) n/a.** Clean pass by rule (WEAK, capped by K1_ABSTAINED_MAJORITY:world:minus with 101/200 abstentions and K4_INCONCLUSIVE); plus 200/200, minus 4/200.
* **(iii) no.** No world log. Minus has no responsive voxel; the controls scramble voxels or flip signs per participant. Nothing in the brief beyond the claim's 'voxels where participants respond'.

#### B1-06 (B-1, KRI10; world C06; awareness C)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 184/200), HIGH_RATE:control (185/200), shuffle probe 188/200 and K5_HOLDS_ON_SHUFFLE. Fixed: 11, 6 and 9/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C06 read C (selected set empty in minus). The claim names the selected voxels as its estimand. Nothing beyond I-4.

#### B1-07 (B-1, KRI09; world C28; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE and K2_FAILS_UNREACHABLE (minus 200/200), HIGH_RATE:control and K4 (control 200/200), K2_NO_SEPARATION, and HIGH_RATE:probe:noise (81/200). The fixed twin lacks every declared flag (minus 2/200, control 16/200). The noise flag is shared with the fixed twin at the same rate (78/200), so the 'generic' label does not show the error; the declared flags do.
* **(ii) no.** Not from the skeleton: the fixed twin fails only on the gate's noise probe (78/200) and passes in the declared worlds and control (minus 2/200, control 16/200). Cause: the claim's index (V-H)/(V+H) on sign-indefinite N(0,1) data, where sums near zero or below zero occur; the fixed criterion must keep the claim's statistic and the allowed guards cannot exclude such sums. The correction itself (selection and index on different presentations) is the documented one. Reported in CASE.md section 7 before the run (99/200).
* **(iii) no.** Log C28 (P): trial noise in minus (I-4). The brief gives rates and the claim only.

#### B1-08 (B-1, KRI09; world C54; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 22/200, 74 abstentions), HIGH_RATE:control (28/200), HIGH_RATE:probe:noise (117/200). Fixed: 2, 2 and 5/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 185/200).
* **(iii) no.** Log C54 (P) names selection effects in minus (I-4). The brief gives the keys and the claim only.

#### B1-09 (B-1, VUL09; world C19; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 200/200, minus 180/200, control 183/200 (K5_HOLDS_ON_NOISE, HIGH_RATE:probe:noise, K2_HIGH_SIZE, HIGH_RATE:control). Fixed (repaired: split by participants): 0, 5 and 3/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 194/200).
* **(iii) no.** The two session keys are not named by the claim; they served the original session-split correction (replaced at the repair round), and the world author gave both sessions a stable subject component (log C19). Neither twin's detection relies on them: the faulty twin averages the sessions and is detected on noise. No sign that the brief decided the structure the detection uses.

#### B1-10 (B-1, MAK19; world C41; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 200/200, control 200/200 (it ranks by rate_pre, so permuting rate_rest cannot affect it), minus 42/200 (K2_HIGH_SIZE, K4). Fixed: 0, 0 and 3/200.
* **(ii) n/a.** Clean pass (WEAK; plus 190/200).
* **(iii) no.** No world log. The resting recording is named in the claim and rate_pre is needed for the change; the skeleton's recording-to-recording fluctuation (STATE_SD 0.15) is ordinary.

#### B1-11 (B-1, MAK19; world C31; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 99/200) and HIGH_RATE:control (86/200). Fixed: 16 and 14/200, below the flag level. Window picked and tested on the same participants versus split participants.
* **(ii) n/a.** Clean pass (WEAK; plus 176/200, minus 16/200).
* **(iii) no.** No world log. Autocorrelated EEG residuals (NOISE_RHO 0.9) give the window means their variance; 'time samples in order' is an axis name. Nothing beyond I-4.

#### B1-12 (B-1, BAR05; world C11; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty K2_HIGH_SIZE (minus 145/200); fixed minus 0/200, no flag.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C11 (P) notes that screening and start are separate noisy visits (I-4). Both scores are named in the claim.

### B-2

#### B2-01 (B-2, L1.1, KAP23; world C44; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty (in-sample AUC): minus 178/200, controls 47/200 and 186/200. Fixed (5-fold CV): 5, 0 and 6/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 179/200).
* **(iii) no.** No world log. Rare onsets (about 5%) and country blocks are the world author's choices (docstring); the brief says only 'new country-years'.

#### B2-02 (B-2, L1.4, KAP23; world C37; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 25/200), HIGH_RATE:control (29/200). Fixed: 0 and 1/200. Copies of oversampled minority rows fall on both sides of the folds.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** No world log. 'The less frequent outcome' is in the claim (sensitivity for that class) and tells the world author the classes are unequal; the detection needs that imbalance (prevalence 0.22 in the skeleton), but it is the claim's own wording (I-4).

#### B2-03 (B-2, L1.4, KAP23; world C21; awareness C)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (faulty WEAK, minus 2/200). Needed: a minus world in which the ridge logistic fit can reproduce copied minority rows (far fewer units per feature than 1000 x 50); at this size the copies carry almost no weight, as CASE.md section 7 expected for a logistic model.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C21 read C/N. 'Balanced accuracy' is the claim's statistic.

#### B2-04 (B-2, L3.1, KAP23; world C34; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 1/200). Needed: a minus world in which the indicators and the next-day outcome share a slow common component, so that randomly folded neighbouring days pass the outcome to the 15-NN fit; in the declared minus the rises follow an independent copy of the process and the lift stays far below 0.58.
* **(ii) n/a.** Clean pass (WEAK; plus 166/200).
* **(iii) no.** No world log. 'Days in chronological order' is an axis name.

#### B2-05 (B-2, L3.1, KAP23; world C51; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). Needed: a minus world in which demand and the drivers share a slowly varying, non-extrapolating component that shuffled folds interpolate and forward evaluation cannot; with demand independent of the drivers a linear fit gains nothing from neighbouring weeks.
* **(ii) n/a.** Clean pass (WEAK; plus 199/200).
* **(iii) no.** Log C51 (C/P): deterministic seasonal drivers avoided to keep minus a clean null. Nothing from the brief beyond an axis name.

#### B2-06 (B-2, L3.2, KAP23; world C47; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). Needed: a minus world with patient-specific feature profiles strong and numerous enough relative to the 80 patients and the patch noise (or more features per patient) for a ridge logistic fit trained on other patches of the same patient to recover that patient's label; the declared offsets (SD 0.8 on 20 features) gave no lift.
* **(ii) n/a.** Clean pass (WEAK; plus 197/200).
* **(iii) no.** Log C47 names the patch-versus-patient mechanism (P; I-4). The brief gives axes and 'new patients' only.

#### B2-07 (B-2, L3.2, KAP23; world C42; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 12/200 against fixed 2/200, below the flag level). Needed: a minus world with a larger stable participant component in the score and fewer participants per measurement, so that OLS on pooled sessions exploits participant identity.
* **(ii) n/a.** Clean pass (WEAK; plus 198/200).
* **(iii) no.** No world log. Axes and 'new participants' only.

#### B2-08 (B-2, L1.3, VAR06; world C26; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Qualified. Faulty: minus 86, control 94, noise 130/200 (K2_HIGH_SIZE, HIGH_RATE:control, HIGH_RATE:probe:noise). The fixed twin carries the same three flags at about half the rates (47, 48, 65/200). By the rule ('markedly different rate') the detection follows from the error, but the fixed twin is itself NOT_FALSIFIABLE with expected flags: the pair would count as detected with a correct criterion.
* **(ii) no.** Not from the skeleton: minus carries no class information (log C26) and the fixed twin also fails on the noise probe (65/200). Cause: the claim's accuracy threshold 0.60 without a test at the brief's 40 samples (nested-CV SD 0.114, P(>= 0.6) about 0.24, CASE.md section 7), kept by the fixed criterion; the correction (nested CV) is the documented one.
* **(iii) no.** Log C26 (P). The claim names the classifier family, not the tuning procedure; the detection holds on the noise probe and needs no world structure.

#### B2-09 (B-2, L1.3, VAR06; world C32; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Qualified. Faulty: minus 26, control 23, noise 67/200; fixed: 18, 20, 25/200 with the same three flags. On the declared streams the rates are nearly equal; only the noise rate differs markedly (67 vs 25). The fixed twin is itself NOT_FALSIFIABLE with expected flags.
* **(ii) no.** Not from the skeleton (minus has no response information; the noise probe gives 25/200). Cause: the claim's AUC threshold 0.65 without a test at 40 patients, kept by the fixed criterion (CASE.md reported 8 to 8.5% in minus); the correction is the documented nested CV.
* **(iii) no.** No world log. Nothing in the brief beyond the claim (classifier family named).

#### B2-10 (B-2, L1.3, VAR06; world C48; awareness C)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Qualified. Faulty: minus 89, control 85, noise 122/200; fixed: 31, 41, 50/200 with the same three flags. Markedly different rates, but the fixed twin is itself NOT_FALSIFIABLE with expected flags.
* **(ii) no.** Not from the skeleton (no class information in minus; noise 50/200). Cause: the claim's accuracy threshold 0.60 without a test at 40 samples, kept by the fixed criterion; the nested CV with gene reselection is the documented correction.
* **(iii) no.** Log C48 read C. The claim names a kernel-based classifier; no world structure is used by the detection.

#### B2-11 (B-2, L1.3, VAR06; world C01; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Qualified. Faulty: minus 132, control 110, shuffle 102, noise 122/200; fixed: 46, 44, 46, 39/200 with the same four flags. Markedly different rates, but the fixed twin is itself NOT_FALSIFIABLE with expected flags.
* **(ii) no.** Not from the skeleton (no group information in minus; noise 39/200). Cause: the claim's balanced-accuracy threshold 0.60 without a test at 40 subjects (CASE.md: mean 0.506, SD 0.106, P(>= 0.6) 0.21), kept by the fixed criterion; the correction is the documented nested CV.
* **(iii) no.** Log C01 (C/P). Nothing beyond the claim.

#### B2-12 (B-2, L1.3, AMB02; world C07; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 188, minus 165, control 173, shuffle 166/200. Fixed: 6, 5, 6, 5/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C07 (P): class proportions 40/22 kept (the world author's own choice). 'Three genes' is the claim's own; the detection is on the noise probe and needs no world structure.

### B-3

#### B3-01 (B-3, CUR13; world C16; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty K2_HIGH_SIZE (minus 33/200); fixed minus 13/200, below the flag level (control 10, noise 10/200). Ratio of heart to body mass versus covariate adjustment, with groups differing in body mass and a non-zero intercept.
* **(ii) n/a.** Clean pass (WEAK; plus 188/200).
* **(iii) no.** Log C16 (P) keeps the drug's body-mass effect and the intercept in minus; body mass is the adjusted-for quantity the claim names (I-6).

#### B3-02 (B-3, CUR13; world C53; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 2/200). Needed: a minus world in which creatinine falls much more steeply with age relative to albumin's other variation, or albumin scales far less than proportionally with creatinine, so that the quotient's correlation with age reaches 0.15.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C53 (P); the adjusted-for quantity is named (I-6).

#### B3-03 (B-3, CUR13; world C39; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). Needed: a minus world with a strong dependence of systolic pressure on body surface area and LV mass far from proportional to it, so that LV mass / BSA carries body-size information; here pressure depends on BSA weakly (3 mmHg per SD against noise SD 17.5).
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** No world log; the adjusted-for quantity is named (I-6).

#### B3-04 (B-3, CUR13; world C13; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (generic), failed clean pass.

* **(i) yes.** Qualified. The noise flag is absent from the fixed twin (faulty noise 65/200, fixed 0/200), so the detection follows from the error through that flag. The declared flags are carried by the fixed twin at similar rates (minus 46 vs 32, control 53 vs 42), and the fixed twin is itself NOT_FALSIFIABLE with expected flags.
* **(ii) yes.** From the skeleton with the claim's rule: the fixed twin fails in minus (32/200) and under the control (42/200) but not on noise (0/200). In this world the kidney variation at fixed body mass is small against the liver noise, so the coefficient's sampling SD is about 0.30 at n = 150 (log C13: in minus it 'exceeds 0.25 by chance in about a fifth of the draws'), and the claim has a threshold without a test. The fixed criterion is the documented regression with body mass as covariate.
* **(iii) no.** Log C13 (P); I-6.

#### B3-05 (B-3, PEA97; world C12; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Generic only: faulty noise 67/200 against fixed 0/200; the declared streams give 0/200 in both twins.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C12 (P); I-6.

#### B3-06 (B-3, PEA97; world C09; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: minus 61, control 62, noise 38/200. Fixed: 0/200 in all three.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) no.** Log C09 (P); I-6.

#### B3-08 (B-3, ARC81; world C30; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 200/200, control 200/200 (it correlates the fall with the first baseline reading, so permuting the second cannot affect it), minus 72/200. Fixed: 0/200 in all three.
* **(ii) n/a.** Clean pass (WEAK; plus 188/200).
* **(iii) no.** Log C30 (P). The second baseline reading is named in the claim because the estimand needs it.

#### B3-09 (B-3, ARC81; world C04; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 199/200, control 200/200 (it ignores o2_uptake_expired), minus 34/200. Fixed: 2, 3, 4/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 200/200).
* **(iii) yes.** The key venous_o2_content is used by no part of the claim (delivery versus expired-gas uptake) and only by the faulty statistic (Fick-calculated uptake). The world author made it Fick-consistent with the measured cardiac output and wrote that the computed uptake 'shares the cardiac-output measurement error with delivery in minus too' (log C04). K2_HIGH_SIZE (minus 34/200) relies on that structure; the noise and control flags do not, so the detection would stand without it.

#### B3-11 (B-3, KRO93; world C24; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: noise 155, control 200, minus 200/200. Fixed: 9, 0, 0/200, no expected flag.
* **(ii) n/a.** Clean pass (WEAK; plus 182/200).
* **(iii) no.** Log C24 (P); I-6.

#### B3-12 (B-3, KRO93; world C25; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed NOT_FALSIFIABLE; detected (declared), failed clean pass.

* **(i) no.** The only expected flag is K2_HIGH_SIZE (minus 25/200); the fixed twin carries the same flag at 23/200 for the same reason (autocorrelated, seasonal monthly residuals that the claim's OLS t test does not model). The detection does not show the error.
* **(ii) yes.** The fixed twin fails only by K2_HIGH_SIZE (minus 23/200; noise 4/200, controls 11 and 0/200): the skeleton keeps AR(1) waves and a seasonal cycle in both worlds (log C25), which inflate the size of the claim's ordinary t test. The fixed criterion is the documented covariate adjustment.
* **(iii) no.** Log C25 (P); I-6.

### B-6

#### B6-01 (B-6, LAZ18; world C27; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 32/200), HIGH_RATE:control (26/200). Fixed: 7 and 1/200. Pups counted as replicates with a litter effect kept in minus.
* **(ii) n/a.** Clean pass (WEAK; plus 181/200).
* **(iii) no.** Log C27 (P): litter effect in both worlds (I-4). The (dams, pups) axes are named in the shape.

#### B6-02 (B-6, LAZ18; world C38; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 32/200, control 42/200. Fixed: 4 and 3/200.
* **(ii) n/a.** Clean pass (WEAK; plus 186/200).
* **(iii) no.** No world log; between-well variation (WELL_SD 0.30) is ordinary; axes only.

#### B6-03 (B-6, LAZ18; world C17; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 67/200, control 69/200. Fixed: 4 and 5/200.
* **(ii) n/a.** Clean pass (WEAK; plus 186/200).
* **(iii) no.** Log C17 (P): animal > section > neuron hierarchy in both worlds (I-4).

#### B6-04 (B-6, LAZ18; world C10; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 7/200; control 13, shuffle 16/200). Needed: a minus world with more animals per cage or a larger cage share of variance; with the brief's 2 animals per cage and an intra-cage correlation near 0.58 the animal-level test stays near its nominal rate.
* **(ii) n/a.** Clean pass (WEAK; plus 187/200).
* **(iii) no.** Log C10 (P): cage component kept (I-4).

#### B6-05 (B-6, NIE11; world C45; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: K2_HIGH_SIZE (minus 47/200) and K2_NO_SEPARATION (plus 76/200). Fixed: minus 6/200, plus 184/200. 'Significant here, not there' with a practice gain in both groups.
* **(ii) n/a.** Clean pass (WEAK; plus 184/200).
* **(iii) no.** No world log; a practice gain in both groups (GAIN_CONTROL 0.035) is ordinary; the claim names the correct test.

#### B6-06 (B-6, NIE11; world C52; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss: the faulty twin never holds (plus, minus and control 0/200; K2_HOLDS_UNREACHABLE, not an expected flag). Needed: worlds in which each group's own slope is near its detection limit (for example a common slope of a few ms per session in minus), so that 'significant in healthy, not in patients' occurs by chance; at -12 (minus) and -16/-8 (plus) both groups are always significant.
* **(ii) n/a.** Clean pass (WEAK; plus 187/200).
* **(iii) no.** Log C52 (N/P). Nothing from the brief.

#### B6-07 (B-6, NIE11; world C08; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 69/200, control 34/200. Fixed: 4 and 3/200.
* **(ii) n/a.** Clean pass (WEAK; plus 180/200).
* **(iii) no.** Log C08 (P): region B more variable than region A in both worlds, the world author's own choice (I-4); the brief says nothing about variability.

#### B6-08 (B-6, HUR84; world C22; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 34/200, control 47/200. Fixed: 5 and 1/200.
* **(ii) n/a.** Clean pass (WEAK; plus 184/200).
* **(iii) no.** Log C22 (P). Four tanks per group (twice the source) does not favour the error.

#### B6-09 (B-6, HUR84; world C35; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 23/200, control 38/200. Fixed: 5 and 1/200.
* **(ii) n/a.** Clean pass (WEAK; plus 189/200).
* **(iii) no.** No world log; plot and date variation are ordinary; axes only.

#### B6-10 (B-6, LAZ10; world C23; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 20/200, control 22/200. Fixed: 5 and 3/200.
* **(ii) n/a.** Clean pass (WEAK; plus 179/200).
* **(iii) no.** Log C23 (P): repeated days of one rat (I-4).

#### B6-11 (B-6, LAZ10; world C03; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 83/200, control 37/200, shuffle 43/200. Fixed: 5, 9 and 2/200.
* **(ii) n/a.** Clean pass (WEAK; plus 179/200).
* **(iii) no.** Log C03 (P): a within-subject day correlation of 0.3 added by the world author as a property 'the claim is not about' (I-4); the claim itself specifies subject means.

#### B6-12 (B-6, MAK19; world C15; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty: minus 39/200, control 59/200. Fixed: 2 and 15/200 (below the flag level).
* **(ii) n/a.** Clean pass (WEAK; plus 178/200).
* **(iii) no.** Log C15 (N/P): correlation 0.4 in both groups in minus. Nothing from the brief.

### Out of scope (O-1 to O-3, description only)

#### O1-A (O, O-1, KAP23; world C40; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). No fixed-rule null stream can show it: scaling and PCA on all rows carry no outcome information when the outcome is independent of the markers; only a world with a true out-of-sample R-squared just below 0.15 could show the small optimism (out of scope).
* **(ii) n/a.** Clean pass (WEAK; plus 192/200).
* **(iii) no.** No world log. The claim names PCA and 5-fold CV as its own statistic; no world structure favours the error.

#### O1-B (O, O-1, KAP23; world C49; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). Dropping the middle severity band cannot create speech information in a minus world without any; a world with weak but real speech information (true balanced accuracy below 0.70) would be needed (out of scope).
* **(ii) n/a.** Clean pass (WEAK; plus 173/200).
* **(iii) yes.** severity_rating is used by no part of the claim and only by the faulty criterion. The world author linked it to diagnosis and built a control for 'an analysis that gets its accuracy from the severity rating' (log C49). Steering is present, but the pair was missed, so no detection depends on it.

#### O2-A (O, O-2, SIM11; world C18; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (declared), clean pass.

* **(i) yes.** Faulty K2_HIGH_SIZE (minus 65/200); fixed minus 7/200, no flag.
* **(ii) n/a.** Clean pass (WEAK; plus 188/200).
* **(iii) yes.** The willingness-to-pay keys are used by no part of the claim (liking only) and only by the faulty criterion (any of three outcomes). The world author gave willingness to pay its own treatment effect and kept it in minus under the fixed rule (log C18). The detection rests entirely on that effect.

#### O2-B (O, O-2, SIM11; world C20; awareness C)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; detected (generic), clean pass.

* **(i) yes.** Faulty: minus 21, control 21, noise 19/200 (just above the flag level). Fixed: 7, 7, 6/200, no flag. Optional stopping.
* **(ii) n/a.** Clean pass (WEAK; plus 188/200).
* **(iii) no.** Log C20 (C). 'On all participants' led the world author to keep a low-effort tail, which the detection does not use (it also holds on i.i.d. noise).

#### O3-A (O, O-3, BAG09; world C29; awareness P)
0.5.0: faulty NOT_FALSIFIABLE, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss: the faulty twin never holds (plus 0/200; K2_HOLDS_UNREACHABLE, not an expected flag). Needed: that flag on the list, or a minus world in which the rows next to the signature carry a sensitivity difference that the signature lacks.
* **(ii) n/a.** Clean pass (WEAK; plus 199/200).
* **(iii) no.** Log C29 (C/P). The signature mask key is needed by the claim.

#### O3-B (O, O-3, HER14; world C14; awareness P)
0.5.0: faulty WEAK, fixed WEAK; missed, clean pass.

* **(i) n/a.** Miss (minus 0/200). Needed: a world in which the five dropped country rows differ systematically from the rest; the declared countries are exchangeable draws.
* **(ii) n/a.** Clean pass (WEAK; plus 199/200).
* **(iii) no.** Log C14 (C/P): trends and country links avoided to keep minus clean. Nothing from the brief.

## Summary

### Counts per class

| Class | Pairs | (i) yes / no / n/a | of the (i) "yes": qualified | (ii) yes / no / n/a | (iii) yes / no |
|---|---|---|---|---|---|
| B-1 | 12 | 12 / 0 / 0 | 0 | 0 / 1 / 11 | 0 / 12 |
| B-2 | 12 | 7 / 0 / 5 | 4 (B2-08 to B2-11) | 0 / 4 / 8 | 0 / 12 |
| B-3 | 10 | 7 / 1 / 2 | 1 (B3-04) | 2 / 0 / 8 | 1 / 9 |
| B-6 | 12 | 10 / 0 / 2 | 0 | 0 / 0 / 12 | 0 / 12 |
| O-1 | 2 | 0 / 0 / 2 | 0 | 0 / 0 / 2 | 1 / 1 |
| O-2 | 2 | 2 / 0 / 0 | 0 | 0 / 0 / 2 | 1 / 1 |
| O-3 | 2 | 0 / 0 / 2 | 0 | 0 / 0 / 2 | 0 / 2 |
| All | 52 | 38 / 1 / 13 | 5 | 2 / 5 / 45 | 3 / 49 |

### Pairs with "no" for (i)

* **B3-12.** The only expected flag, K2_HIGH_SIZE (minus 25/200), is carried by the fixed twin for the same reason
  (23/200). The detection does not show the planted error. REPORT §7.3 says the same.

### Pairs with "no" for (ii) (the failure does not come from the skeleton)

* **B1-07.** The fixed twin fails only on the gate's noise probe (78/200). The cause is the claim's ratio index on
  sign-indefinite noise. Minus gives 2/200 and the control 16/200.
* **B2-08, B2-09, B2-10, B2-11.** The cause is the claim's accuracy, AUC or balanced-accuracy threshold without a test at
  the brief's 40 samples. The noise probe fails too (65, 25, 50 and 39/200). Minus carries no class information.

In all five the fixed criterion is the documented correction. The fault lies in the claim's rule, which the fixed
criterion must keep. The two failed clean passes that do come from the skeleton are B3-04 (low kidney variation against
the liver noise, with a threshold and no test) and B3-12 (autocorrelated, seasonal residuals under an ordinary t test).

### Pairs with "yes" for (iii)

* **B3-09.** `venous_o2_content` is read only by the faulty Fick uptake. The world author made it Fick-consistent with the
  measured cardiac output. That structure supports K2_HIGH_SIZE (34/200). The detection would stand without it: noise
  gives 199/200 and the control 200/200.
* **O2-A** (out of scope). The willingness-to-pay keys are read only by the faulty "any of three outcomes" rule. The
  world author kept a treatment effect on willingness to pay in `minus`. The detection (65/200) rests entirely on it.
  Phase B's auditor flagged the overlapping O2a for steering too.
* **O1-B** (out of scope, missed). `severity_rating` is read only by the faulty criterion. The world author built a
  control around it. No detection depends on it. Phase B's auditor flagged the overlapping O1a for steering too.

### Qualified detections (answer "yes", but the fixed twin is also NOT_FALSIFIABLE with expected flags)

* **B2-08, B2-10, B2-11.** The fixed twin carries every detecting flag at roughly a third to a half of the faulty rate.
* **B2-09.** On the declared streams the rates are nearly equal (minus 26 vs 18, control 23 vs 20). Only the noise rate
  differs markedly (67 vs 25).
* **B3-04.** The noise flag is absent from the fixed twin (65 vs 0). The declared flags are carried at similar rates
  (minus 46 vs 32, control 53 vs 42).

Under a strict counterfactual reading ("would the pair be detected with the fixed criterion?") these five pairs, with
B3-12, would count as detected without the error. B-2's 7 detections include 4 such pairs. B-3's 8 include 2 (B3-04,
B3-12). This is a post-hoc observation. It changes nothing in the pre-registered table (PB §7).

Two further detections reach the error by a route other than holding where the claim is false:
* **B1-02.** The planted error costs the faulty twin power in `plus` (10/200).
* **B1-07.** The "generic" label rests on a noise flag that the fixed twin shares at the same rate. Its declared flags do
  show the error.

## Statements in REPORT.md (sections 1 to 8) that the certificates or files contradict or do not support

1. **§7.4, size ratios: "The rest are about 1."** This is contradicted. B2-01's indicator axis is 30 of the source's 90:
   ratio 0.33 in `run\RESULTS.json` (pair B2-01, `size_ratio`) and in the designer line of `cases\B2-01\CASE.md`. This
   reduction is not due to the cap of 1000 per axis. §8 ("four VAR06 pairs and O3-A are reduced (7.4)") omits it too. The
   fidelity auditor accepted 30 as "within the source's models" (`record\audit\B2\out\AUDIT.json`, B2-01 item (f)).
2. **§1, "18 through its own noise probe", and §3, "The noise probe, which needs no declaration, found 18 of the 37
   in-scope detections."** The count of 18 matches the pre-registered label rule. "Found" is not supported for two of
   them:
   * **B1-02.** The noise probe holds on 1/200. K5_HOLDS_ON_NOISE fires only because the faulty twin holds in `plus` on
     10/200, and the declared flags carry the detection.
   * **B1-07.** The fixed twin holds on noise at the same rate (78 vs 81/200), so the noise flag does not reflect the
     error. The detection rests on declared flags.

   For B2-08 to B2-11 the fixed twins carry the noise flag as well, at lower rates.
3. **§7.1: "The declared worlds did not contain enough of what the error exploits for the gate to see it."** This is
   not supported as the whole cause for B2-03, B2-05 and B2-07. Their `CASE.md` section 7 records that the low-capacity
   model chosen for both twins lets copied rows, neighbouring weeks or a participant's other sessions leak little. That
   model is a ridge logistic regression in B2-03 and ordinary least squares in B2-05 and B2-07. The miss depends on that
   choice as well as on the worlds.
4. **§8: "Every certificate carries K5_INCONCLUSIVE:zeros: the allowed zero-variance guard makes the criteria abstain on
   the all-zeros probe."** The flag is on all 208 certificates and no file is FALSIFIABLE (checked). In B1-01, B1-03,
   B1-12 and O3-B, however, the abstention on all-zero data comes from the empty-selection guard. On all-zero data no
   unit passes the claim's cut (start index >= 20, reading >= 160, screening score >= 60, debt ratio > 90), as their
   `CASE.md` pre-checks show. The zero-variance guard is not involved. This is minor.
5. **Phase B items: §4, "Unlike Phase B, three of the four in-scope pairs read C were detected"; §5, the Phase B
   awareness column (12/0/0, 8/1/3, 10/2/0, 11/0/1); §7.3, "Phase B's B1-02 failed for the same reason."** These cannot
   be checked from the files of this audit, which hold no Phase B awareness reading and no Phase B per-pair result.
   P-7 item 6 names only the class rows of Phase B's `RESULTS.json` as Phase B input. Nothing here contradicts them:
   Phase B's own totals (P-1: 45 P, 5 C, 4 N) are consistent, and `PHASE_B_TABLE.json` shows that Phase B's B1-02 used
   the same kind of ratio index.

Checked and supported, among others:
* the class table, the Wilson bounds and the generic/declared/K2-only splits;
* the B-2 subtype rows and the 0.4.1 table and comparison (eight UNDEFINED files, all "soft only");
* the noise-only and declared-only baselines for both versions, and the overlap and addendum counts;
* the tables without overlapping pairs, the awareness counts and the eight disagreements;
* the abstention shares, the eleven "error too small" labels and every rate quoted in §7;
* the guard-expression note, the run window (17:41 to 18:24 UTC from the certificates), the tag commits in the run logs
  and the freeze cores.

Related observation (an omission, not a statement): REPORT §7.3 says that B3-12's detection does not show the error. It
does not say that the fixed twins of B2-08 to B2-11 and B3-04 are also NOT_FALSIFIABLE with expected flags, so those
detections are equally matched by the fixed twin.
