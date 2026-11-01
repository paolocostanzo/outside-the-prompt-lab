# RQ1 — prevalence-robust agreement (POST HOC, exploratory)

**Post hoc.** Written on 1 Nov 2026, after all RQ1 results were known, in answer to reviewers (kappa and the prevalence paradox: about 90% of labels in classes 1–3). Not preregistered. **It does not change H1a**: the preregistered criterion, Fleiss' κ ≥ 0.6 over R0 and the three models on four classes, is not met (κ = 0.458). AC1 and PABAK are reported alongside κ, not as substitutes.

Cases: 120. Bootstrap: percentile, resampling cases with replacement (explore_disagreement.boot), 2000 resamples, seed 20261028, fresh random.Random(seed) for each interval.

## Checks against the reported figures (all must match; the script stops otherwise)

| Figure | Recomputed | Saved / reported | Match |
|---|---|---|---|
| Fleiss kappa, four classes (RESULTS-RQ1.json H1a.fleiss_all_raters) | 0.4578425873995138 | 0.4578425873995138 | yes |
| cases used by Fleiss kappa (RESULTS-RQ1.json H1a.n_complete) | 120 | 120 | yes |
| Fleiss kappa, binary (EXPLORATORY-DISAGREEMENT.json; paper 0.48) | 0.47851851851851845 | 0.47851851851851845 | yes |
| Fleiss kappa, binary, bootstrap low (paper 0.27) | 0.26675094816687744 | 0.26675094816687744 | yes |
| Fleiss kappa, binary, bootstrap high (paper 0.64) | 0.6404494382022474 | 0.6404494382022474 | yes |
| Fleiss kappa, four classes, bootstrap low (paper 0.35) | 0.3457965154578288 | 0.3457965154578288 | yes |
| Fleiss kappa, four classes, bootstrap high (paper 0.55) | 0.5541444919028803 | 0.5541444919028803 | yes |
| R0 vs majority, cases with a majority (paper 117) | 117 | 117 | yes |
| R0 vs majority, binary agreements (paper 113 of 117) | 113 | 113 | yes |
| R0 vs majority, four-class agreements (paper 104 of 117) | 104 | 104 | yes |
| R0 vs majority, binary raw agreement (EXPLORATORY-DISAGREEMENT.json) | 0.9658119658119658 | 0.9658119658119658 | yes |
| R0 vs majority, binary Cohen kappa (EXPLORATORY-DISAGREEMENT.json) | 0.7328767123287672 | 0.7328767123287672 | yes |
| R0 vs majority, binary PABAK (EXPLORATORY-DISAGREEMENT.json) | 0.9316239316239316 | 0.9316239316239316 | yes |

## Gwet's AC1, R0 + three models (R0, gemma4:26b-a4b-it-q8_0, nemotron-3.5-lightning:30b-a3b-q4_K_M, qwen3.8:27b-q8_0), 120 cases (same as the reported Fleiss' κ)

| Question | Fleiss' κ (reported) | Gwet's AC1 [95%] |
|---|---|---|
| Four classes | 0.458 | 0.770 [0.71, 0.83] |
| Binary (P = 1–3 vs M = 4) | 0.479 | 0.931 [0.89, 0.97] |

Share labelled P per rater: R0 90.0%, gemma4:26b-a4b-it-q8_0 90.8%, nemotron-3.5-lightning:30b-a3b-q4_K_M 99.2%, qwen3.8:27b-q8_0 95.0%.

## R0 vs model majority (117 cases with a majority; 3 without)

| Question | Raw agreement | Cohen's κ | PABAK [95%] | AC1 [95%] |
|---|---|---|---|---|
| Four classes | 104/117 = 0.889 | 0.649 | 0.852 [0.77, 0.92] | 0.876 [0.81, 0.94] |
| Binary (P vs M) | 113/117 = 0.966 | 0.733 | 0.932 [0.86, 0.98] | 0.961 [0.92, 0.99] |

PABAK four classes = (4·p_o − 1)/3; binary = 2·p_o − 1.

## Confusion table, rows R0, columns model majority

| R0 \ majority | 1 | 2 | 3 | 4 | no majority | total |
|---|---|---|---|---|---|---|
| 1 | 6 | 0 | 0 | 0 | 0 | 6 |
| 2 | 0 | 2 | 0 | 0 | 0 | 2 |
| 3 | 8 | 1 | 90 | 0 | 1 | 100 |
| 4 | 0 | 1 | 3 | 6 | 2 | 12 |

## Per-class agreement (cases with a majority)

| Class | R0 count (with majority) | Majority count | Both | Specific agreement | Share of R0's class confirmed | Share of majority's class confirmed |
|---|---|---|---|---|---|---|
| 1 | 6 (6) | 14 | 6 | 0.60 | 1.00 | 0.43 |
| 2 | 2 (2) | 4 | 2 | 0.67 | 1.00 | 0.50 |
| 3 | 100 (99) | 93 | 90 | 0.94 | 0.91 | 0.97 |
| 4 | 12 (10) | 6 | 6 | 0.75 | 0.60 | 1.00 |

Cases without a model majority: RQ1-0276, RQ1-0296, RQ1-0311.
