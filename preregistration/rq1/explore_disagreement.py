#!/usr/bin/env python3
"""RQ1, EXPLORATORY (not preregistered; D51): where the raters disagree. Written on 28 Oct 2026, after the confirmatory
results were known. It changes no confirmatory figure and no verdict; it only describes the labels already analysed.

    python3 preregistration/rq1/explore_disagreement.py RUN_DIR [OUT_DIR]

Reports, on the 120 sampled cases: 4x4 confusion tables R0 vs each model rater and vs the model majority; which class pairs
make up the disagreements; agreement on the binary question H1 actually asks (classes 1-3, decided by the product, vs class 4,
decided by the model) as percent agreement, Cohen's and Fleiss' kappa and PABAK; per-class specific agreement; disagreement
split by the D41 flag and by product type. Kappa intervals are percentile bootstraps over cases (2000 resamples, seed 20261028).
Writes EXPLORATORY-DISAGREEMENT.{json,md} into OUT_DIR (default: the <run>-rq1-analysis directory).
"""
import collections, csv, hashlib, io, json, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import classify  # noqa: E402
import analyze as an  # noqa: E402
from analyze import majority  # noqa: E402

CLASSES = (1, 2, 3, 4)
SEED, RESAMPLES = 20261028, 2000


def binary(c):
    """H1's question: 'P' (classes 1-3, decided by the product) or 'M' (class 4, decided by the model); None stays None."""
    return None if c is None else ("P" if c in (1, 2, 3) else "M")


def confusion(a, b):
    """4x4 counts, rows = a, columns = b, on cases both labelled."""
    t = {r: {c: 0 for c in CLASSES} for r in CLASSES}
    for k in a:
        if a[k] and b.get(k):
            t[a[k]][b[k]] += 1
    return t


def cohen_any(a, b):
    """Cohen's kappa for any label set (classify.cohen counts categories generically); None when undefined."""
    return classify.cohen(a, b)


def fleiss_any(ratings, cats):
    """Fleiss' kappa over an arbitrary category set; None when undefined."""
    N = len(ratings)
    if N == 0:
        return None
    n = len(next(iter(ratings.values())))
    pj, P = collections.Counter(), []
    for r in ratings.values():
        cnt = collections.Counter(r); pj.update(cnt)
        P.append((sum(v * v for v in cnt.values()) - n) / (n * (n - 1)))
    pe = sum((pj[c] / (N * n)) ** 2 for c in cats)
    return (sum(P) / N - pe) / (1 - pe) if pe < 1 else None


def percent(a, b):
    keys = [k for k in a if a[k] and b.get(k)]
    return (sum(a[k] == b[k] for k in keys) / len(keys), len(keys)) if keys else (None, 0)


def pabak(a, b):
    """Prevalence- and bias-adjusted kappa for two categories: 2*po - 1."""
    po, n = percent(a, b)
    return None if po is None else 2 * po - 1


def boot(fn, keys, rng):
    """Percentile 95% interval of fn(resampled keys); undefined resamples are skipped and counted."""
    vals, undefined = [], 0
    for _ in range(RESAMPLES):
        v = fn([rng.choice(keys) for _ in keys])
        if v is None:
            undefined += 1
        else:
            vals.append(v)
    if not vals:
        return None
    vals.sort()
    return {"low": vals[int(0.025 * len(vals))], "high": vals[min(len(vals) - 1, int(0.975 * len(vals)))],
            "undefined_resamples": undefined}


def resampled(labels_by_rater, keys):
    """Relabel resampled keys as distinct cases (a key drawn twice counts twice)."""
    return {r: {i: lab.get(k) for i, k in enumerate(keys)} for r, lab in labels_by_rater.items()}


def specific_agreement(a, b, c):
    """Specific agreement for class c between two raters: 2*n_cc / (n_c(a) + n_c(b)), on cases both labelled."""
    keys = [k for k in a if a[k] and b.get(k)]
    both = sum(a[k] == c and b[k] == c for k in keys)
    tot = sum(a[k] == c for k in keys) + sum(b[k] == c for k in keys)
    return (2 * both / tot) if tot else None


def analyse(sample, r0, models, flagged):
    """sample: case -> product type; r0: case -> class or None; models: name -> case -> class or None; flagged: set."""
    rng = random.Random(SEED)
    names = sorted(models)
    maj = {c: majority([models[m].get(c) for m in names]) for c in sample}
    raters = {"R0": r0, **models, "model majority": maj}
    res = {"exploratory": True, "n_sampled": len(sample), "confusion": {}, "disagreement_pairs": {}, "binary": {},
           "four_class": {}, "specific_agreement": {}, "by_flag": {}, "by_product_type": {}}

    for name in names + ["model majority"]:
        res["confusion"][f"R0 vs {name}"] = confusion(r0, raters[name])
        pairs = collections.Counter(tuple(sorted((r0[c], raters[name][c]))) for c in sample
                                    if r0[c] and raters[name].get(c) and r0[c] != raters[name][c])
        res["disagreement_pairs"][f"R0 vs {name}"] = {f"{a}-{b}": n for (a, b), n in pairs.most_common()}
        res["specific_agreement"][f"R0 vs {name}"] = {c: specific_agreement(r0, raters[name], c) for c in CLASSES}

    # Four classes and the binary H1 question, R0 vs each model (Cohen) and all four raters (Fleiss), with bootstraps.
    four = {"R0": r0, **models}
    complete = [c for c in sample if all(four[r].get(c) for r in four)]
    for label, conv, cats in (("four_class", lambda x: x, CLASSES), ("binary", binary, ("P", "M"))):
        conv_r = {r: {c: conv(v) for c, v in lab.items()} for r, lab in raters.items()}
        out = res[label]
        for name in names + ["model majority"]:
            a, b = conv_r["R0"], conv_r[name]
            k, n = cohen_any(a, b)
            po, _ = percent(a, b)
            keys = [c for c in sample if a.get(c) and b.get(c)]
            ci = boot(lambda ks: cohen_any(*resampled({"a": a, "b": b}, ks).values())[0], keys, rng)
            row = {"percent_agreement": po, "cohen_kappa": k, "kappa_95": ci, "n": n}
            if label == "binary":
                row["pabak"] = pabak(a, b)
            out[f"R0 vs {name}"] = row
        fl = lambda ks: fleiss_any({i: [conv_r[r][k] for r in four] for i, k in enumerate(ks)}, cats)
        out["Fleiss, R0 + three models"] = {"kappa": fl(complete), "kappa_95": boot(fl, complete, rng), "n": len(complete)}
        if label == "binary":
            out["prevalence"] = {r: (sum(conv_r[r][c] == "P" for c in sample if conv_r[r].get(c))
                                     / max(1, sum(1 for c in sample if conv_r[r].get(c)))) for r in four}

    def disagree(c):
        return bool(r0[c] and maj[c] and r0[c] != maj[c])

    def binary_disagree(c):
        return bool(r0[c] and maj[c] and binary(r0[c]) != binary(maj[c]))

    def split(group):
        g = [c for c in sample if c in group]
        return {"cases": len(g), "R0 vs majority disagree (4 classes)": sum(map(disagree, g)),
                "R0 vs majority disagree (binary)": sum(map(binary_disagree, g)),
                "no model majority": sum(maj[c] is None for c in g)}

    res["by_flag"] = {"flagged (D41)": split(flagged), "not flagged": split(set(sample) - flagged)}
    for t in sorted(set(sample.values())):
        res["by_product_type"][t] = split({c for c, p in sample.items() if p == t})
    res["binary_disagreement_cases"] = sorted(c for c in sample if binary_disagree(c))
    return res


def f(x, d=3):
    return "n/a" if x is None else f"{x:.{d}f}"


def ci(c):
    return "n/a" if not c else f"[{c['low']:.2f}, {c['high']:.2f}]"


def markdown(res):
    out = ["# RQ1 — where the raters disagree (EXPLORATORY, D51)", "",
           "Not preregistered; written after the confirmatory results. No confirmatory figure or verdict changes.",
           f"Cases: {res['n_sampled']}. Bootstrap: {RESAMPLES} resamples over cases, seed {SEED}.", "",
           "## Agreement on four classes and on the question H1 asks (product 1–3 vs model 4)", "",
           "| Pair | n | 4 classes: agreement | 4 classes: κ [95%] | Binary: agreement | Binary: κ [95%] | Binary: PABAK |",
           "|---|---|---|---|---|---|---|"]
    for k in res["four_class"]:
        if not k.startswith("R0 vs"):
            continue
        a, b = res["four_class"][k], res["binary"][k]
        out.append(f"| {k} | {a['n']} | {f(a['percent_agreement'])} | {f(a['cohen_kappa'])} {ci(a['kappa_95'])} | "
                   f"{f(b['percent_agreement'])} | {f(b['cohen_kappa'])} {ci(b['kappa_95'])} | {f(b['pabak'])} |")
    a, b = res["four_class"]["Fleiss, R0 + three models"], res["binary"]["Fleiss, R0 + three models"]
    out += [f"| Fleiss, R0 + three models | {a['n']} | – | {f(a['kappa'])} {ci(a['kappa_95'])} | – | "
            f"{f(b['kappa'])} {ci(b['kappa_95'])} | – |", "",
            "Share labelled 'product' (1–3) per rater: "
            + ", ".join(f"{r} {v:.1%}" for r, v in res["binary"]["prevalence"].items())
            + ". With a share this far from 50%, κ is low even at high raw agreement (prevalence effect); PABAK is shown for "
              "that reason and is not a substitute for κ.", "",
            "## Which class pairs the disagreements are", "", "| Pair | Disagreements by class pair (count) |", "|---|---|"]
    for k, v in res["disagreement_pairs"].items():
        out.append(f"| {k} | " + ", ".join(f"{p}: {n}" for p, n in v.items()) + " |")
    out += ["", "## Specific agreement per class (2·both / (count R0 + count other))", "",
            "| Pair | 1 | 2 | 3 | 4 |", "|---|---|---|---|---|"]
    for k, v in res["specific_agreement"].items():
        out.append(f"| {k} | " + " | ".join(f(v[c], 2) for c in CLASSES) + " |")
    out += ["", "## Confusion tables (rows R0, columns the other rater)", ""]
    for k, t in res["confusion"].items():
        out += [f"**{k}**", "", "| R0 \\ other | 1 | 2 | 3 | 4 |", "|---|---|---|---|---|"]
        out += [f"| {r} | " + " | ".join(str(t[r][c]) for c in CLASSES) + " |" for r in CLASSES] + [""]
    out += ["## Disagreement R0 vs model majority, by group", "",
            "| Group | Cases | Disagree (4 classes) | Disagree (binary) | No model majority |", "|---|---|---|---|---|"]
    for g, v in list(res["by_flag"].items()) + list(res["by_product_type"].items()):
        out.append(f"| {g} | {v['cases']} | {v['R0 vs majority disagree (4 classes)']} | {v['R0 vs majority disagree (binary)']} | "
                   f"{v['no model majority']} |")
    out += ["", f"Cases where R0 and the model majority disagree on product vs model: {', '.join(res['binary_disagreement_cases']) or 'none'}."]
    return "\n".join(out) + "\n"


def verified_inputs():
    """The frozen frame (from the frame commit, hash-checked) and the sample recomputed from it, which must equal
    rq1-sample.csv; estimate.py bound to the frame commit. The same checks as the primary analysis (analyze.main)."""
    sman = json.loads((HERE / "rq1-sample-manifest.json").read_text())
    frame_raw = an.git_show(sman["frame_commit"], an.sf.FRAME_IN_REPO)
    if hashlib.sha256(frame_raw).hexdigest() != sman["frame_sha256"]:
        sys.exit("the frame in the frame commit differs from the sample manifest")
    _, _, recomputed = an.sf.sample(an.sf.read_frame(frame_raw), sman["seed"])
    sample_rows = [{k: str(v) for k, v in r.items()} for r in recomputed]
    with open(HERE / "rq1-sample.csv", newline="") as fh:
        if [dict(r) for r in csv.DictReader(fh)] != sample_rows:
            sys.exit("rq1-sample.csv differs from the sample recomputed from the frozen frame and seed")
    provenance = {"frame_commit": sman["frame_commit"], "frame_sha256": sman["frame_sha256"],
                  "estimate_sha256": an.es.bound_to(sman["frame_commit"])}
    return list(csv.DictReader(io.StringIO(frame_raw.decode()))), sample_rows, provenance


def main(run_dir, out_dir=None):
    run_dir = pathlib.Path(run_dir).resolve()
    out_dir = pathlib.Path(out_dir) if out_dir else run_dir.parent / (run_dir.name + "-rq1-analysis")
    models, manifest = classify.load_models(run_dir)
    if manifest.get("r0_sha256") != classify.sha256_file(HERE / "rq1-r0.json"):
        sys.exit("rq1-r0.json differs from the R0 file recorded in the run manifest")
    _, sample_rows, provenance = verified_inputs()
    sample = {r["case_id"]: r["product_type"] for r in sample_rows if r["sampled"] == "yes"}
    r0_doc = json.loads((HERE / "rq1-r0.json").read_text())
    r0 = {c: r0_doc["classes"].get(c) for c in sample}
    flagged = set(json.loads((HERE / "rq1-flags.json").read_text())["flagged"]) & set(sample)
    res = analyse(sample, r0, models, flagged)
    res.update(run_dir=str(run_dir), **provenance)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "EXPLORATORY-DISAGREEMENT.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "EXPLORATORY-DISAGREEMENT.md").write_text(markdown(res))
    print(markdown(res))


if __name__ == "__main__":
    main(*sys.argv[1:3])
