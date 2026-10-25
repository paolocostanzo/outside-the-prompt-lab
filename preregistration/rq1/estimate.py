#!/usr/bin/env python3
"""RQ1 share estimate on the D44 sample: stratified estimator and a conservative 95% interval from exact hypergeometric bounds
per stratum, Bonferroni-split across the sampled strata and combined with the population weights (D44 point 6). Exact
fractions throughout, so the H1 verdict does not depend on floating point. Standard library only."""
import hashlib, pathlib, subprocess, sys
from fractions import Fraction
from math import comb

ALPHA = Fraction(5, 100)
H1_SHARE = Fraction(60, 100)


def _tail_ge(N, K, n, x):  # P(X >= x), X hypergeometric: K positives among N, n drawn
    return Fraction(sum(comb(K, i) * comb(N - K, n - i) for i in range(x, min(n, K) + 1)), comb(N, n))


def _tail_le(N, K, n, x):
    return Fraction(sum(comb(K, i) * comb(N - K, n - i) for i in range(max(0, n - (N - K)), x + 1)), comb(N, n))


def hyper_bounds(N, n, x, a):
    """Exact bounds for the number of positives K in a stratum of N, given x of n sampled, each tail at level a."""
    ks = range(x, N - (n - x) + 1)
    lo = next(K for K in ks if _tail_ge(N, K, n, x) > a)
    hi = next(K for K in reversed(ks) if _tail_le(N, K, n, x) > a)
    return lo, hi


def stratified_share(strata, alpha=ALPHA, weights=None):
    """strata: {name: (M_h, n_h, x_h) or (M_h, n_h, x_h, u_h)}: M_h the stratum size of the frozen frame (D44 point 5: eligibility is settled before the draw; an integer >= n_h, used for the weights and the bounds),
    n_h sampled, x_h sampled cases labelled in classes 1-3, u_h sampled cases without a label (non-response, no majority; D44
    point 6: counted outside classes 1-3 in the share, both ways in the interval). Empty strata (M_h = 0) are ignored. weights (optional, e.g. equal weights for
    the secondary estimate of D44 point 6) replace M_h / sum M_h for the share and for combining the bounds; the bounds always use
    the true M_h. Returns share, unweighted share and interval as Fractions; the interval is None when every stratum is taken
    whole (the share is then exact)."""
    s = {k: (tuple(v) + (0,))[:4] for k, v in strata.items() if v[0] > 0}
    for k, (M, n, x, u) in s.items():
        if not all(type(v) is int for v in (M, n, x, u)) or not (1 <= n <= M) or not (0 <= x <= n) or not (0 <= u <= n - x):
            raise ValueError(f"stratum {k}: need integers 1 <= n <= M, 0 <= x, 0 <= u, x + u <= n, got {M, n, x, u}")
    total = sum(v[0] for v in s.values())
    w = {k: Fraction(v[0], total) for k, v in s.items()}
    if weights is not None:
        ws = {k: Fraction(weights[k]) for k in s}
        w = {k: v / sum(ws.values()) for k, v in ws.items()}
    share = sum(w[k] * Fraction(x, n) for k, (M, n, x, u) in s.items())
    unweighted = Fraction(sum(v[2] for v in s.values()), sum(v[1] for v in s.values()))
    sampled = [k for k, v in s.items() if v[1] < v[0]]
    if not sampled and not any(v[3] for v in s.values()):
        return {"share": share, "unweighted": unweighted, "interval": None, "exact": True}
    a = alpha / 2 / max(1, len(sampled))  # no sampled stratum: only the unlabelled cases make the interval
    lo = hi = Fraction(0)
    for k, (M, n, x, u) in s.items():
        kl = hyper_bounds(M, n, x, a)[0] if k in sampled else x  # unlabelled counted outside classes 1-3
        kh = hyper_bounds(M, n, x + u, a)[1] if k in sampled else x + u  # unlabelled counted inside
        lo += w[k] * Fraction(kl, M); hi += w[k] * Fraction(kh, M)
    return {"share": share, "unweighted": unweighted, "interval": (lo, hi), "exact": False}


def h1_verdict(r0, models):
    """D44 point 6: H1 holds when the point estimate is at least 60% for both R0 and the model majority."""
    if r0["share"] < H1_SHARE or models["share"] < H1_SHARE:
        return "not supported"
    def above(r): return r["exact"] or r["interval"][0] >= H1_SHARE
    return "supported, interval above 60%" if above(r0) and above(models) else "supported on the point estimate only"


def bound_to(commit):
    """D44: the analysis runs only with the estimate.py of the frame commit; returns its SHA-256 for the analysis output."""
    here = pathlib.Path(__file__).resolve()
    copy = subprocess.run(["git", "-C", str(here.parent), "show", f"{commit}:preregistration/rq1/estimate.py"],
                          capture_output=True, check=True).stdout
    if copy != here.read_bytes():
        sys.exit("estimate.py differs from its copy in the frame commit")
    return hashlib.sha256(copy).hexdigest()
