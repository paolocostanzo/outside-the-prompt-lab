"""Tests for rq1/second_rater.py and rq1/h2_sheet.py (exploratory, D51) on synthetic labels. Run:
python3 -m unittest discover -s preregistration/test"""
import json, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import second_rater as sr  # noqa: E402
import h2_sheet  # noqa: E402

M = ["qwen3.8:27b-q8_0", "gemma4:26b-a4b-it-q8_0", "nemotron-3.5-lightning:30b-a3b-q4_K_M"]
T = "MCP server or connector"


def world(n=20, size=40):
    frame = [{"case_id": f"C{i:02d}", "decision": "include", "product_type": T} for i in range(size)]
    sample = [{"case_id": f"C{i:02d}", "product_type": T, "sampled": "yes" if i < n else "no"} for i in range(size)]
    ids = [f"C{i:02d}" for i in range(n)]
    return frame, sample, ids


class SecondRater(unittest.TestCase):
    def test_identical_humans(self):
        frame, sample, ids = world()
        r0 = {c: (4 if i % 5 == 0 else 3) for i, c in enumerate(ids)}
        res = sr.analyse(frame, sample, r0, dict(r0), {m: dict(r0) for m in M})
        self.assertAlmostEqual(res["pairs"]["H2 vs R0"]["four_class"]["cohen_kappa"], 1.0)
        self.assertEqual(res["binary_disagreement_R0_H2"], [])
        self.assertEqual(res["h2_share"]["share"], res["r0_share"]["share"])

    def test_binary_disagreement_listed(self):
        frame, sample, ids = world()
        r0 = {c: 3 for c in ids}; r0[ids[0]] = 4; r0[ids[1]] = 4
        h2 = dict(r0); h2[ids[0]] = 1; h2[ids[2]] = 1  # ids[0]: 4 vs 1 (binary); ids[2]: 3 vs 1 (within product)
        res = sr.analyse(frame, sample, r0, h2, {m: dict(r0) for m in M})
        self.assertEqual(res["binary_disagreement_R0_H2"], [ids[0]])
        self.assertEqual(res["confusion_R0_vs_H2"][3][1], 1)
        self.assertEqual(res["confusion_R0_vs_H2"][4][1], 1)

    def test_unlabelled_h2(self):
        frame, sample, ids = world()
        r0 = {c: 3 for c in ids}; r0[ids[3]] = 4
        h2 = dict(r0); h2[ids[5]] = None
        res = sr.analyse(frame, sample, r0, h2, {m: dict(r0) for m in M})
        self.assertEqual(res["h2_unlabelled"], [ids[5]])
        self.assertEqual(res["pairs"]["H2 vs R0"]["four_class"]["n"], len(ids) - 1)

    def test_load_h2_validation(self):
        sample = {"A", "B"}
        ok = {"rater": "H2", "sheet": sr.SHEET, "declaration": sr.DECLARATION, "seed": "s", "criteria_sha256": "c",
              "classes": {"A": 3, "B": None}}
        self.assertEqual(sr.load_h2(ok, sample, "s", "c"), {"A": 3, "B": None})
        bad = [{**ok, "rater": "R0"}, {**ok, "sheet": "v3-guided"}, {**ok, "declaration": "x"}, {**ok, "seed": "t"},
               {**ok, "criteria_sha256": "d"}, {**ok, "classes": {"A": 3}}, {**ok, "classes": {"A": 5, "B": 4}},
               {**ok, "classes": {"A": True, "B": 4}}, {**ok, "classes": {"A": 1.0, "B": 4}}]
        for doc in bad:
            with self.assertRaises(SystemExit):
                sr.load_h2(doc, sample, "s", "c")


class Sheet(unittest.TestCase):
    def test_h2_page_is_blind_and_separate(self):
        page = h2_sheet.build()
        self.assertNotIn("rq1-r0", page)
        self.assertIn("rq1-h2.json", page)
        self.assertIn(f'sheet: "{sr.SHEET}"', page)
        self.assertIn(sr.DECLARATION, page)
        for word in ("qwen", "gemma", "nemotron"):
            self.assertNotIn(word, page.lower())
        data = json.loads(page.split("const CASES = ", 1)[1].split("; const NONRESP", 1)[0])
        self.assertEqual({k for d in data for k in d}, {"id", "summary", "summary_it", "src", "bundle"})

    def test_calibration_uses_pilot_only(self):
        cal = h2_sheet.calibration()
        self.assertEqual(cal.count("\n## C"), 10)
        self.assertIn("## C01 — classe / class 4", cal)
        self.assertNotIn("RQ1-", cal)


if __name__ == "__main__":
    unittest.main()
