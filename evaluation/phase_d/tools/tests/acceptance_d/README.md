# tests/acceptance_d: synthetic certificate pairs

Each folder holds `faulty.json`, `fixed.json` (a gate-style body: verdict, components[0] with flags, counts, bounds, and load_error where it applies) and `expected_flags.json` (the expected-flag list of the pair, the base list plus one `HIGH_RATE:control:<id>` per control and one `HIGH_RATE:probe:shuffle:<a>,<b>` per shuffle stream the pair declares). The folder name is the path the pair exercises. n = 200 on every stream. Flags were computed from the counts with the gate's own `check_k1`, `check_k2`, `check_k4`, `check_k5`, `check_high_rate` and `component_verdict` at alpha_family 0.05 and the study's m (below); the bounds are the gate's Wilson bounds at a = 0.05 / (2 m).

These files state no expected outcome. The designer writes `EXPECTED.md` by hand from the pre-registration text.

## a_true_b_false

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 18 of 200, bounds [0.051, 0.154]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 17 of 200, bounds [0.047, 0.148]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## a_false_k2_high_size

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200, bounds [0.226, 0.386]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 30 of 200, bounds [0.098, 0.224]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## a_false_high_rate_control

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:control:permute_y; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 80 of 200, bounds [0.318, 0.488].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:control:permute_y; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 40 of 200, bounds [0.139, 0.279].

## a_false_high_rate_noise

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:probe:noise; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 70 of 200, bounds [0.271, 0.438]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:probe:noise; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 35 of 200, bounds [0.118, 0.252]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## a_false_k5_holds_on_null

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:world:null, K2_LOW_POWER, K5_HOLDS_ON_NULL; m = 5; world:plus: 30 of 200, bounds [0.096, 0.226]; world:minus: 4 of 200, bounds [0.006, 0.065]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; world:null: 30 of 200, bounds [0.096, 0.226].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K5_HOLDS_ON_NULL; m = 5; world:plus: 30 of 200, bounds [0.096, 0.226]; world:minus: 4 of 200, bounds [0.006, 0.065]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; world:null: 14 of 200, bounds [0.036, 0.132].

## a_false_shuffle

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:probe:shuffle:x,y; m = 5; world:plus: 190 of 200, bounds [0.894, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.079]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; probe:shuffle:x,y: 90 of 200, bounds [0.362, 0.541].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:probe:shuffle:x,y; m = 5; world:plus: 190 of 200, bounds [0.894, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.079]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; probe:shuffle:x,y: 45 of 200, bounds [0.158, 0.309].

## k4_two_controls_one_meets_bounds

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K4_CONTROL_ALSO_HOLDS; m = 5; world:plus: 30 of 200, bounds [0.096, 0.226]; world:minus: 4 of 200, bounds [0.006, 0.065]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 17 of 200, bounds [0.047, 0.150]; control:permute_x: 2 of 200, bounds [0.002, 0.050].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K4_CONTROL_ALSO_HOLDS; m = 5; world:plus: 30 of 200, bounds [0.096, 0.226]; world:minus: 4 of 200, bounds [0.006, 0.065]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 1 of 200, bounds [0.001, 0.041]; control:permute_x: 17 of 200, bounds [0.047, 0.150].

## shuffle_two_pairs

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K5_HOLDS_ON_SHUFFLE; m = 6; world:plus: 30 of 200, bounds [0.095, 0.228]; world:minus: 4 of 200, bounds [0.006, 0.066]; probe:noise: 2 of 200, bounds [0.002, 0.051]; probe:zeros: 0 of 200, bounds [0.000, 0.034]; control:permute_y: 3 of 200, bounds [0.004, 0.059]; probe:shuffle:x,y: 17 of 200, bounds [0.046, 0.152]; probe:shuffle:y,x: 2 of 200, bounds [0.002, 0.051].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K5_HOLDS_ON_SHUFFLE; m = 6; world:plus: 30 of 200, bounds [0.095, 0.228]; world:minus: 4 of 200, bounds [0.006, 0.066]; probe:noise: 2 of 200, bounds [0.002, 0.051]; probe:zeros: 0 of 200, bounds [0.000, 0.034]; control:permute_y: 3 of 200, bounds [0.004, 0.059]; probe:shuffle:x,y: 1 of 200, bounds [0.001, 0.043]; probe:shuffle:y,x: 17 of 200, bounds [0.046, 0.152].

## fixed_load_error

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200, bounds [0.226, 0.386]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: no component; load_error = SyntaxError (verdict UNDEFINED).

## faulty_load_error

- Faulty twin: no component; load_error = SyntaxError (verdict UNDEFINED).
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## fixed_hard_undefined

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200, bounds [0.226, 0.386]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict UNDEFINED; flags: K1_UNDEFINED; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200 (50 hard UNDEFINED), bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## generic_only_k5_holds_on_noise

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K5_HOLDS_ON_NOISE; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 17 of 200, bounds [0.047, 0.148]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict WEAK; flags: K2_LOW_POWER; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 1 of 200, bounds [0.001, 0.039]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## declared_only

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200, bounds [0.226, 0.386]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## Round 4 folders

Seven more folders (D-R4-9), built like the ones above: flags and bounds from the gate's own check functions, n = 200.

## k2_no_separation_only

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K2_NO_SEPARATION; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 17 of 200, bounds [0.047, 0.148]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## faulty_not_nf_with_rate_flag

- Faulty twin: verdict UNDEFINED; flags: K1_UNDEFINED, K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200 (5 hard UNDEFINED), bounds [0.226, 0.386]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## faulty_nf_unexpected_mandatory

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K5_HOLDS_ON_DEGENERATE; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 17 of 200, bounds [0.047, 0.148]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## generic_and_declared

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:probe:noise, K2_HIGH_SIZE; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 60 of 200, bounds [0.226, 0.386]; probe:noise: 70 of 200, bounds [0.271, 0.438]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## fixed_missing_stream

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:control:permute_x; m = 5; world:plus: 190 of 200, bounds [0.894, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.079]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; control:permute_x: 80 of 200, bounds [0.315, 0.491].
- Fixed twin: verdict FALSIFIABLE; flags: none; m = 4; world:plus: 190 of 200, bounds [0.896, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.077]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 3 of 200, bounds [0.004, 0.055].

## fixed_hard_undefined_other_stream

- Faulty twin: verdict NOT_FALSIFIABLE; flags: K2_HIGH_SIZE; m = 5; world:plus: 190 of 200, bounds [0.894, 0.977]; world:minus: 60 of 200, bounds [0.224, 0.389]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; world:null: 4 of 200, bounds [0.006, 0.065].
- Fixed twin: verdict UNDEFINED; flags: K1_UNDEFINED; m = 5; world:plus: 190 of 200, bounds [0.894, 0.977]; world:minus: 6 of 200, bounds [0.011, 0.079]; probe:noise: 2 of 200, bounds [0.002, 0.050]; probe:zeros: 0 of 200, bounds [0.000, 0.032]; control:permute_y: 3 of 200, bounds [0.004, 0.057]; world:null: 4 of 200 (50 hard UNDEFINED), bounds [0.006, 0.065].

## fixed_k4_blocks_high_rate_control

- Faulty twin: verdict NOT_FALSIFIABLE; flags: HIGH_RATE:control:permute_y, K2_LOW_POWER, K4_CONTROL_ALSO_HOLDS; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 80 of 200, bounds [0.318, 0.488].
- Fixed twin: verdict NOT_FALSIFIABLE; flags: K2_LOW_POWER, K4_CONTROL_ALSO_HOLDS; m = 4; world:plus: 30 of 200, bounds [0.098, 0.224]; world:minus: 4 of 200, bounds [0.006, 0.063]; probe:noise: 2 of 200, bounds [0.002, 0.048]; probe:zeros: 0 of 200, bounds [0.000, 0.030]; control:permute_y: 17 of 200, bounds [0.047, 0.148].
