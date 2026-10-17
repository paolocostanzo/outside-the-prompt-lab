"""q4_events.py: the plan and the commands (D24 point 3). No VM is touched. Run: python3 -m unittest discover -s telemetry/test"""
import collections, importlib.util, subprocess, sys, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("q4_events", SCRIPTS / "q4_events.py")
q4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q4)


class Plan(unittest.TestCase):
    def test_36_runs_each_client_event_once_per_block(self):
        runs = q4.plan(20261018)
        self.assertEqual(len(runs), 36)
        self.assertEqual(len({r["name"] for r in runs}), 36)
        per = collections.Counter((r["client"], r["event"]) for r in runs)
        self.assertEqual(set(per.values()), {2})
        for rep in (1, 2):
            block = [(r["client"], r["event"]) for r in runs if r["rep"] == rep]
            self.assertEqual(len(block), 18)
            self.assertEqual(len(set(block)), 18)
        self.assertEqual([r["rep"] for r in runs], [1] * 18 + [2] * 18, "block 1 runs entirely before block 2")

    def test_seed_fixes_the_order(self):
        self.assertEqual(q4.plan(7), q4.plan(7))
        self.assertNotEqual([r["name"] for r in q4.plan(7)], [r["name"] for r in q4.plan(8)])

    def test_commands(self):
        q5 = q4.cell_command({"client": "codex", "event": "q5-start", "rep": 2})
        self.assertIn("run_q5_matrix.py", q5)
        self.assertIn("--only codex:after-decision", q5)
        self.assertIn("--reps 1", q5)
        self.assertIn("--only goose:open-in-repo", q4.cell_command({"client": "goose", "event": "q5-start", "rep": 1}))
        a = q4.cell_command({"client": "gemini", "event": "q3-announced", "rep": 1})
        s = q4.cell_command({"client": "gemini", "event": "q3-silent", "rep": 1})
        self.assertIn("--signal list_changed", a)
        self.assertIn("--signal none", s)
        self.assertIn("--change description", s)
        self.assertEqual(q4.collect_command(10, 20),
                         "python3 -I ~/lab/telemetry/scripts/vm_logs.py collect ~/lab/telemetry/inventory/candidates.json 10 20")

    def test_every_client_has_a_q5_cell_and_matches_the_inventory_names(self):
        self.assertEqual(set(q4.Q5_CELL), set(q4.CLIENTS))
        import json
        cand = json.loads((SCRIPTS.parent / "inventory/candidates.json").read_text())
        self.assertTrue(set(q4.CLIENTS) <= set(cand))

    def test_dry_run_touches_nothing(self):
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "q4_events.py"), "--snapshot", "x", "--seed", "1",
                            "--inventory", "/nonexistent.json", "--out", "/nonexistent-dir", "--dry-run"],
                           capture_output=True, text=True, check=True)
        self.assertEqual(len([l for l in r.stdout.splitlines() if "__r" in l]), 36)
        self.assertFalse(Path("/nonexistent-dir").exists())


if __name__ == "__main__":
    unittest.main()
