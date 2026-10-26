"""Tests for rq1/r0_report.py. Run: python3 -m unittest discover -s preregistration/test"""
import pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import r0_report as rr  # noqa: E402


class Report(unittest.TestCase):
    def test_shares_and_ids(self):
        doc = {"classes": {"A": 1, "B": 4, "C": 3, "D": None},
               "class_set_directly": {"A": False, "B": True, "C": True},
               "direct_class_contradicts_answers": {"A": False, "B": False, "C": True},
               "source_opened": {"A": True, "B": False, "C": True}, "source_opened_auto": {"A": True, "B": False, "C": False},
               "sheet": "v3-guided"}
        r = rr.report(doc)
        self.assertEqual(r["labelled"], 3); self.assertEqual(r["non_response"], ["D"]); self.assertEqual(r["from_guided_answers"], 1)
        self.assertEqual(r["chosen_directly"], {"n": 2, "share": 0.6667, "ids": ["B", "C"]})
        self.assertEqual(r["direct_contradicting_answers"]["ids"], ["C"])
        self.assertEqual(r["source_opened"]["n"], 2); self.assertEqual(r["source_opened"]["automatic_record"], 1)

    def test_old_export_without_fields(self):  # a pre-guided export: every label was chosen directly
        r = rr.report({"classes": {"A": 2, "B": None}, "sheet": "v2"})
        self.assertEqual(r["chosen_directly"]["n"], 1); self.assertEqual(r["from_guided_answers"], 0)
        self.assertEqual(r["source_opened"]["n"], 0)

    def test_incomplete_provenance_refused(self):
        with self.assertRaises(SystemExit):
            rr.report({"classes": {"A": 2, "B": 1}, "sheet": "v3-guided", "class_set_directly": {"A": False}})


if __name__ == "__main__":
    unittest.main()
