s = open('build.py', encoding='utf-8').read()

def block(lid):
    i = s.index('add("%s"' % lid)
    j = s.find('\nadd(', i + 5)
    if j < 0:
        j = s.index('briefs = ')
    return i, j

new03 = '''add("B1-03",
    "In a study of 60 participants, those who perform worst at the start of a perceptual-learning task benefit most from training: the "
    "improvement (late-block score minus early-block score) of the lower-scoring half exceeds that of the higher-scoring half by at "
    "least 4 points, with an independent-samples t-test p < 0.05 (one-sided).",
    [k("score", "(participants, blocks)", "float", "percent correct (0 to 100) in each of 4 consecutive blocks of the task, block 0 first and block 3 last")],
    "60 participants, 4 blocks.",
    "KRI09",
    "KRI09, Introduction (Fig. 1 text): 'In behavioral studies, an example of selection is the division of a group of subjects into subgroups based on task performance.' The same text states that selection inside the same data distorts descriptive statistics and tests.",
    "Split participants at the median of block 0 (lower vs upper half); improvement = block 3 - block 0 per participant; independent-samples t (one-sided, lower half larger) p<0.05 and mean difference >= 4.",
    "Split participants at the median of block 0; improvement = block 3 - block 1 per participant (block 1 not used for the split); same one-sided independent t and mean difference >= 4.",
    "Replaces the earlier EEG time-window draft (see LOG). Statistic: independent-samples t / mean difference of change between two data-defined subgroups. The fix uses a second early block as an independent baseline; it is a standard correction (BAR05-style) and the split-data policy in KRI09 Fig. 4.")
'''
new09 = '''add("B1-09",
    "In a recording of 200 cortical neurons, the neurons that fire least at baseline show an increase in firing rate after the "
    "manipulation of at least 2 spikes/s on average. The claim holds when a one-sample t-test of the per-neuron increase against zero, "
    "over the low-baseline neurons, is significant at p < 0.05 (one-sided) and the mean increase is at least 2.",
    [k("base", "(neurons, epochs)", "float", "mean firing rate in spikes/s in two separate pre-manipulation epochs of equal length"),
     k("post", "(neurons,)", "float", "mean firing rate in spikes/s in the epoch after the manipulation")],
    "200 neurons, 2 baseline epochs.",
    "MAK19",
    "MAK19, section 'Circular analysis': 'They therefore split the population to sub-groups, by binning the data based on the activity levels observed at baseline. This leads to a significant interaction effect - those neurons that initially produced low responses show response increases ... could therefore be observed in pure noise.'",
    "Baseline = mean of the two baseline epochs; lowest-baseline third of neurons; increase = post - baseline for those neurons; one-sample t vs 0 (one-sided) p<0.05 and mean >= 2. Guard: >=5 neurons.",
    "Choose the lowest third by baseline epoch 0; increase = post - baseline epoch 1; same one-sample t and mean >= 2.",
    "Replaces the earlier compound-screen draft (setting not in any source). Statistic: one-sample t over a data-defined subgroup. Source example is exactly neurons binned on baseline.")
'''

for lid, new in (("B1-03", new03), ("B1-09", new09)):
    i, j = block(lid)
    s = s[:i] + new + s[j:]

# passages: replace the text between '"KRI09",\n    ' style positions by locating each add block's passage via source+order
passages = {
"B1-01": "KRI09, Introduction: 'In neuroimaging, an example of selection is the definition of a region of interest (ROI) by means of a statistical mapping that highlights voxels more strongly active during one condition than another.' Also: double dipping 'will give distorted descriptive statistics and invalid statistical inference'; independent data or a split-data analysis is the remedy (Fig. 4 policy). Example 2 simulates 30x30x20 voxels, 200 time points, four conditions.",
"B1-02": "KRI09, Example 1 discussion: 'In single-cell recording, for example, it is common to select neurons according to some criterion (e.g. visual responsiveness or selectivity) before applying further analyses to the selected subset. If the selection is based on the same data set as used for selective analysis, biases will arise.' (orientation tuning index is my instance of 'selectivity')",
"B1-04": "VUL09, 'The Nonindependence Error': 'This approach amounts to selecting one or more voxels based on a functional analysis and then reporting the results of the same analysis and functional data from just the selected voxels.' Fig. 4 simulates 10 subjects and 10,000 voxels of pure noise.",
"B1-05": "VUL09, survey section: 53% of respondents said 'regression across subjects' was the functional constraint used to select voxels; the reliability discussion mentions two scanning sessions (Manoach et al. 2001). Using a second session as the independent measure is my construction, not stated in VUL09.",
"B1-06": "VUL09, discussion of gradations of nonindependence: Study 26 'split the data into two groups: those with high IAT scores and those with low IAT scores. They then found voxels that showed a main effect between these two groups and computed a correlation within those voxels.' The Welch-t statistic is my variant of reporting the group effect in those voxels.",
"B1-07": "MAK19, 'Circular analysis': 'circular analysis is used to divide ... or reduce (e.g. defining a region of interest ...) the complete dataset using a selection criterion that is retrospective and inherently relevant to the statistical outcome.' KRI09 Introduction lists 'inferential analysis performed for a statistically selected subset of genes'. The tumour/normal panel is my instance.",
"B1-08": "MAK19, 'Circular analysis': 'circular analysis recruits the noise (inherent to any empirical data) to inflate the statistical outcome'; its worked example is a neuronal population measured before and after a manipulation. KRI09 describes selecting neurons by visual responsiveness. The calcium-imaging responders with a tone are my instance.",
"B1-10": "BAR05 abstract (verified): 'The effect of RTM in a sample becomes more noticeable with increasing measurement error and when follow-up measurements are only examined on a sub-sample selected using a baseline value.' Remedy per abstract: 'better study design and use of suitable statistical methods'. Full text not accessible: the blood-pressure setting and the placebo-arm remedy are NOT VERIFIED against the full text.",
"B1-11": "BAR05 abstract (verified): 'unusually large or small measurements tend to be followed by measurements that are closer to the mean.' The second-baseline remedy is NOT VERIFIED (full text not accessible). MAK19 'Circular analysis' also describes binning on baseline and then showing change as an artefact.",
"B1-12": "BAR05 abstract (verified): same sentence as B1-10 about a follow-up on a sub-sample selected using a baseline value. The education / test-score setting is NOT VERIFIED (full text not accessible).",
}
import re
for lid, p in passages.items():
    i, j = block(lid)
    blk = s[i:j]
    # passage is the 7th positional arg: the string right after the sizes line and source line
    m = re.search(r'(\n    "(?:KRI09|VUL09|MAK19|BAR05)",\n    )(.*?)(,\n    "(?:Per |Select|Among|Voxel|Average|Split|Students|Baseline|Grand|Choose))', blk, re.S)
    assert m, lid
    blk = blk[:m.start(2)] + repr(p) + blk[m.end(2):]
    s = s[:i] + blk + s[j:]
open('build.py', 'w', encoding='utf-8').write(s)
