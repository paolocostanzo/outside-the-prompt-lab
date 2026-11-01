#!/usr/bin/env python3
"""RQ1, POST HOC and EXPLORATORY (not preregistered): prevalence-robust agreement. Written on 1 Nov 2026, after all RQ1
results were known, in answer to reviewers who note that kappa suffers from the prevalence paradox (about 90% of labels fall
in classes 1-3). It changes no confirmatory figure and no verdict: H1a (preregistered Fleiss' kappa >= 0.6) stays not met.

    python3 -I preregistration/rq1/agreement-posthoc/agreement.py [RUN_DIR] [OUT_DIR]

RUN_DIR defaults to the confirmatory run preregistration/runs/rq1-confirmatory-20261027T142818Z; OUT_DIR defaults to this
script's directory. Inputs are read exactly as analyze.py / explore_disagreement.py read them (classify.load_models with the
frozen roster and digests, rq1-r0.json checked against the run manifest, the sample recomputed from the frozen frame and seed
and checked against rq1-sample.csv); those scripts are imported, never changed.

Before anything new is computed, the figures already reported are recomputed and must equal the saved values (the script
stops otherwise): Fleiss' kappa four classes (RESULTS-RQ1.json, H1a), and from EXPLORATORY-DISAGREEMENT.json the binary
Fleiss' kappa with its bootstrap interval, the four-class Fleiss interval, and R0 vs model majority binary raw agreement
(113/117 in the paper), four-class raw agreement (104/117), Cohen's kappa and PABAK.

New, post hoc: Gwet's AC1 (multi-rater, R0 + the three models, the same 120 cases as the reported Fleiss' kappa; four classes
and binary P = classes 1-3 vs M = class 4) and AC1 for R0 vs model majority; PABAK R0 vs model majority (binary and four
classes); the 4x5 confusion table R0 x model majority (with a 'no majority' column) and per-class agreement. Intervals:
percentile bootstrap over cases, 2000 resamples, seed 20261028 (the convention of explore_disagreement.py, whose boot()
is reused); here every interval starts from a fresh random.Random(20261028), so each one is reproducible on its own.
"""
import json, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
RQ1 = HERE.parent
sys.path.insert(0, str(RQ1)); sys.path.insert(0, str(RQ1.parent))
import classify  # noqa: E402
import analyze as an  # noqa: E402
import explore_disagreement as ed  # noqa: E402

DEFAULT_RUN = RQ1.parent / "runs" / "rq1-confirmatory-20261027T142818Z"
CLASSES = ed.CLASSES
SEED, RESAMPLES = ed.SEED, ed.RESAMPLES
WRITTEN = "2026-11-01"


def ac1_multi(ratings, cats):
    """Gwet's AC1 for any number of raters (each case rated by all raters): Pa = mean_i sum_k r_ik(r_ik-1)/(r(r-1)),
    pe = (1/(K-1)) sum_k pi_k(1-pi_k), pi_k = mean_i r_ik/r; AC1 = (Pa-pe)/(1-pe). None when undefined."""
    N = len(ratings)
    if N == 0:
        return None
    K = len(cats)
    pa, pi = 0.0, {c: 0.0 for c in cats}
    for labels in ratings.values():
        r = len(labels)
        for c in cats:
            n_c = sum(v == c for v in labels)
            pa += n_c * (n_c - 1) / (r * (r - 1))
            pi[c] += n_c / r
    pa /= N
    pe = sum((pi[c] / N) * (1 - pi[c] / N) for c in cats) / (K - 1)
    return (pa - pe) / (1 - pe) if pe < 1 else None


def pabak_k(po, k):
    """PABAK for k categories: (k*po - 1)/(k - 1); 2*po - 1 for two."""
    return None if po is None else (k * po - 1) / (k - 1)


def interval(fn, keys):
    return ed.boot(fn, keys, random.Random(SEED))


def check(name, got, want, tol=1e-12):
    ok = got is not None and want is not None and abs(got - want) <= tol
    if not ok:
        sys.exit(f"check failed: {name}: recomputed {got}, saved {want}")
    return {"recomputed": got, "saved": want, "match": True}


def analyse(sample, r0, models, saved_results, saved_explore, explore_recomputed):
    names = sorted(models)
    maj = {c: an.majority([models[m].get(c) for m in names]) for c in sample}
    four = {"R0": r0, **{m: models[m] for m in names}}
    complete = [c for c in sample if all(four[r].get(c) for r in four)]
    both = [c for c in sample if r0[c] and maj[c]]
    bin_four = {r: {c: ed.binary(v) for c, v in lab.items()} for r, lab in four.items()}
    r0b, majb = {c: ed.binary(r0[c]) for c in sample}, {c: ed.binary(maj[c]) for c in sample}

    # 1. Checks against the saved values.
    fk4 = classify.fleiss({c: [four[r][c] for r in four] for c in complete})
    fk2 = ed.fleiss_any({c: [bin_four[r][c] for r in four] for c in complete}, ("P", "M"))
    agree4 = sum(r0[c] == maj[c] for c in both)
    agree2 = sum(r0b[c] == majb[c] for c in both)
    se, xe = saved_explore, explore_recomputed
    checks = {
        "Fleiss kappa, four classes (RESULTS-RQ1.json H1a.fleiss_all_raters)":
            check("fleiss four", fk4, saved_results["H1a"]["fleiss_all_raters"]),
        "cases used by Fleiss kappa (RESULTS-RQ1.json H1a.n_complete)":
            check("n complete", len(complete), saved_results["H1a"]["n_complete"]),
        "Fleiss kappa, binary (EXPLORATORY-DISAGREEMENT.json; paper 0.48)":
            check("fleiss binary", fk2, se["binary"]["Fleiss, R0 + three models"]["kappa"]),
        "Fleiss kappa, binary, bootstrap low (paper 0.27)":
            check("fleiss binary low", xe["binary"]["Fleiss, R0 + three models"]["kappa_95"]["low"],
                  se["binary"]["Fleiss, R0 + three models"]["kappa_95"]["low"]),
        "Fleiss kappa, binary, bootstrap high (paper 0.64)":
            check("fleiss binary high", xe["binary"]["Fleiss, R0 + three models"]["kappa_95"]["high"],
                  se["binary"]["Fleiss, R0 + three models"]["kappa_95"]["high"]),
        "Fleiss kappa, four classes, bootstrap low (paper 0.35)":
            check("fleiss four low", xe["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["low"],
                  se["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["low"]),
        "Fleiss kappa, four classes, bootstrap high (paper 0.55)":
            check("fleiss four high", xe["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["high"],
                  se["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["high"]),
        "R0 vs majority, cases with a majority (paper 117)":
            check("n both", len(both), se["binary"]["R0 vs model majority"]["n"]),
        "R0 vs majority, binary agreements (paper 113 of 117)": check("agree2", agree2, 113),
        "R0 vs majority, four-class agreements (paper 104 of 117)": check("agree4", agree4, 104),
        "R0 vs majority, binary raw agreement (EXPLORATORY-DISAGREEMENT.json)":
            check("po2", agree2 / len(both), se["binary"]["R0 vs model majority"]["percent_agreement"]),
        "R0 vs majority, binary Cohen kappa (EXPLORATORY-DISAGREEMENT.json)":
            check("cohen2", classify.cohen(r0b, majb)[0], se["binary"]["R0 vs model majority"]["cohen_kappa"]),
        "R0 vs majority, binary PABAK (EXPLORATORY-DISAGREEMENT.json)":
            check("pabak2", pabak_k(agree2 / len(both), 2), se["binary"]["R0 vs model majority"]["pabak"]),
    }

    # 2. Gwet's AC1, multi-rater, same raters and cases as the reported Fleiss' kappa.
    ac1_4 = lambda ks: ac1_multi({i: [four[r][k] for r in four] for i, k in enumerate(ks)}, CLASSES)
    ac1_2 = lambda ks: ac1_multi({i: [bin_four[r][k] for r in four] for i, k in enumerate(ks)}, ("P", "M"))
    ac1_pair4 = lambda ks: ac1_multi({i: [r0[k], maj[k]] for i, k in enumerate(ks)}, CLASSES)
    ac1_pair2 = lambda ks: ac1_multi({i: [r0b[k], majb[k]] for i, k in enumerate(ks)}, ("P", "M"))
    po = lambda lab_a, lab_b: (lambda ks: sum(lab_a[k] == lab_b[k] for k in ks) / len(ks))
    pab4 = lambda ks: pabak_k(po(r0, maj)(ks), 4)
    pab2 = lambda ks: pabak_k(po(r0b, majb)(ks), 2)
    prevalence = {r: sum(bin_four[r][c] == "P" for c in complete) / len(complete) for r in four}

    ac1 = {"raters": list(four), "n": len(complete),
           "four_class": {"ac1": ac1_4(complete), "ac1_95": interval(ac1_4, complete), "fleiss_kappa": fk4},
           "binary": {"ac1": ac1_2(complete), "ac1_95": interval(ac1_2, complete), "fleiss_kappa": fk2},
           "share_P_per_rater": prevalence}
    pair = {"n": len(both), "left_out_no_majority": len(sample) - len(both),
            "four_class": {"raw_agreement": agree4 / len(both), "agreements": agree4,
                           "cohen_kappa": classify.cohen({c: r0[c] for c in both}, {c: maj[c] for c in both})[0],
                           "pabak": pab4(both), "pabak_95": interval(pab4, both),
                           "ac1": ac1_pair4(both), "ac1_95": interval(ac1_pair4, both)},
            "binary": {"raw_agreement": agree2 / len(both), "agreements": agree2,
                       "cohen_kappa": classify.cohen(r0b, majb)[0],
                       "pabak": pab2(both), "pabak_95": interval(pab2, both),
                       "ac1": ac1_pair2(both), "ac1_95": interval(ac1_pair2, both)}}

    # 3. Confusion table R0 x model majority (rows R0, columns majority + 'no majority') and per-class agreement.
    cols = [*CLASSES, None]
    table = {r: {("no majority" if c is None else c): sum(1 for k in sample if r0[k] == r and maj[k] == c) for c in cols}
             for r in CLASSES}
    per_class = {}
    for c in CLASSES:
        n_r0 = sum(r0[k] == c for k in sample)
        n_r0_with = sum(r0[k] == c for k in both)
        n_maj = sum(maj[k] == c for k in both)
        agree = table[c][c]
        per_class[c] = {"R0 count": n_r0, "R0 count with a majority": n_r0_with, "majority count": n_maj, "both": agree,
                        "specific_agreement": (2 * agree / (n_r0_with + n_maj)) if n_r0_with + n_maj else None,
                        "share of R0's class confirmed by majority": (agree / n_r0_with) if n_r0_with else None,
                        "share of majority's class confirmed by R0": (agree / n_maj) if n_maj else None}
    return {"post_hoc": True, "exploratory": True, "written": WRITTEN,
            "h1a_unchanged": "H1a (preregistered: Fleiss' kappa >= 0.6, all four raters, four classes) is not met; "
                             "nothing here changes that verdict.",
            "bootstrap": {"method": "percentile, resampling cases with replacement (explore_disagreement.boot)",
                          "resamples": RESAMPLES, "seed": SEED, "rng": "fresh random.Random(seed) for each interval"},
            "n_sampled": len(sample), "checks_against_saved": checks, "gwet_ac1_multirater": ac1,
            "R0_vs_model_majority": pair, "confusion_R0_x_majority": table, "per_class_agreement": per_class,
            "no_majority_cases": sorted(c for c in sample if maj[c] is None)}


def f(x, d=3):
    return "n/a" if x is None else f"{x:.{d}f}"


def ci(c):
    return "n/a" if not c else f"[{c['low']:.2f}, {c['high']:.2f}]"


def markdown(res):
    a, p = res["gwet_ac1_multirater"], res["R0_vs_model_majority"]
    out = ["# RQ1 — prevalence-robust agreement (POST HOC, exploratory)", "",
           f"**Post hoc.** Written on 1 Nov 2026, after all RQ1 results were known, in answer to reviewers (kappa and the "
           f"prevalence paradox: about 90% of labels in classes 1–3). Not preregistered. **It does not change H1a**: the "
           f"preregistered criterion, Fleiss' κ ≥ 0.6 over R0 and the three models on four classes, is not met "
           f"(κ = {f(a['four_class']['fleiss_kappa'])}). AC1 and PABAK are reported alongside κ, not as substitutes.", "",
           f"Cases: {res['n_sampled']}. Bootstrap: {res['bootstrap']['method']}, {RESAMPLES} resamples, seed {SEED}, "
           f"{res['bootstrap']['rng']}.", "",
           "## Checks against the reported figures (all must match; the script stops otherwise)", "",
           "| Figure | Recomputed | Saved / reported | Match |", "|---|---|---|---|"]
    for k, v in res["checks_against_saved"].items():
        out.append(f"| {k} | {v['recomputed']} | {v['saved']} | {'yes' if v['match'] else 'NO'} |")
    out += ["", f"## Gwet's AC1, R0 + three models ({', '.join(a['raters'])}), {a['n']} cases (same as the reported Fleiss' κ)", "",
            "| Question | Fleiss' κ (reported) | Gwet's AC1 [95%] |", "|---|---|---|",
            f"| Four classes | {f(a['four_class']['fleiss_kappa'])} | {f(a['four_class']['ac1'])} {ci(a['four_class']['ac1_95'])} |",
            f"| Binary (P = 1–3 vs M = 4) | {f(a['binary']['fleiss_kappa'])} | {f(a['binary']['ac1'])} {ci(a['binary']['ac1_95'])} |",
            "", "Share labelled P per rater: " + ", ".join(f"{r} {v:.1%}" for r, v in a["share_P_per_rater"].items()) + ".", "",
            f"## R0 vs model majority ({p['n']} cases with a majority; {p['left_out_no_majority']} without)", "",
            "| Question | Raw agreement | Cohen's κ | PABAK [95%] | AC1 [95%] |", "|---|---|---|---|---|"]
    for lab, key in (("Four classes", "four_class"), ("Binary (P vs M)", "binary")):
        r = p[key]
        out.append(f"| {lab} | {r['agreements']}/{p['n']} = {f(r['raw_agreement'])} | {f(r['cohen_kappa'])} | "
                   f"{f(r['pabak'])} {ci(r['pabak_95'])} | {f(r['ac1'])} {ci(r['ac1_95'])} |")
    out += ["", "PABAK four classes = (4·p_o − 1)/3; binary = 2·p_o − 1.", "",
            "## Confusion table, rows R0, columns model majority", "",
            "| R0 \\ majority | 1 | 2 | 3 | 4 | no majority | total |", "|---|---|---|---|---|---|---|"]
    for r, row in res["confusion_R0_x_majority"].items():
        out.append(f"| {r} | " + " | ".join(str(v) for v in row.values()) + f" | {sum(row.values())} |")
    out += ["", "## Per-class agreement (cases with a majority)", "",
            "| Class | R0 count (with majority) | Majority count | Both | Specific agreement | Share of R0's class confirmed | Share of majority's class confirmed |",
            "|---|---|---|---|---|---|---|"]
    for c, v in res["per_class_agreement"].items():
        out.append(f"| {c} | {v['R0 count']} ({v['R0 count with a majority']}) | {v['majority count']} | {v['both']} | "
                   f"{f(v['specific_agreement'], 2)} | {f(v['share of R0' + chr(39) + 's class confirmed by majority'], 2)} | "
                   f"{f(v['share of majority' + chr(39) + 's class confirmed by R0'], 2)} |")
    out += ["", f"Cases without a model majority: {', '.join(res['no_majority_cases']) or 'none'}."]
    return "\n".join(out) + "\n"


def main(run_dir=None, out_dir=None):
    run_dir = pathlib.Path(run_dir or DEFAULT_RUN).resolve()
    out_dir = pathlib.Path(out_dir) if out_dir else HERE
    analysis_dir = run_dir.parent / (run_dir.name + "-rq1-analysis")
    models, manifest = classify.load_models(run_dir)
    if manifest.get("r0_sha256") != classify.sha256_file(RQ1 / "rq1-r0.json"):
        sys.exit("rq1-r0.json differs from the R0 file recorded in the run manifest")
    _, sample_rows, provenance = ed.verified_inputs()
    sample = {r["case_id"]: r["product_type"] for r in sample_rows if r["sampled"] == "yes"}
    r0_doc = json.loads((RQ1 / "rq1-r0.json").read_text())
    r0 = {c: r0_doc["classes"].get(c) for c in sample}
    flagged = set(json.loads((RQ1 / "rq1-flags.json").read_text())["flagged"]) & set(sample)
    saved_results = json.loads((analysis_dir / "RESULTS-RQ1.json").read_text())
    saved_explore = json.loads((analysis_dir / "EXPLORATORY-DISAGREEMENT.json").read_text())
    explore_recomputed = ed.analyse(sample, r0, models, flagged)  # same rng sequence as the saved exploratory run
    res = analyse(sample, r0, models, saved_results, saved_explore, explore_recomputed)
    res.update(run_dir=an.repo_path(run_dir), r0_sha256=manifest["r0_sha256"], **provenance)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "AGREEMENT-POSTHOC.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "AGREEMENT-POSTHOC.md").write_text(markdown(res))
    print(markdown(res))


if __name__ == "__main__":
    main(*sys.argv[1:3])
