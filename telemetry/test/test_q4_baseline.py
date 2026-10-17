"""q4_baseline.py: plan, commands and the holdout gap (D13 point 2, D24 point 4). No VM. Run: python3 -m unittest discover -s telemetry/test"""
import importlib.util, json, tempfile, time, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("q4_baseline", SCRIPTS / "q4_baseline.py")
qb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qb)


class BaselinePlan(unittest.TestCase):
    def test_dev_block_then_holdout_block_in_the_same_order(self):
        p = qb.plan(11)
        self.assertEqual(len(p), 12)
        dev = [s["client"] for s in p if s["part"] == "dev"]
        hold = [s["client"] for s in p if s["part"] == "holdout"]
        self.assertEqual(dev, hold)
        self.assertEqual(sorted(dev), sorted(qb.ev.CLIENTS))
        self.assertEqual([s["part"] for s in p], ["dev"] * 6 + ["holdout"] * 6)
        self.assertEqual(qb.plan(11), p)

    def test_command(self):
        c = qb.session_command({"client": "gemini", "part": "holdout"}, 60)
        self.assertEqual(c, "python3 ~/lab/telemetry/scripts/baseline_session.py --client gemini --part holdout --minutes 60 --out ~/q4-out")

    def test_holdout_waits_for_the_gap(self):
        out = Path(tempfile.mkdtemp())
        (out / "baseline__codex__dev").mkdir()
        (out / "baseline__codex__dev" / "run.json").write_text(json.dumps({"t1": time.time() - 3600}))
        slept, notes = [], []
        w = qb.wait_for_gap(out, {"client": "codex", "part": "holdout", "name": "x"}, 6, lambda **k: notes.append(k), slept.append)
        self.assertAlmostEqual(w, 5 * 3600, delta=5)
        self.assertAlmostEqual(slept[0], 5 * 3600, delta=5)
        self.assertEqual(qb.wait_for_gap(out, {"client": "codex", "part": "dev", "name": "y"}, 6, print, slept.append), 0)
        (out / "baseline__codex__dev" / "run.json").write_text(json.dumps({"t1": time.time() - 7 * 3600}))
        self.assertEqual(qb.wait_for_gap(out, {"client": "codex", "part": "holdout", "name": "x"}, 6, print, slept.append), 0)
        self.assertEqual(len(slept), 1)


if __name__ == "__main__":
    unittest.main()
