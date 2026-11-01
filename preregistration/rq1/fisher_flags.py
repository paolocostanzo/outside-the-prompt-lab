#!/usr/bin/env python3
"""Exploratory (D51): two-sided Fisher exact test of whether R0 and the model majority disagree (four classes) more often among
the flagged summaries than among the others, on the cases that have a model majority. The paper quotes p = 0.24 from these
counts. Reads the D51 output written by explore_disagreement.py and prints the 2x2 table and p as JSON. Standard library only.

    python3 preregistration/rq1/fisher_flags.py EXPLORATORY-DISAGREEMENT.json

Two-sided p: the sum of the hypergeometric probabilities of every table with the observed margins that is no more probable than
the observed one (the usual definition, as in R's fisher.test; probabilities are compared exactly, as fractions).
"""
import json, math, sys
from fractions import Fraction

DIS = "R0 vs majority disagree (4 classes)"
GROUPS = ("flagged (D41)", "not flagged")


def table(by_flag):
    """[[disagree, agree] for flagged, [disagree, agree] for not flagged], on the cases with a model majority."""
    rows = []
    for g in GROUPS:
        v = by_flag[g]
        with_majority = v["cases"] - v["no model majority"]
        rows.append([v[DIS], with_majority - v[DIS]])
    return rows


def fisher_two_sided(t):
    (a, b), (c, d) = t
    r1, c1, n = a + b, a + c, a + b + c + d
    prob = lambda x: Fraction(math.comb(c1, x) * math.comb(n - c1, r1 - x), math.comb(n, r1))
    obs = prob(a)
    return sum(p for p in (prob(x) for x in range(max(0, r1 + c1 - n), min(r1, c1) + 1)) if p <= obs)


def main(path):
    res = json.loads(open(path).read())
    t = table(res["by_flag"])
    p = fisher_two_sided(t)
    out = {"exploratory": "D51: disagreement (4 classes) by flag, cases with a model majority; two-sided Fisher exact test",
           "rows": list(GROUPS), "columns": ["disagree", "agree"], "table": t,
           "p_two_sided": f"{float(p):.6f}", "p_two_sided_2dp": f"{float(p):.2f}"}
    return json.dumps(out, indent=1) + "\n"


if __name__ == "__main__":
    sys.stdout.write(main(sys.argv[1]))
