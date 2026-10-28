#!/usr/bin/env python3
"""RQ1, EXPLORATORY (D51): agreement of a second, independent human rater (H2) with the author (R0) and the model raters.
Fixed before any H2 label exists. Nothing here changes a confirmatory figure or verdict.

    python3 preregistration/rq1/second_rater.py RUN_DIR H2_JSON [OUT_DIR]

H2_JSON is the export of the sheet built by h2_sheet.py (rq1-h2.json): {"rater": "H2", "classes": {id: 1-4 or null}, ...}.
Reported: Cohen's kappa H2 vs R0 on four classes and on the binary H1 question (classes 1-3 vs 4), with percent agreement,
PABAK and bootstrap intervals; H2 vs each model rater and vs the model majority; Fleiss' kappa over R0, H2 and the three
models; H2's stratified share of classes 1-3 with the same conservative interval as the primary analysis; the cases where R0
and H2 disagree on the binary question. Writes EXPLORATORY-H2.{json,md} into OUT_DIR (default: <run>-rq1-analysis).
"""
import json, pathlib, random, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE)); sys.path.insert(0, str(HERE.parent))
import classify  # noqa: E402
import analyze as an  # noqa: E402
import explore_disagreement as ed  # noqa: E402


SHEET = "v3-guided-h2"
DECLARATION = "labelled by a second human rater without AI assistance, blind to all other labels (D51)"


def load_h2(doc, sample, seed=None, criteria_sha256=None):
    """The H2 export, checked against the sheet that produced it: rater, sheet version, declaration, seed and criteria digest,
    exactly the sampled cases, and classes that are integers 1-4 or null (JSON true or 1.0 are rejected)."""
    if doc.get("rater") != "H2" or doc.get("sheet") != SHEET or doc.get("declaration") != DECLARATION:
        sys.exit("not an export of the H2 sheet (rater, sheet version or declaration differ)")
    if seed is not None and doc.get("seed") != seed:
        sys.exit("the H2 export was made with a different seed")
    if criteria_sha256 is not None and doc.get("criteria_sha256") != criteria_sha256:
        sys.exit("the H2 export was made under different criteria")
    classes = doc.get("classes")
    if not isinstance(classes, dict) or set(classes) != set(sample):
        sys.exit("the H2 export does not cover exactly the sampled cases")
    if any(v is not None and (type(v) is not int or v not in (1, 2, 3, 4)) for v in classes.values()):
        sys.exit("the H2 export has a class that is not an integer 1-4 or null")
    return dict(classes)


def pair(a, b, keys, rng):
    out = {}
    for label, conv in (("four_class", lambda x: x), ("binary", ed.binary)):
        ca, cb = {k: conv(a.get(k)) for k in keys}, {k: conv(b.get(k)) for k in keys}
        k, n = ed.cohen_any(ca, cb)
        po, _ = ed.percent(ca, cb)
        both = [c for c in keys if ca.get(c) and cb.get(c)]
        row = {"percent_agreement": po, "cohen_kappa": k, "n": n,
               "kappa_95": ed.boot(lambda ks: ed.cohen_any(*ed.resampled({"a": ca, "b": cb}, ks).values())[0], both, rng)}
        if label == "binary":
            row["pabak"] = ed.pabak(ca, cb)
        out[label] = row
    return out


def analyse(frame_rows, sample_rows, r0, h2, models):
    rng = random.Random(ed.SEED)
    sizes = {t: sum(1 for r in frame_rows if r["decision"] == "include" and r["product_type"] == t) for t in an.TYPES}
    sample = {r["case_id"]: r["product_type"] for r in sample_rows if r["sampled"] == "yes"}
    names = sorted(models)
    maj = {c: an.majority([models[m].get(c) for m in names]) for c in sample}
    keys = sorted(sample)
    res = {"exploratory": True, "n_sampled": len(sample), "h2_unlabelled": sorted(c for c in sample if h2.get(c) is None),
           "pairs": {"H2 vs R0": pair(h2, r0, keys, rng), "H2 vs model majority": pair(h2, maj, keys, rng),
                     **{f"H2 vs {m}": pair(h2, models[m], keys, rng) for m in names}}}
    five = {"R0": r0, "H2": h2, **models}
    complete = [c for c in keys if all(five[r].get(c) for r in five)]
    res["fleiss_R0_H2_models"] = {"four_class": ed.fleiss_any({c: [five[r][c] for r in five] for c in complete}, ed.CLASSES),
                                  "binary": ed.fleiss_any({c: [ed.binary(five[r][c]) for r in five] for c in complete}, ("P", "M")),
                                  "n": len(complete)}
    humans = {"R0": r0, "H2": h2}
    hc = [c for c in keys if r0.get(c) and h2.get(c)]
    res["fleiss_two_humans_check"] = ed.fleiss_any({c: [humans[r][c] for r in humans] for c in hc}, ed.CLASSES) if hc else None
    res["h2_share"] = an.fmt(an.share(h2, sample, sizes))
    res["r0_share"] = an.fmt(an.share(r0, sample, sizes))
    res["binary_disagreement_R0_H2"] = sorted(c for c in hc if ed.binary(r0[c]) != ed.binary(h2[c]))
    res["confusion_R0_vs_H2"] = ed.confusion(r0, h2)
    return res


def markdown(res):
    f, ci = ed.f, ed.ci
    out = ["# RQ1 — second human rater H2 (EXPLORATORY, D51)", "",
           "Not preregistered. Plan fixed before any H2 label. No confirmatory figure or verdict changes.", "",
           f"Cases: {res['n_sampled']}; left unlabelled by H2: {len(res['h2_unlabelled'])}.", "",
           "| Pair | n | 4 classes: agreement | 4 classes: κ [95%] | Binary: agreement | Binary: κ [95%] | Binary: PABAK |",
           "|---|---|---|---|---|---|---|"]
    for k, v in res["pairs"].items():
        a, b = v["four_class"], v["binary"]
        out.append(f"| {k} | {a['n']} | {f(a['percent_agreement'])} | {f(a['cohen_kappa'])} {ci(a['kappa_95'])} | "
                   f"{f(b['percent_agreement'])} | {f(b['cohen_kappa'])} {ci(b['kappa_95'])} | {f(b['pabak'])} |")
    fl = res["fleiss_R0_H2_models"]
    out += ["", f"Fleiss' κ, R0 + H2 + three models (n={fl['n']}): four classes {f(fl['four_class'])}, binary {f(fl['binary'])}.", "",
            f"Share in classes 1–3 (stratified, conservative 95% interval): H2 {res['h2_share']['share']:.1%} "
            + (f"[{res['h2_share']['interval'][0]:.1%}–{res['h2_share']['interval'][1]:.1%}]" if res['h2_share']['interval'] else "")
            + f"; R0 {res['r0_share']['share']:.1%}.", "",
            "Confusion R0 (rows) vs H2 (columns):", "", "| R0 \\ H2 | 1 | 2 | 3 | 4 |", "|---|---|---|---|---|"]
    t = res["confusion_R0_vs_H2"]
    out += [f"| {r} | " + " | ".join(str(t[r][c]) for c in ed.CLASSES) + " |" for r in ed.CLASSES]
    out += ["", "Cases where R0 and H2 disagree on product vs model: " + (", ".join(res["binary_disagreement_R0_H2"]) or "none") + "."]
    return "\n".join(out) + "\n"


def main(run_dir, h2_file, out_dir=None):
    run_dir = pathlib.Path(run_dir).resolve()
    out_dir = pathlib.Path(out_dir) if out_dir else run_dir.parent / (run_dir.name + "-rq1-analysis")
    models, manifest = classify.load_models(run_dir)
    if manifest.get("r0_sha256") != classify.sha256_file(HERE / "rq1-r0.json"):
        sys.exit("rq1-r0.json differs from the R0 file recorded in the run manifest")
    frame_rows, sample_rows, provenance = ed.verified_inputs()  # frozen frame, recomputed sample, bound estimator
    sample = {r["case_id"] for r in sample_rows if r["sampled"] == "yes"}
    r0 = {c: json.loads((HERE / "rq1-r0.json").read_text())["classes"].get(c) for c in sample}
    seed = json.loads((HERE / "rq1-sample-manifest.json").read_text())["seed"]
    h2 = load_h2(json.loads(pathlib.Path(h2_file).read_text()), sample, seed, classify.CRITERIA_SHA256)
    res = analyse(frame_rows, sample_rows, r0, h2, models)
    res.update(run_dir=str(run_dir), h2_sha256=classify.sha256_file(pathlib.Path(h2_file)), **provenance)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "EXPLORATORY-H2.json").write_text(json.dumps(res, indent=1, default=str))
    (out_dir / "EXPLORATORY-H2.md").write_text(markdown(res))
    print(markdown(res))


if __name__ == "__main__":
    main(*sys.argv[1:4])
