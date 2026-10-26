#!/usr/bin/env python3
"""RQ1 confirmatory analysis (§5 as amended by D41, D43, D44, D45): H1 and H1a on the D44 sample, with every preregistered
variant computed alone against the primary. Writes RESULTS-RQ1.json and RESULTS-RQ1.md into OUT_DIR (default: a sibling of
the run directory named <run>-rq1-analysis; never inside the run directory, which holds model results only).

    python3 preregistration/rq1/analyze.py RUN_DIR [OUT_DIR]

The frame is read from the frame commit named in rq1-sample-manifest.json and checked against the manifest's hash; the sample is
recomputed from that frame and seed and must equal rq1-sample.csv; estimate.py must be the copy in the frame commit (its hash is
recorded). Inputs otherwise: rq1-r0.json (whose hash the run manifest recorded), rq1-flags.json, rq1-frame-erratum.csv and the
confirmatory run directory written by classify.py. Analyses that need inputs this script does not handle (a grouping erratum,
summaries corrected after the runs) stop it with a message instead of being skipped.
"""
import csv, io, json, pathlib, subprocess, sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import estimate as es  # noqa: E402
import classify  # noqa: E402
import sample_frame as sf  # noqa: E402

TYPES = ("agent client", "MCP server or connector", "SDK")
R2 = "gemma4:26b-a4b-it-q8_0"  # D43


def majority(votes):
    """Model majority (D7): the class given by more than half of the model raters; None otherwise (no majority)."""
    votes = [v for v in votes]
    for c in (1, 2, 3, 4):
        if sum(v == c for v in votes) * 2 > len(votes):
            return c
    return None


def share(labels, sample, sizes, drop=frozenset(), weights=None):
    """Stratified share of classes 1-3 (D44 point 6). labels: case -> class or None (unlabelled: outside 1-3 in the point
    estimate, both ways in the interval). Dropped cases leave the sample and the frame of their stratum."""
    strata, observed, positive = {}, {}, 0
    for t in (t for t in TYPES if t in sizes):  # only the strata of the population being estimated
        ids = [c for c, pt in sample.items() if pt == t and c not in drop]
        pop = sizes[t] - sum(1 for c in drop if sample.get(c) == t)
        if not ids:
            if pop > 0:  # a populated stratum without observations: all its cases unknown (outside 1-3 in the point estimate,
                strata[t] = (pop, pop, 0, pop)  # both ways in the interval), never dropped from the weights
            continue
        x = sum(labels.get(c) in (1, 2, 3) for c in ids); u = sum(labels.get(c) is None for c in ids)
        strata[t] = (pop, len(ids), x, u); observed[t] = len(ids); positive += x
    if not any(c not in drop for c in sample):
        return None  # no sampled case left: not available
    r = es.stratified_share(strata, weights=weights and {k: weights[k] for k in strata})
    r["strata"] = strata  # (population, n used for the bounds, x, unlabelled); unobserved strata enter as all unknown
    r["observed"] = {t: observed.get(t, 0) for t in strata}  # actual sampled cases retained
    n_obs = sum(observed.values())
    r["unweighted"] = Fraction(positive, n_obs) if n_obs else None  # over actual observations only
    return r


def fmt(r):
    if r is None:
        return {"share": None, "interval": None, "available": False}
    iv = r["interval"]
    return {"share": float(r["share"]), "share_exact": str(r["share"]),
            "unweighted": None if r["unweighted"] is None else float(r["unweighted"]), "observed": r.get("observed"),
            "interval": None if iv is None else [float(iv[0]), float(iv[1])], "exact": r["exact"],
            "strata": {k: list(v) for k, v in r.get("strata", {}).items()}}


def verdict(r0, models):
    return "not available (no observed case)" if r0 is None or models is None else es.h1_verdict(r0, models)


def analyse(frame_rows, sample_rows, r0_doc, models, flags_doc, erratum_rows, quality=None):
    """quality: model -> case -> {"n_invalid": int, "tie": bool} from the run's result files (D41 points 4 and 9)."""
    quality = quality or {}
    if any(r["kind"].startswith("grouping") for r in erratum_rows):
        sys.exit("rq1-frame-erratum.csv lists a grouping error: the corrected-disclosure analysis (D44 point 5) is not "
                 "implemented here; implement and review it before running the analysis")
    sizes = {t: sum(1 for r in frame_rows if r["decision"] == "include" and r["product_type"] == t) for t in TYPES}
    sample = {r["case_id"]: r["product_type"] for r in sample_rows if r["sampled"] == "yes"}
    source = {r["case_id"]: r["source"] for r in sample_rows if r["sampled"] == "yes"}
    r0 = {c: r0_doc["classes"].get(c) for c in sample}
    if set(r0_doc["classes"]) != set(sample):
        sys.exit("rq1-r0.json does not cover exactly the sampled cases")
    names = list(models)
    if sorted(names) != sorted(classify.ROSTER):
        sys.exit(f"model raters {names} are not the frozen roster")
    maj = {c: majority([models[m].get(c) for m in names]) for c in sample}
    maj_no_r2 = {c: majority([models[m].get(c) for m in names if m != R2]) for c in sample}
    flagged = set(flags_doc["flagged"])
    late = {r["case_id"] for r in erratum_rows if r["kind"].startswith("late ineligible")}
    doubtful = {r["case_id"] for r in frame_rows if r["reason"] == "I?" and r["case_id"] in sample}
    bundle = r0_doc.get("bundle_model_finding", {})
    mixed = {c for c, yes in bundle.items() if yes and r0.get(c) in (1, 2, 3)}
    bad_quality = {c for m in names for c, q in quality.get(m, {}).items() if c in sample and (q.get("n_invalid") or q.get("tie"))}
    contested = (flagged | {c for c in sample if r0[c] is None or maj[c] is None or r0[c] != maj[c]}
                 | {c for c in sample if any(models[m].get(c) is None for m in names)} | bad_quality)
    invalid_rate = {m: (sum(q.get("n_invalid", 0) for c, q in quality.get(m, {}).items() if c in sample)
                        / max(1, sum(len(q.get("answers", [])) or 3 for c, q in quality.get(m, {}).items() if c in sample)))
                    for m in names}
    raters = {"R0": r0, "model majority": maj}

    def both(fn):
        out = {}
        for name, lab in raters.items():
            out[name] = fn(name, lab)
        res = {k: fmt(v) for k, v in out.items()}
        res["verdict"] = verdict(out["R0"], out["model majority"])
        return res

    primary = both(lambda n, lab: share(lab, sample, sizes))
    variants = {
        "D45/D41 p1: mixed bundles as class 4": both(lambda n, lab: share({**lab, **{c: 4 for c in mixed}}, sample, sizes)),
        "D41 p6: contested cases against H1": both(lambda n, lab: share({**lab, **{c: 4 for c in contested}}, sample, sizes)),
        "D41 p6: contested cases in favour of H1": both(lambda n, lab: share({**lab, **{c: 1 for c in contested}}, sample, sizes)),
        "D43: model majority without R2": (lambda r0s, ms: {"R0": fmt(r0s), "model majority": fmt(ms),
                                                            "verdict": verdict(r0s, ms)})(
            share(r0, sample, sizes), share(maj_no_r2, sample, sizes)),
        "D44 p1: without the flagged (I?) cases": both(lambda n, lab: share(lab, sample, sizes, drop=frozenset(doubtful))),
        "D44 p5: without late-ineligible cases": both(lambda n, lab: share(lab, sample, sizes, drop=frozenset(late))),
        "D44 p6: labelled cases only": both(lambda n, lab: share(lab, sample, sizes,
                                                                drop=frozenset(c for c in sample if lab[c] is None))),
        "D44 p6: equal weights for the three product types": both(lambda n, lab: share(lab, sample, sizes,
                                                                                      weights={t: 1 for t in TYPES})),
    }
    not_applicable = {"D41 p7: corrected summaries": "no summary was corrected after the runs (no rq1-summary-corrections.json)",
                      "D44 p5: corrected-disclosure count": "no grouping error in rq1-frame-erratum.csv"}
    strata_rows = {}
    for t in TYPES:
        ids = frozenset(c for c in sample if sample[c] != t)
        only = {n: fmt(share(lab, {c: p for c, p in sample.items() if p == t}, {t: sizes[t]})) for n, lab in raters.items()}
        rest = {k: v for k, v in sizes.items() if k != t}
        without = {n: share(lab, {c: p for c, p in sample.items() if p != t}, rest) for n, lab in raters.items()}
        n_t = sum(1 for p in sample.values() if p == t)
        strata_rows[t] = {"sampled": n_t, "interpreted": n_t >= 10, "stratum": only,
                          "frame without it": {n: fmt(v) for n, v in without.items()},
                          "H1 depends on it": primary["verdict"] != "not supported"
                          and any(v["share"] < es.H1_SHARE for v in without.values())}
    lab4 = {**{"R0": r0}, **models}
    complete = [c for c in sample if all(lab4[k].get(c) for k in lab4)]
    fk = classify.fleiss({c: [lab4[k][c] for k in lab4] for c in complete}) if complete else None
    no_r2 = {k: v for k, v in lab4.items() if k != R2}
    complete2 = [c for c in sample if all(no_r2[k].get(c) for k in no_r2)]
    fk2 = classify.fleiss({c: [no_r2[k][c] for k in no_r2] for c in complete2}) if complete2 else None
    cohen = {}
    for m in names:
        k, n = classify.cohen({c: r0[c] for c in sample if r0[c]}, {c: models[m].get(c) for c in sample})
        cohen[m] = {"kappa": k, "n": n, "left_out": len(sample) - n}
    return {
        "n_sampled": len(sample), "frame_sizes": sizes,
        "unlabelled": {"R0": sorted(c for c in sample if r0[c] is None),
                       "model majority": sorted(c for c in sample if maj[c] is None)},
        "primary": primary,
        "H1a": {"fleiss_all_raters": fk, "n_complete": len(complete), "left_out": len(sample) - len(complete),
                "holds": fk is not None and fk >= 0.6, "fleiss_without_R2": fk2, "n_complete_without_R2": len(complete2),
                "cohen_vs_R0": cohen},
        "variants": variants, "not_applicable": not_applicable,
        "contested": sorted(contested), "mixed_bundles": sorted(mixed), "late_ineligible": sorted(late),
        "flagged_I?": sorted(doubtful),
        "by_product_type": strata_rows,
        "source_split": source_split(raters, sample, source, frame_rows),
        "per_model": {m: {**fmt(share(models[m], sample, sizes)), "unlabelled": sorted(c for c in sample if models[m].get(c) is None),
                          "invalid_answer_rate": invalid_rate[m], "over_10_percent_invalid": invalid_rate[m] > 0.10}
                      for m in names},
    }


def source_split(raters, sample, source, frame_rows):
    """D41 point 3: the source strata ("timeline", "query only") as domains, each and the frame without it, with the same
    stratified estimator over product types; computed, reported with counts, not interpreted (D44 point 6)."""
    frame_src = {r["case_id"]: r["source"] for r in frame_rows if r["decision"] == "include"}
    frame_type = {r["case_id"]: r["product_type"] for r in frame_rows if r["decision"] == "include"}
    out = {"timeline_in_frame": sorted(c for c, s in frame_src.items() if s == "timeline"), "interpreted": False}
    for s_name in ("timeline", "query only"):
        sub = {c: p for c, p in sample.items() if source[c] == s_name}
        sizes_s = {t: sum(1 for c in frame_src if frame_src[c] == s_name and frame_type[c] == t) for t in TYPES}
        rest = {c: p for c, p in sample.items() if source[c] != s_name}
        sizes_r = {t: sum(1 for c in frame_src if frame_src[c] != s_name and frame_type[c] == t) for t in TYPES}
        out[s_name] = {"sampled": len(sub),
                       "domain": {n: fmt(share(lab, sub, sizes_s)) for n, lab in raters.items()} if sub else "not available",
                       "frame without it": {n: fmt(share(lab, rest, sizes_r)) for n, lab in raters.items()} if rest else "not available"}
    return out


def markdown(res):
    p = res["primary"]
    def line(name, r):
        iv = r["interval"]
        uw = "n/a" if r["unweighted"] is None else f"{r['unweighted']:.1%}"
        return f"| {name} | {r['share']:.1%} | " + ("exact" if iv is None else f"{iv[0]:.1%}–{iv[1]:.1%}") + f" | {uw} |"
    out = ["# RQ1 results (D44 sample)", "", f"Sampled cases: {res['n_sampled']}; frame sizes {res['frame_sizes']}.", "",
           "| Rater | Share in classes 1–3 (stratified) | 95% interval (exact, conservative) | Unweighted |", "|---|---|---|---|",
           line("R0", p["R0"]), line("Model majority", p["model majority"]), "", f"**H1: {p['verdict']}.**", "",
           f"H1a: Fleiss' κ (all raters) = {res['H1a']['fleiss_all_raters']} on {res['H1a']['n_complete']} cases "
           f"({res['H1a']['left_out']} left out); holds: {res['H1a']['holds']}. Without R2: {res['H1a']['fleiss_without_R2']}.", "",
           "## Variants (each alone against the primary)", "", "| Variant | R0 | Model majority | Verdict |", "|---|---|---|---|"]
    for k, v in res["variants"].items():
        pct = lambda x: "n/a" if x is None else f"{x:.1%}"
        out.append(f"| {k} | {pct(v['R0']['share'])} | {pct(v['model majority']['share'])} | {v['verdict']} |")
    for k, v in res["not_applicable"].items():
        out.append(f"| {k} | n/a | n/a | {v} |")
    out += ["", "## Each model rater", "", "| Model | Share (stratified) | Interval | Unlabelled | Invalid answers | Cohen's κ vs R0 (n, left out) |",
            "|---|---|---|---|---|---|"]
    for m, v in res["per_model"].items():
        iv = v["interval"]; ck = res["H1a"]["cohen_vs_R0"][m]
        out.append(f"| {m} | {v['share']:.1%} | " + ("exact" if iv is None else f"{iv[0]:.1%}–{iv[1]:.1%}")
                   + f" | {len(v['unlabelled'])} | {v['invalid_answer_rate']:.1%}{' (>10%)' if v['over_10_percent_invalid'] else ''} | "
                   f"{ck['kappa']} ({ck['n']}, {ck['left_out']}) |")
    out += ["", "## By product type", "", "| Type | Sampled | R0 in stratum | Majority in stratum | Frame without it: R0 / majority | H1 depends on it |",
            "|---|---|---|---|---|---|"]
    for t, s in res["by_product_type"].items():
        w = s["frame without it"]
        out.append(f"| {t} | {s['sampled']}{'' if s['interpreted'] else ' (not interpreted)'} | {s['stratum']['R0']['share']:.1%} | "
                   f"{s['stratum']['model majority']['share']:.1%} | {w['R0']['share']:.1%} / {w['model majority']['share']:.1%} | "
                   f"{s['H1 depends on it']} |")
    out += ["", f"Contested cases: {len(res['contested'])}. Mixed bundles: {res['mixed_bundles']}. Late ineligible: "
            f"{res['late_ineligible']}. Unlabelled: {res['unlabelled']}. Source split (not interpreted): timeline cases sampled "
            f"{res['source_split']['timeline']['sampled']}, in the frame {res['source_split']['timeline_in_frame']}."]
    return "\n".join(out) + "\n"


def git_show(commit, path):
    return subprocess.run(["git", "-C", str(HERE), "show", f"{commit}:{path}"], capture_output=True, check=True).stdout


def model_quality(run_dir, manifest):
    """Per model and case: number of invalid answers, tie and the answers, from the run's result files (D41 points 4, 9)."""
    out = {}
    for e in manifest["models"]:
        d = json.loads((run_dir / e["file"]).read_text())
        out[e["name"]] = {c: {"n_invalid": v.get("n_invalid", 0), "tie": bool(v.get("tie")), "answers": v.get("answers", [])}
                          for c, v in d["cases"].items()}
    return out


def main(run_dir, out_dir=None):
    run_dir = pathlib.Path(run_dir).resolve()
    out_dir = pathlib.Path(out_dir) if out_dir else run_dir.parent / (run_dir.name + "-rq1-analysis")
    if out_dir.resolve() == run_dir:
        sys.exit("the analysis output never goes into the model run directory")
    if (HERE / "rq1-summary-corrections.json").exists():
        sys.exit("summaries were corrected after the runs: the D41 point 7 analysis is not implemented here; implement and "
                 "review it before running the analysis")
    sman = json.loads((HERE / "rq1-sample-manifest.json").read_text())
    frame_raw = git_show(sman["frame_commit"], sf.FRAME_IN_REPO)
    if __import__("hashlib").sha256(frame_raw).hexdigest() != sman["frame_sha256"]:
        sys.exit("the frame in the frame commit differs from the sample manifest")
    _, _, recomputed = sf.sample(sf.read_frame(frame_raw), sman["seed"])
    with open(HERE / "rq1-sample.csv", newline="") as f:
        if [dict(r) for r in csv.DictReader(f)] != [{k: str(v) for k, v in r.items()} for r in recomputed]:
            sys.exit("rq1-sample.csv differs from the sample recomputed from the frozen frame and seed")
    est_sha = es.bound_to(sman["frame_commit"])
    models, manifest = classify.load_models(run_dir)  # confirmatory manifest, roster and digests enforced
    r0_path = HERE / "rq1-r0.json"
    if manifest.get("r0_sha256") != classify.sha256_file(r0_path):
        sys.exit("rq1-r0.json differs from the R0 file recorded in the run manifest")
    read = lambda f: list(csv.DictReader(open(HERE / f, newline="")))
    frame_rows = list(csv.DictReader(io.StringIO(frame_raw.decode())))
    res = analyse(frame_rows, [{k: str(v) for k, v in r.items()} for r in recomputed], json.loads(r0_path.read_text()),
                  models, json.loads((HERE / "rq1-flags.json").read_text()), read("rq1-frame-erratum.csv"),
                  model_quality(run_dir, manifest))
    res.update(estimate_sha256=est_sha, frame_commit=sman["frame_commit"], run_dir=str(run_dir),
               r0_sha256=manifest["r0_sha256"])
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "RESULTS-RQ1.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "RESULTS-RQ1.md").write_text(markdown(res))
    print(markdown(res))

if __name__ == "__main__":
    main(*sys.argv[1:3])
