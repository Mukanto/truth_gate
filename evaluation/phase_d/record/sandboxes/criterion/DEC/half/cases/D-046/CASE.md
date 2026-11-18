# D-046 (DEC-07)

## 1. Case
- Case id: D-046 (local id DEC-07); class B-6; tag (mechanism): units-not-independent; statistic family: regression-slope; subtype: None.

## 2. Source
- Source key: LAZ10. Documenting passage: "clearly the rat that the observation came from partly determines what that value is." (hierarchical example: 2 rats x 100 CA3 cells = 200 data points, only 2 rats are independent units)
- Who read it and how: read by the brief author in the Europe PMC full-text XML (first 100000 of 166051 characters); I did not re-read the source and fetched no URL.

## 3. Brief
Claim: Ten animals each received a different dose of a drug, and the response amplitude (in mV) of 100 CA3 cells was recorded in each animal. Claim: response increases with dose, that is, the slope of an animal's mean cell response on dose, across animals, is positive, judged by a one-sided test at the 0.05 level.

Data keys:
  - `response`, (animals, cells), float: response amplitude in mV of each recorded CA3 cell
  - `dose`, (animals,), float: dose of the drug given to each animal

Sizes: {"animals": 10, "cells": 100}

## 4. Mapping
Faulty (`D-046/faulty_body.py`): line 113 carries the error: the dose of each animal is repeated for each of its cells and the one-sided t test of the least-squares slope uses all 1000 cell values as replicates (df = 998). Helper `_slope_p` (shared, line 78) does the regression; line 116 applies p < 0.05. Documented in the private note and LAZ10 (the animal a cell comes from partly determines the value; 2 rats x 100 cells).

Fixed (`D-046/fixed_body.py`): line 113 only: `_slope_p(x, y.mean(axis=1))`, the slope of the animal mean response on dose over the 10 animals (df = 8). Everything else is identical.

Estimand: the slope of the animal mean response on dose with animals as replicates (the same expected slope in a balanced design).

## 5. Allowed-guard minimum used
Private note minimum: 3. Used: 3 units (cells in the faulty body, animals in the fixed body); non-finite values; zero variance of dose, or a zero residual variance (standard error zero).

## 6. Runs of the fixed body
Fixed-body revisions: 0 (no change after the first version). Runs: self-generated random-intercept data with slope 0.2 (10 animals, 100 cells): True; 0.1 ms per call (3 calls + 1 repeat, equal); the slope p-value of `_slope_p` matched scipy.stats.linregress (alternative greater) to better than 1e-15. Every run returned a Python bool. Helper check (shared t-tail code): maximum absolute difference to scipy.stats.t.sf over 110 (t, df) pairs 6.7e-14; critical t for p = 0.001 matches scipy at df 4 and 9. Guard runs (fixed bodies only: empty selection or cell, group of one, constant dose or exposure, non-finite values, zero variance) all returned None. Scripts: `work/run_fixed.py`, `work/edge_fixed.py`. The faulty body: syntax check and a text-only AST form check (`work/form_check.py`, no import) only; never run.

## 7. Deviations from the private note and problems
The p-values of the fixed body (and of the shared helpers) come from a hand-written regularised incomplete beta function (Lanczos log-gamma, continued fraction), because a body may import only numpy. The zero-residual guard (standard error zero) is my reading of "zero variance" for the test statistic. Problems: none.
