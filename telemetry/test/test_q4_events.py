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


import io as _io, json as _json, tarfile as _tarfile, tempfile as _tempfile


def _tgz(files):
    buf = _io.BytesIO()
    with _tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in files.items():
            info = _tarfile.TarInfo(name); info.size = len(data)
            tar.addfile(info, _io.BytesIO(data))
    return buf.getvalue()


class GroundTruthAndPlan(unittest.TestCase):
    def test_q3_ground_truth(self):
        run = {"client": "codex", "event": "q3-silent", "rep": 2}
        row_name = "q4-out/codex__none__description__r2/row.json"
        row = _json.dumps({"client": "codex", "signal": "none", "rep": 2}).encode()
        cell = "codex:none:description:r2"
        ts = '"ts":"2026-10-18T10:00:00.000Z"'
        good = (f'{{{ts},"event":"out","cell":"{cell}","state":"A"}}\n'
                f'{{{ts},"event":"definition-changed","cell":"{cell}","state":"B","from":"A","to":"B"}}\n').encode()
        self.assertEqual(q4.validate_ground_truth(run, _tgz({row_name: row, "q3-server.log": good})), [])
        bad_cases = {
            "server log missing": {row_name: row},
            "no change record": {row_name: row, "q3-server.log": f'{{{ts},"event":"out","cell":"{cell}"}}\n'.encode()},
            "change of another cell": {row_name: row, "q3-server.log": good.replace(cell.encode(), b"gemini:none:description:r1")},
            "truncated record": {row_name: row, "q3-server.log": good + b'{"ts":"2026-10-18T10:00:01Z","event":"defin'},
            "record without ts": {row_name: row, "q3-server.log": good + f'{{"event":"x","cell":"{cell}"}}\n'.encode()},
            "row.json missing": {"q3-server.log": good},
            "row.json of another cell": {row_name: _json.dumps({"client": "codex", "signal": "none", "rep": 1}).encode(),
                                         "q3-server.log": good},
        }
        for why, files in bad_cases.items():
            self.assertTrue(q4.validate_ground_truth(run, _tgz(files)), why)
        self.assertTrue(q4.validate_ground_truth(run, b"not a tar"))

    def test_q5_ground_truth(self):
        run = {"client": "goose", "event": "q5-start", "rep": 1}
        csv_ok = b"client,cell\ngoose,open-in-repo\n"
        self.assertEqual(q4.validate_ground_truth(run, _tgz({"q4-out/x/matrix.csv": csv_ok, "canary-start.log": b""})), [],
                         "an empty canary log is a valid 'no event', as long as it was copied")
        start = b'{"ts":"2026-10-18T10:00:00.000Z","event":"start","client":"goose","source":"x"}\n'
        self.assertEqual(q4.validate_ground_truth(run, _tgz({"q4-out/x/matrix.csv": csv_ok, "canary-start.log": start})), [])
        self.assertTrue(q4.validate_ground_truth(run, _tgz({"q4-out/x/matrix.csv": csv_ok, "canary-start.log": b'{"event":"st'})),
                        "a non-empty but malformed canary log is not usable ground truth")
        self.assertTrue(q4.validate_ground_truth(run, _tgz({"q4-out/x/matrix.csv": csv_ok})))
        self.assertTrue(q4.validate_ground_truth(run, _tgz({"q4-out/x/matrix.csv": b"client,cell\ncodex,after-decision\n",
                                                             "canary-start.log": b""})))

    def test_required_files_only(self):
        self.assertNotIn("ignore-failed-read", q4.ground_truth_command({"event": "q3-silent"}))
        self.assertIn("canary-start.log", q4.ground_truth_command({"event": "q5-start"}))

    def test_persisted_plan_is_executed_and_changed_inputs_refused(self):
        out = Path(_tempfile.mkdtemp())
        frozen = {"seed": 1, "snapshot": "s"}
        first = q4.load_or_create_plan(out, frozen, q4.plan(1))
        self.assertEqual(q4.load_or_create_plan(out, frozen, q4.plan(999)), first, "a restart runs the published order")
        with self.assertRaises(SystemExit):
            q4.load_or_create_plan(out, {"seed": 2, "snapshot": "s"}, q4.plan(2))

    def test_failed_attempt_is_kept_and_run_stays_incomplete(self):
        d = Path(_tempfile.mkdtemp()) / "run"
        d.mkdir()
        (d / "cell.stdout.txt").write_text("x")
        dest = q4.keep_attempt(d, "ground-truth-unavailable", {"problems": ["p"]})
        self.assertTrue((dest / "cell.stdout.txt").exists())
        self.assertEqual(_json.loads((dest / "attempt.json").read_text())["status"], "ground-truth-unavailable")
        self.assertFalse((d / "run.json").exists())
        self.assertEqual(q4.keep_attempt(d, "again", {}).name, "2")
