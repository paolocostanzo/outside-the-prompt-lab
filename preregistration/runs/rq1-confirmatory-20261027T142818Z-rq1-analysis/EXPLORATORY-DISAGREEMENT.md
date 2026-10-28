# RQ1 — where the raters disagree (EXPLORATORY, D51)

Not preregistered; written after the confirmatory results. No confirmatory figure or verdict changes.
Cases: 120. Bootstrap: 2000 resamples over cases, seed 20261028.

## Agreement on four classes and on the question H1 asks (product 1–3 vs model 4)

| Pair | n | 4 classes: agreement | 4 classes: κ [95%] | Binary: agreement | Binary: κ [95%] | Binary: PABAK |
|---|---|---|---|---|---|---|
| R0 vs gemma4:26b-a4b-it-q8_0 | 120 | 0.825 | 0.513 [0.33, 0.67] | 0.942 | 0.663 [0.38, 0.87] | 0.883 |
| R0 vs nemotron-3.5-lightning:30b-a3b-q4_K_M | 120 | 0.725 | 0.328 [0.19, 0.47] | 0.908 | 0.141 [0.00, 0.44] | 0.817 |
| R0 vs qwen3.8:27b-q8_0 | 120 | 0.900 | 0.654 [0.47, 0.80] | 0.950 | 0.643 [0.33, 0.88] | 0.900 |
| R0 vs model majority | 117 | 0.889 | 0.649 [0.47, 0.81] | 0.966 | 0.733 [0.38, 0.94] | 0.932 |
| Fleiss, R0 + three models | 120 | – | 0.458 [0.35, 0.55] | – | 0.479 [0.27, 0.64] | – |

Share labelled 'product' (1–3) per rater: R0 90.0%, qwen3.8:27b-q8_0 95.0%, gemma4:26b-a4b-it-q8_0 90.8%, nemotron-3.5-lightning:30b-a3b-q4_K_M 99.2%. With a share this far from 50%, κ is low even at high raw agreement (prevalence effect); PABAK is shown for that reason and is not a substitute for κ.

## Which class pairs the disagreements are

| Pair | Disagreements by class pair (count) |
|---|---|
| R0 vs gemma4:26b-a4b-it-q8_0 | 1-3: 12, 3-4: 5, 1-2: 1, 1-4: 1, 2-3: 1, 2-4: 1 |
| R0 vs nemotron-3.5-lightning:30b-a3b-q4_K_M | 1-3: 20, 1-4: 5, 3-4: 5, 2-3: 2, 2-4: 1 |
| R0 vs qwen3.8:27b-q8_0 | 1-3: 5, 3-4: 3, 1-4: 2, 2-4: 1, 2-3: 1 |
| R0 vs model majority | 1-3: 8, 3-4: 3, 2-3: 1, 2-4: 1 |

## Specific agreement per class (2·both / (count R0 + count other))

| Pair | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| R0 vs gemma4:26b-a4b-it-q8_0 | 0.30 | 0.57 | 0.91 | 0.70 |
| R0 vs nemotron-3.5-lightning:30b-a3b-q4_K_M | 0.32 | 0.57 | 0.85 | 0.15 |
| R0 vs qwen3.8:27b-q8_0 | 0.59 | 0.50 | 0.96 | 0.67 |
| R0 vs model majority | 0.60 | 0.67 | 0.94 | 0.75 |

## Confusion tables (rows R0, columns the other rater)

**R0 vs gemma4:26b-a4b-it-q8_0**

| R0 \ other | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 3 | 1 | 1 | 1 |
| 2 | 0 | 2 | 0 | 0 |
| 3 | 11 | 1 | 86 | 2 |
| 4 | 0 | 1 | 3 | 8 |

**R0 vs nemotron-3.5-lightning:30b-a3b-q4_K_M**

| R0 \ other | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 6 | 0 | 0 | 0 |
| 2 | 0 | 2 | 0 | 0 |
| 3 | 20 | 2 | 78 | 0 |
| 4 | 5 | 1 | 5 | 1 |

**R0 vs qwen3.8:27b-q8_0**

| R0 \ other | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 5 | 0 | 1 | 0 |
| 2 | 0 | 1 | 1 | 0 |
| 3 | 4 | 0 | 96 | 0 |
| 4 | 2 | 1 | 3 | 6 |

**R0 vs model majority**

| R0 \ other | 1 | 2 | 3 | 4 |
|---|---|---|---|---|
| 1 | 6 | 0 | 0 | 0 |
| 2 | 0 | 2 | 0 | 0 |
| 3 | 8 | 1 | 90 | 0 |
| 4 | 0 | 1 | 3 | 6 |

## Disagreement R0 vs model majority, by group

| Group | Cases | Disagree (4 classes) | Disagree (binary) | No model majority |
|---|---|---|---|---|
| flagged (D41) | 74 | 10 | 3 | 3 |
| not flagged | 46 | 3 | 1 | 0 |
| MCP server or connector | 76 | 8 | 3 | 0 |
| SDK | 7 | 1 | 0 | 0 |
| agent client | 37 | 4 | 1 | 3 |

Cases where R0 and the model majority disagree on product vs model: RQ1-0060, RQ1-0175, RQ1-0193, RQ1-0325.
