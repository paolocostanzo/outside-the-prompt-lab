"""Post hoc (1 Nov 2026): compare the source audit (Claude, source-audit.csv) with a blind second reading by a model of
another provider (Codex, source-audit-codex.csv). Joint outcome: A if both A, B if both B, otherwise U (undetermined or
disagreement). Shares use ../estimate.py unmodified. Standard library only; run with python3 -I."""
import csv, json, pathlib, sys
from collections import Counter
HERE = pathlib.Path(__file__).resolve().parent; RQ1 = HERE.parent
sys.path.insert(0, str(RQ1))
import estimate as es  # noqa: E402

a = {r["case_id"]: r["outcome"] for r in csv.DictReader(open(HERE / "source-audit.csv"))}
b = {r["case_id"]: r["outcome"] for r in csv.DictReader(open(HERE / "source-audit-codex.csv"))}
assert set(a) == set(b) and len(a) == 120
sample = {r["case_id"]: r["product_type"].strip() for r in csv.DictReader(open(RQ1 / "rq1-sample.csv", encoding="utf-8-sig"))
          if r["sampled"].strip() == "yes"}
sizes = json.load(open(RQ1 / "rq1-sample-manifest.json"))["stratum_sizes"]
joint = {k: (a[k][0] if a[k] == b[k] and a[k][0] in "AB" else "U") for k in a}
tab = Counter((a[k][0], b[k][0]) for k in a)
res = {"cross_tab_claude_x_codex": {f"{x}|{y}": n for (x, y), n in sorted(tab.items())},
       "exact_agreement": sum(a[k] == b[k] for k in a), "joint": dict(Counter(joint.values()))}
def strata(mode):
    st = {}
    for t, M in sizes.items():
        c = Counter(joint[k] for k in joint if sample[k] == t)
        if mode == "decided": st[t] = (M, c["A"] + c["B"], c["A"])
        else: st[t] = (M, sum(c.values()), c["A"])
    return st
for mode in ("decided", "against"):
    r = es.stratified_share(strata(mode))
    res[f"share_A_{mode}"] = {"share": r["share"], "interval": r["interval"]}
cls = json.load(open(RQ1 / "rq1-r0.json"))["classes"]
res["joint_x_R0"] = {f"{j}|R0 {r}": n for (j, r), n in sorted(
    Counter((joint[k], "1-3" if cls.get(k) in (1, 2, 3) else "4") for k in joint).items())}
(HERE / "COMPARE-RATERS.json").write_text(json.dumps(res, indent=1, default=str))
print(json.dumps(res, indent=1, default=str))
