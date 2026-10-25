"""Tests for rq1/estimate.py (D44 point 6). Run: python3 -m unittest discover -s preregistration/test"""
import pathlib, random, sys, unittest
from fractions import Fraction as F

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import estimate as es  # noqa: E402


class Estimate(unittest.TestCase):
    def test_proportional_sample(self):
        r = es.stratified_share({"a": (126, 30, 21), "m": (338, 81, 57), "s": (38, 9, 6)})
        self.assertLess(abs(r["share"] - r["unweighted"]), F(1, 200))
        lo, hi = r["interval"]; self.assertTrue(lo < r["share"] < hi); self.assertLess(hi - lo, F(30, 100))

    def test_weights_matter_when_disproportionate(self):
        r = es.stratified_share({"a": (100, 50, 50), "b": (100, 10, 0)})
        self.assertEqual(r["share"], F(1, 2)); self.assertEqual(r["unweighted"], F(5, 6))

    def test_census_is_exact(self):
        r = es.stratified_share({"a": (10, 10, 7), "b": (5, 5, 1)})
        self.assertTrue(r["exact"]); self.assertIsNone(r["interval"]); self.assertEqual(r["share"], F(8, 15))

    def test_codex_counterexample_is_covered(self):
        # D44-08: strata 150/150/3, sample 60/59/1, true positives 147/0/0; the first stratum's sample all positive
        r = es.stratified_share({"a": (150, 60, 60), "b": (150, 59, 0), "c": (3, 1, 0)})
        lo, hi = r["interval"]; self.assertTrue(lo <= F(147, 303) <= hi)

    def test_coverage_by_simulation(self):
        rnd = random.Random(7); pops = {"a": (126, 30, 80), "m": (338, 81, 250), "s": (38, 9, 10)}  # (M, n, true positives)
        truth = F(sum(K for _, _, K in pops.values()), sum(M for M, _, _ in pops.values())); miss = 0
        for _ in range(300):
            st = {k: (M, n, sum(rnd.sample([1] * K + [0] * (M - K), n))) for k, (M, n, K) in pops.items()}
            lo, hi = es.stratified_share(st)["interval"]; miss += not (lo <= truth <= hi)
        self.assertLessEqual(miss, 15)  # at most 5% of 300

    def test_hyper_bounds_edges(self):
        self.assertEqual(es.hyper_bounds(10, 10, 4, F(1, 100)), (4, 4))
        lo, hi = es.hyper_bounds(100, 20, 0, F(1, 40)); self.assertEqual(lo, 0); self.assertGreater(hi, 0)
        lo, hi = es.hyper_bounds(100, 20, 20, F(1, 40)); self.assertEqual(hi, 100); self.assertLess(lo, 100)

    def test_singleton_census_empty_strata(self):
        r = es.stratified_share({"a": (100, 40, 30), "b": (20, 1, 1), "c": (3, 3, 0), "d": (0, 0, 0)})
        self.assertFalse(r["exact"]); lo, hi = r["interval"]; self.assertTrue(lo < r["share"] < hi)

    def test_bad_input(self):
        for bad in ({"a": (10, 11, 1)}, {"a": (10, 0, 0)}, {"a": (10, 5, 6)}, {"a": (10.5, 5, 1)}):
            with self.assertRaises(ValueError): es.stratified_share(bad)

    def test_equal_weights_use_true_sizes_for_bounds(self):
        st = {"a": (100, 40, 30), "m": (300, 80, 40), "s": (30, 10, 5)}
        eq = es.stratified_share(st, weights={"a": 1, "m": 1, "s": 1})
        self.assertEqual(eq["share"], (F(30, 40) + F(40, 80) + F(5, 10)) / 3)
        lo, hi = eq["interval"]; self.assertTrue(lo < eq["share"] < hi)
        self.assertNotEqual(eq["share"], es.stratified_share(st)["share"])

    def test_unlabelled_cases_widen_both_ways(self):
        # D44-15: availability correlated with class; 200 cases, 100 sampled, 50 labelled positive, 50 unlabelled (truly negative)
        r = es.stratified_share({"s": (200, 100, 50, 50)})
        self.assertEqual(r["share"], F(1, 2)); lo, hi = r["interval"]
        self.assertTrue(lo <= F(1, 2) <= hi); self.assertGreater(hi, F(9, 10))
        full = es.stratified_share({"s": (200, 200, 100, 100)})  # census with unlabelled cases: not exact
        self.assertFalse(full["exact"]); self.assertEqual(full["interval"], (F(1, 2), F(1)))
        with self.assertRaises(ValueError): es.stratified_share({"s": (200, 100, 60, 50)})

    def test_h1_verdict(self):
        sup = {"share": F(7, 10), "interval": (F(61, 100), F(78, 100)), "exact": False}
        weak = {"share": F(7, 10), "interval": (F(55, 100), F(80, 100)), "exact": False}
        edge = {"share": F(60, 100), "interval": (F(50, 100), F(70, 100)), "exact": False}
        low = {"share": F(59, 100), "interval": (F(50, 100), F(70, 100)), "exact": False}
        self.assertEqual(es.h1_verdict(sup, sup), "supported, interval above 60%")
        self.assertEqual(es.h1_verdict(sup, weak), "supported on the point estimate only")
        self.assertEqual(es.h1_verdict(edge, sup), "supported on the point estimate only")
        self.assertEqual(es.h1_verdict(sup, low), "not supported")


if __name__ == "__main__":
    unittest.main()
