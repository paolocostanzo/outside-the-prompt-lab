"""Tests for rq1/explore_disagreement.py (exploratory, D51) on synthetic labels. Run:
python3 -m unittest discover -s preregistration/test"""
import pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import explore_disagreement as ed  # noqa: E402

M = ["qwen3.8:27b-q8_0", "gemma4:26b-a4b-it-q8_0", "nemotron-3.5-lightning:30b-a3b-q4_K_M"]


def world(r0, per_model, types=None, flagged=()):
    ids = sorted(r0)
    sample = {c: (types or {}).get(c, "MCP server or connector") for c in ids}
    return sample, dict(r0), {m: dict(per_model[m]) for m in M}, set(flagged)


class Explore(unittest.TestCase):
    def test_perfect_agreement(self):
        r0 = {f"C{i}": (3 if i % 4 else 4) for i in range(12)}
        res = ed.analyse(*world(r0, {m: r0 for m in M}))
        self.assertAlmostEqual(res["four_class"]["R0 vs model majority"]["cohen_kappa"], 1.0)
        self.assertAlmostEqual(res["binary"]["R0 vs model majority"]["cohen_kappa"], 1.0)
        self.assertEqual(res["binary"]["R0 vs model majority"]["pabak"], 1.0)
        self.assertEqual(res["disagreement_pairs"]["R0 vs model majority"], {})
        self.assertEqual(res["binary_disagreement_cases"], [])

    def test_within_product_disagreement_is_not_binary(self):
        # R0 says 3, every model says 1: four-class disagreement, binary agreement (both 'product').
        r0 = {f"C{i}": 3 for i in range(6)} | {f"D{i}": 4 for i in range(4)}
        mod = {c: (1 if c.startswith("C") else 4) for c in r0}
        res = ed.analyse(*world(r0, {m: mod for m in M}))
        self.assertEqual(res["disagreement_pairs"]["R0 vs model majority"], {"1-3": 6})
        self.assertEqual(res["binary_disagreement_cases"], [])
        self.assertEqual(res["binary"]["R0 vs model majority"]["percent_agreement"], 1.0)
        self.assertEqual(res["confusion"]["R0 vs model majority"][3][1], 6)

    def test_binary_disagreement_and_groups(self):
        r0 = {"A": 4, "B": 3, "C": 3, "D": 4}
        mod = {"A": 3, "B": 3, "C": 3, "D": 4}
        res = ed.analyse(*world(r0, {m: mod for m in M}, types={"A": "agent client"}, flagged=["A"]))
        self.assertEqual(res["binary_disagreement_cases"], ["A"])
        self.assertEqual(res["by_flag"]["flagged (D41)"]["R0 vs majority disagree (binary)"], 1)
        self.assertEqual(res["by_flag"]["not flagged"]["R0 vs majority disagree (binary)"], 0)
        self.assertEqual(res["by_product_type"]["agent client"]["cases"], 1)

    def test_no_majority_and_missing_labels(self):
        r0 = {"A": 3, "B": None, "C": 4}
        per = {M[0]: {"A": 1, "B": 3, "C": 4}, M[1]: {"A": 2, "B": 3, "C": 4}, M[2]: {"A": 3, "B": 3, "C": None}}
        res = ed.analyse(*world(r0, per))
        self.assertEqual(res["by_flag"]["not flagged"]["no model majority"], 1)  # A: 1/2/3
        self.assertEqual(res["four_class"]["R0 vs model majority"]["n"], 1)      # only C labelled by both
        self.assertEqual(res["four_class"]["Fleiss, R0 + three models"]["n"], 1)  # only A complete

    def test_specific_agreement(self):
        a = {"A": 1, "B": 1, "C": 3}
        b = {"A": 1, "B": 3, "C": 3}
        self.assertAlmostEqual(ed.specific_agreement(a, b, 1), 2 / 3)
        self.assertAlmostEqual(ed.specific_agreement(a, b, 3), 2 / 3)
        self.assertIsNone(ed.specific_agreement(a, b, 4))

    def test_bootstrap_is_seeded(self):
        r0 = {f"C{i}": (3 if i % 3 else 4) for i in range(30)}
        mod = {c: (v if int(c[1:]) % 7 else 1) for c, v in r0.items()}
        one = ed.analyse(*world(r0, {m: mod for m in M}))
        two = ed.analyse(*world(r0, {m: mod for m in M}))
        self.assertEqual(one["four_class"]["R0 vs model majority"]["kappa_95"],
                         two["four_class"]["R0 vs model majority"]["kappa_95"])


if __name__ == "__main__":
    unittest.main()
