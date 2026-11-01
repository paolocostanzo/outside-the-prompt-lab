"""Tests for rq1/fisher_flags.py (exploratory, D51) on synthetic counts. Run:
python3 -m unittest discover -s preregistration/test"""
import json, pathlib, sys, tempfile, unittest
from fractions import Fraction

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import fisher_flags as ff  # noqa: E402


def by_flag(f_cases, f_dis, f_nomaj, n_cases, n_dis, n_nomaj):
    return {"flagged (D41)": {"cases": f_cases, ff.DIS: f_dis, "no model majority": f_nomaj},
            "not flagged": {"cases": n_cases, ff.DIS: n_dis, "no model majority": n_nomaj}}


class Fisher(unittest.TestCase):
    def test_table_excludes_cases_without_majority(self):
        self.assertEqual(ff.table(by_flag(74, 10, 3, 46, 3, 0)), [[10, 61], [3, 43]])

    def test_known_values(self):
        self.assertEqual(ff.fisher_two_sided([[1, 0], [0, 1]]), 1)  # every table as probable as the observed one
        self.assertEqual(ff.fisher_two_sided([[3, 0], [0, 3]]), Fraction(2, 20))  # 1/20 each tail
        self.assertAlmostEqual(float(ff.fisher_two_sided([[1, 9], [11, 3]])), 0.002759, places=6)  # R fisher.test

    def test_symmetric_in_rows(self):
        self.assertEqual(ff.fisher_two_sided([[10, 61], [3, 43]]), ff.fisher_two_sided([[3, 43], [10, 61]]))

    def test_main_output(self):
        with tempfile.TemporaryDirectory() as d:
            p = pathlib.Path(d) / "x.json"; p.write_text(json.dumps({"by_flag": by_flag(74, 10, 3, 46, 3, 0)}))
            out = json.loads(ff.main(p))
        self.assertEqual(out["table"], [[10, 61], [3, 43]])
        self.assertEqual(out["p_two_sided_2dp"], "0.24")


if __name__ == "__main__":
    unittest.main()
