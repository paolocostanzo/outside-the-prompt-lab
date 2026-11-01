#!/usr/bin/env python3
"""Post hoc source audit (1 Nov 2026): recompute counts and shares from source-audit.csv.

Exploratory, not preregistered. Reads only source-audit.csv, ../rq1-sample.csv (stratum of each case),
../rq1-sample-manifest.json (stratum sizes) and, with --r0, ../rq1-r0.json for the cross-tab.
Uses ../estimate.py unmodified (import only). Standard library only.

Shares reported (A = A_no_model):
  1. decided only:   per stratum (M_h, n_decided_h, x_A_h)            -> A among A+B
  2. C against:      per stratum (M_h, n_h, x_A_h)                    -> C and B counted outside A, interval strict
  3. C both ways:    per stratum (M_h, n_h, x_A_h, u=C_h)             -> estimate.py convention for unlabelled cases
  4. sensitivity:    as 2 and 3, with A cases whose only basis is "the source frames the attacker as the tool caller"
                     (a_basis == tool_caller) moved to C.
Note for 1: estimate.py treats n_decided as a random draw from the stratum; decided cases are not a random subsample,
so that interval is descriptive only.
"""
import argparse, csv, json, pathlib, sys
from collections import Counter

HERE = pathlib.Path(__file__).resolve().parent
RQ1 = HERE.parent
sys.path.insert(0, str(RQ1))
import estimate as es  # noqa: E402  (unmodified, imported only)

OUT = ("A_no_model", "B_model", "C_undetermined")


def load():
    rows = list(csv.DictReader(open(HERE / "source-audit.csv", newline="")))
    sample = {r["case_id"]: r for r in csv.DictReader(open(RQ1 / "rq1-sample.csv", newline="", encoding="utf-8-sig"))}
    sizes = json.load(open(RQ1 / "rq1-sample-manifest.json"))["stratum_sizes"]
    for r in rows:
        s = sample[r["case_id"]]
        assert s["sampled"].strip() == "yes", r["case_id"]
        r["stratum"] = s["product_type"].strip()
        assert r["outcome"] in OUT, r
    return rows, sizes


def pct(x):
    return f"{float(x):.1%}"


def show(name, res):
    iv = res["interval"]
    ivs = "exact (all strata whole)" if iv is None else f"[{pct(iv[0])}, {pct(iv[1])}]"
    print(f"  {name:<34} share {pct(res['share'])}  unweighted {pct(res['unweighted'])}  95% {ivs}")


def strata_for(rows, sizes, mode, move_tool_caller=False):
    st = {}
    for t, M in sizes.items():
        rs = [r for r in rows if r["stratum"] == t]
        if not rs:
            continue
        def out(r):
            if move_tool_caller and r["outcome"] == "A_no_model" and r.get("a_basis") == "tool_caller":
                return "C_undetermined"
            return r["outcome"]
        c = Counter(out(r) for r in rs)
        a, b, u = c["A_no_model"], c["B_model"], c["C_undetermined"]
        if mode == "decided":
            st[t] = (M, a + b, a)
        elif mode == "against":
            st[t] = (M, len(rs), a)
        else:  # both ways
            st[t] = (M, len(rs), a, u)
    return st


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--r0", action="store_true", help="also print the cross-tab against rq1-r0.json (classes 1-3 vs 4)")
    args = ap.parse_args()
    rows, sizes = load()
    print(f"cases: {len(rows)}")
    tot = Counter(r["outcome"] for r in rows)
    print("counts:", {k: tot[k] for k in OUT})
    for t in sizes:
        c = Counter(r["outcome"] for r in rows if r["stratum"] == t)
        print(f"  {t:<24} M={sizes[t]:<4} n={sum(c.values()):<3} " + " ".join(f"{k[0]}={c[k]}" for k in OUT))
    nb = Counter(r["a_basis"] for r in rows if r["outcome"] == "A_no_model")
    print("A basis:", dict(nb))
    print("shares of A (stratified, weights = frame stratum sizes):")
    show("1 decided only (A / A+B)", es.stratified_share(strata_for(rows, sizes, "decided")))
    show("2 C counted against", es.stratified_share(strata_for(rows, sizes, "against")))
    show("3 C both ways in interval", es.stratified_share(strata_for(rows, sizes, "both")))
    show("4a sens.: tool_caller->C, decided", es.stratified_share(strata_for(rows, sizes, "decided", True)))
    show("4b sens.: tool_caller->C, against", es.stratified_share(strata_for(rows, sizes, "against", True)))
    if args.r0:
        cls = json.load(open(RQ1 / "rq1-r0.json"))["classes"]
        tab = Counter()
        for r in rows:
            k = cls.get(r["case_id"])
            col = "R0 1-3" if k in (1, 2, 3) else ("R0 4" if k == 4 else "R0 none")
            tab[(r["outcome"], col)] += 1
        cols = ["R0 1-3", "R0 4", "R0 none"]
        print("cross-tab (rows: source audit; cols: R0):")
        print("  " + " " * 16 + "".join(f"{c:>9}" for c in cols) + f"{'total':>9}")
        for o in OUT:
            print(f"  {o:<16}" + "".join(f"{tab[(o, c)]:>9}" for c in cols) + f"{sum(tab[(o, c)] for c in cols):>9}")
        print(f"  {'total':<16}" + "".join(f"{sum(tab[(o, c)] for o in OUT):>9}" for c in cols) + f"{len(rows):>9}")
        dec = [(o, c) for (o, c) in tab if o != "C_undetermined" and c != "R0 none"]
        agree = tab[("A_no_model", "R0 1-3")] + tab[("B_model", "R0 4")]
        n_dec = sum(tab[k] for k in dec)
        print(f"  agreement on decided cases (A~1-3, B~4): {agree}/{n_dec}")
        for o, c in (("A_no_model", "R0 4"), ("B_model", "R0 1-3")):
            ids = [r["case_id"] for r in rows if r["outcome"] == o and
                   (("R0 4" if cls.get(r["case_id"]) == 4 else "R0 1-3" if cls.get(r["case_id"]) in (1, 2, 3) else "R0 none") == c)]
            print(f"  {o} x {c}: {', '.join(ids) or '-'}")
        cr = Counter("R0 1-3" if cls.get(r["case_id"]) in (1, 2, 3) else "R0 4" if cls.get(r["case_id"]) == 4 else "none"
                     for r in rows if r["outcome"] == "C_undetermined")
        print(f"  C cases by R0: {dict(cr)}")


if __name__ == "__main__":
    main()
