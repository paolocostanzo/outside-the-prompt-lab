# RQ1 results (D44 sample)

Sampled cases: 120; frame sizes {'agent client': 100, 'MCP server or connector': 210, 'SDK': 20}.

| Rater | Share in classes 1–3 (stratified) | 95% interval (exact, conservative) | Unweighted |
|---|---|---|---|
| R0 | 90.1% | 77.9%–95.8% | 90.0% |
| Model majority | 92.6% | 81.2%–98.2% | 92.5% |

**H1: supported, interval above 60%.**

**Robustness (D41 point 6): NOT robust** — a contested-case variant changes the verdict (D41 p6: contested cases against H1: not supported; D41 p6: contested cases in favour of H1: supported, interval above 60%).

H1a: Fleiss' κ (all raters) = 0.4578425873995138 on 120 cases (0 left out); holds: False. Without R2: 0.4077665699813848.

## Variants (each alone against the primary)

| Variant | R0 | Model majority | Verdict |
|---|---|---|---|
| D45/D41 p1: mixed bundles as class 4 | 88.4% | 90.9% | supported, interval above 60% |
| D41 p6: contested cases against H1 | 32.6% | 32.6% | not supported |
| D41 p6: contested cases in favour of H1 | 97.5% | 97.5% | supported, interval above 60% |
| D43: model majority without R2 | 90.1% | 73.4% | supported on the point estimate only |
| D44 p1: without the flagged (I?) cases | 90.0% | 92.5% | supported, interval above 60% |
| D44 p5: without late-ineligible cases | 90.0% | 92.5% | supported, interval above 60% |
| D44 p6: labelled cases only | 90.1% | 94.8% | supported, interval above 60% |
| D44 p6: equal weights for the three product types | 92.0% | 93.3% | supported, interval above 60% |
| D41 p7: corrected summaries | n/a | n/a | no summary was corrected after the runs (no rq1-summary-corrections.json) |
| D44 p5: corrected-disclosure count | n/a | n/a | no grouping error in rq1-frame-erratum.csv |

## Each model rater

| Model | Share (stratified) | Interval | Unlabelled | Invalid answers | Cohen's κ vs R0 (n, left out) |
|---|---|---|---|---|---|
| qwen3.8:27b-q8_0 | 95.0% | 84.2%–98.2% | 0 | 0.0% | 0.6536796536796537 (120, 0) |
| gemma4:26b-a4b-it-q8_0 | 90.9% | 79.4%–95.8% | 0 | 2.2% | 0.5129493621955932 (120, 0) |
| nemotron-3.5-lightning:30b-a3b-q4_K_M | 99.2% | 90.3%–99.7% | 0 | 0.0% | 0.32790224032586557 (120, 0) |

## Run-to-run instability (preregistration section 4)

| Model | Cases whose valid answers differ | Cases with an invalid answer |
|---|---|---|
| qwen3.8:27b-q8_0 | 0 | 0 |
| gemma4:26b-a4b-it-q8_0 | 4 (RQ1-0080, RQ1-0285, RQ1-0297, RQ1-0306) | 5 (RQ1-0016, RQ1-0130, RQ1-0156, RQ1-0288, RQ1-0327) |
| nemotron-3.5-lightning:30b-a3b-q4_K_M | 0 | 0 |

## By product type

| Type | Sampled | R0 in stratum | Majority in stratum | Frame without it: R0 / majority | H1 depends on it |
|---|---|---|---|---|---|
| agent client | 37 | 83.8% | 83.8% | 92.8% / 96.4% | False |
| MCP server or connector | 76 | 92.1% | 96.1% | 86.5% / 86.5% | False |
| SDK | 7 (not interpreted) | 100.0% | 100.0% | 89.4% / 92.1% | False |

Contested cases: 78. Mixed bundles: ['RQ1-0023', 'RQ1-0130']. Late ineligible: ['RQ1-0022']. Unlabelled: {'R0': [], 'model majority': ['RQ1-0276', 'RQ1-0296', 'RQ1-0311']}. Source split (not interpreted): timeline cases sampled 1, in the frame ['RQ1-0215'].
