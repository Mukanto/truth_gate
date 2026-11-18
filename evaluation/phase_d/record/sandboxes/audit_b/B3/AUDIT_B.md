# AUDIT_B (B-3, part B, item o)

Answer per world file: X and Y are both yes in all 7 cases (D-008, D-023, D-040, D-056, D-062, D-067, D-068). Neither file in any case names a variable by its role in the error, adds a key that only the faulty body reads, or builds a dependence aimed at one twin. All keys in each skeleton are the brief's keys.

- D-008 X: yes. Shared haemoglobin error and a Fick-consistent venous content are ordinary; the independent copy of delivery implements only the claim's quantity in minus.
- D-008 Y: yes. The lung-uptake offset is a per-patient constant, so it does not change within-patient slopes. The relational pair (cardiac_output, vo2_expired_gas) uses the claim's own variables.
- D-023 X: yes. Linear allometry and a sex offset in body length are ordinary dependence.
- D-023 Y: yes. Locality clusters and a log-size model are ordinary; the independent copies implement the null only.
- D-040 X: yes. Linear scaling on length with a sex offset.
- D-040 Y: yes. A general-size factor and independent burial-phase offsets are ordinary; the minus uses a conditional copy of size.
- D-056 X: yes. Group mass differences and mass^0.75 scaling are realistic.
- D-056 Y: yes. Group mass differences, mass^0.67 scaling and a shared day drift are realistic. The minus docstring remark that raw VO2 still differs through body mass describes the world and names no role variable. The wording is borderline but not a leak.
- D-062 X: yes. Species ratios with a size-proportional residual.
- D-062 Y: yes. Per-species log allometry with a sex offset.
- D-067 X: yes. A standardised Gaussian model with heart-mass correlation 0.7.
- D-067 Y: yes. An allometric model with unrecorded litter clustering (no key added).
- D-068 X: yes. Population and within-population structure with a sex offset; the 'copy' implements the claim's null only.
- D-068 Y: yes. Plain linear structure with a random partial slope per population.

No helper computation was run. No criterion was called, no gate run, no validity result seen.

Files read: only inside this sandbox (FIDELITY_AUDIT_D.md, SPEC.md grep for `relational`, STRUCTURE_LOG.md of D-008, and brief.json, PRIVATE.json, faulty_body.py and fixed_body.py with the diff, X.py and Y.py of each case).
URLs read: none.
