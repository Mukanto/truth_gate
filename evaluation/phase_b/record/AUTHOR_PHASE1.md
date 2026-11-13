# Instructions for criterion authors, phase 1 (briefs)

You are a **criterion author** in a pre-registered evaluation of Truth_Gate, a tool that checks whether the acceptance
criteria of computational studies can fail. The rules are frozen in
`E:\Claude Projects\kapi-oss\evaluation\phase_b\PREREG_PHASE_B.md` (read §0–§4 and §8 carefully) and the sources in
`E:\Claude Projects\kapi-oss\evaluation\phase_b\SOURCES.md`. Public documentation you may read:
`E:\Claude Projects\kapi-oss\README.md`, `docs\GATE.md`, `docs\MANIFEST.md`, `docs\SPEC.md`.

## What you must NOT do

* Do not read anything under `truth_gate\`, `kapi\`, `tests\`, `examples\`, or `evaluation\` other than the two
  `phase_b` files named above. Do not read other authors' folders.
* Do not run Truth_Gate (any version, any command) and do not write any criterion code in this phase.
* Do not write files anywhere except your own folder given in your task.

## What you do in this phase

For your class, plan the cases and write, per case:

1. **A neutral brief** (public: it goes to a world author who does not know the error, the class or the source):
   * `claim`: the scientific claim, including its statistic and decision threshold, phrased as a researcher would state
     it, **without saying how the error enters** and **without saying what "claim false" means** (the world author
     applies a fixed rule: the claimed quantity at its null, everything else unchanged).
   * `data_keys`: every array the study's data dict contains: key, shape (with named axes), dtype (`float` or `bool`),
     meaning. **Encoding rules:** group, subject, trial and time structure is carried by array axes (for example shape
     `(animals, cells)` or rows in time order), never by integer codes stored in a value array; binary labels are `bool`.
   * `sizes`: the sample sizes, within the range the source describes for this kind of study; at most 300 rows (or units)
     and at most 60 features per sample (§2). If the source's studies are larger (for example thousands of voxels), use
     the cap and say so in your private note.
   * The claim must be **positive**: the criterion holds when the effect is present and the evidence supports it.
   * **Banned terms** (in any inflection, case-insensitive) anywhere in a brief: circular, double dip, leak, pseudorepl,
     coupl, spurious, non-independ, nonindepend, regression to the mean, selection bias, overfit, inflat, contaminat,
     optimis. Also avoid words that describe the faulty procedure itself (how items are chosen, how data are split).
2. **A private note** (never shown to the world author): source key; the documenting passage (quote of at most two
   sentences, or section/page); the error as it will appear in the faulty criterion, with the parameters the source
   documents; the correction in the fixed criterion; for B-2 the KAP23 subtype; anything about sizes.

## Output files (in your folder only)

* `BRIEFS.json`: a JSON list of objects `{"local_id": "...", "claim": "...", "data_keys": [{"key": "...", "shape": "...",
  "dtype": "...", "meaning": "..."}], "sizes": "..."}`. Nothing else in these objects (no source, no class, no error).
* `PRIVATE.json`: a JSON list of objects `{"local_id": "...", "source": "...", "passage": "...", "faulty": "...",
  "fixed": "...", "subtype": "...", "notes": "..."}`.
* `LOG.md`: every brief you drafted, including abandoned ones, with the reason; which sources you actually read and how
  (full text, abstract, section).

## Quantities

Follow the numbers in your task. Within your class, every case must differ from every other in at least one of: the
statistic, the data structure, the pipeline step where the error occurs, the sample-size regime. Respect the source caps
(at most 4 cases per source per class; KAP23 up to 8 in B-2).

Read the sources yourself (they are listed in `SOURCES.md` with DOIs; most have open full texts or abstracts on PubMed
Central, Europe PMC or arXiv). Base each case on a setting the source actually describes.

## Final message

Report: the number of briefs written per source (and per subtype for B-2), the number abandoned, which sources you read
and how, and any rule you found impossible to satisfy (do not bend a rule silently; report it).
