# Independent recomputation of the RQ1 analysis by Codex (27 Oct 2026)

Final report of a read-only Codex session (model gpt-6.1-sol, finished 2026-10-27 22:25 UTC) that re-parsed all raw model answers and recomputed every RQ1 estimate without importing the repository's analysis code. Copied verbatim on 1 Nov 2026 at the author's request; only this final report is included (not the session transcript). Its two reporting findings were addressed in commit 7421a8f (D41.6 robustness statement and run-to-run instability).

```json
{
  "verdict": "REVISE",
  "summary": "Independent recalculation reproduced the numerical results. Two reporting omissions remain; no numerical correctness defect was found.",
  "findings": [
    {
      "id": "RQ1-A5-001",
      "severity": "medium",
      "path": "otp-lab-q4/preregistration/rq1/analyze.py:193",
      "evidence": "D41.6 requires explicitly reporting H1 as not robust when the contested-case sensitivity changes the verdict. RESULTS-RQ1.md headlines H1 as supported, while assigning contested cases against H1 reduces both estimates to 32.5842% and changes the verdict to not supported. The table contains these results, but neither output explicitly states the required robustness conclusion.",
      "fix": "Add a derived robustness conclusion to RESULTS-RQ1.json and prominently state in RESULTS-RQ1.md that primary H1 is supported but is not robust to the preregistered contested-case sensitivity."
    },
    {
      "id": "RQ1-A5-002",
      "severity": "low",
      "path": "otp-lab-q4/preregistration/rq1/analyze.py:202",
      "evidence": "Preregistration §4 requires reporting run-to-run instability. The aggregate outputs report invalid-answer rates but omit instability. Gemma has four cases with differing valid classes: RQ1-0080 [1,4,4], RQ1-0297 [3,4,4], RQ1-0306 [3,1,1], and RQ1-0285 [1,3,3]. Five additional cases contain invalid answers, making nine cases marked stable:false in the raw file.",
      "fix": "Report per-model counts and case IDs for differing valid classes, separately from cases containing invalid answers, in both aggregate outputs."
    }
  ],
  "coverage": [
    "Verified the plan SHA-256 and all 15 document hashes listed in the plan.",
    "Independently parsed all 1,080 raw answers and reproduced all 360 model modal labels, invalid counts, tie flags and stability flags without importing repository analysis code.",
    "Reproduced all 41 estimate blocks, including exact fractions, hypergeometric Bonferroni intervals, product/source domains and every listed sensitivity variant. No numerical differences remained.",
    "Reproduced Fleiss κ 0.4578425873995138, without-R2 κ 0.4077665699813848, and all three Cohen κ values.",
    "Confirmed 78 contested cases, two mixed bundles, one late-ineligible case and three cases without model majority.",
    "Reconstructed all 330 sample rows. The allocation 37/76/7 follows the frozen sampler's tie-break between equal client/MCP allocation remainders.",
    "Traced sample_frame.py, classify.py, r0_sheet.py, r0_report.py, GPU runner/ETA callers and the manuscript consumer beyond the plan's file list.",
    "Confirmed frozen frame/estimator/sampler byte equality and R0 equality with commit 090ece7. Local Git chronology places R0, summaries, flags, erratum and applicable analysis rules before the recorded confirmatory run."
  ],
  "limitations": [
    "No tests were run, files edited or work delegated. Read-only standalone calculations were used for reproduction.",
    "Remote drand values, GitHub push events and Internet Archive captures were not independently authenticated; sampling verification used their locally recorded values.",
    "Local commits and recorded timestamps support ordering but cannot prove that no unrecorded earlier model run or data use occurred.",
    "Primary-source eligibility, summary fidelity and Italian translations were not re-audited case by case."
  ]
}```
