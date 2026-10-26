#!/usr/bin/env python3
"""RQ1: what the R0 sheet recorded about how each label was reached (D42 point 3, D47): classes from the guided answers or
chosen directly, direct choices that contradict the answers, sources opened. Reads rq1-r0.json; prints a JSON summary.

    python3 preregistration/rq1/r0_report.py [rq1-r0.json]
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent


def report(doc):
    labelled = [c for c, v in doc["classes"].items() if v is not None]
    n = len(labelled)
    provenance = doc.get("class_set_directly")
    if doc.get("sheet") != "v3-guided" or provenance is None:
        # exports from sheets before the guided questions (D47) carry no provenance: every label was chosen directly
        provenance = {c: True for c in labelled}
    elif set(provenance) != set(labelled):
        sys.exit("class_set_directly does not cover exactly the labelled cases: provenance unavailable")
    direct = sorted(c for c in labelled if provenance.get(c))
    contra = sorted(c for c in labelled if doc.get("direct_class_contradicts_answers", {}).get(c))
    opened = sorted(c for c in labelled if doc.get("source_opened", {}).get(c))
    auto = sorted(c for c in labelled if doc.get("source_opened_auto", {}).get(c))
    share = lambda xs: round(len(xs) / n, 4) if n else None
    return {"labelled": n, "non_response": sorted(c for c, v in doc["classes"].items() if v is None),
            "from_guided_answers": n - len(direct), "chosen_directly": {"n": len(direct), "share": share(direct), "ids": direct},
            "direct_contradicting_answers": {"n": len(contra), "share": share(contra), "ids": contra},
            "source_opened": {"n": len(opened), "share": share(opened), "automatic_record": len(auto),
                              "note": "the automatic record is set by the sheet's link or key; the rest is the author's tick"},
            "sheet": doc.get("sheet"), "criteria_sha256": doc.get("criteria_sha256")}


if __name__ == "__main__":
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else HERE / "rq1-r0.json"
    print(json.dumps(report(json.loads(path.read_text())), indent=1))
