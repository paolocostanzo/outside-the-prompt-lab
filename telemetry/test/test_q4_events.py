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


from types import SimpleNamespace as _NS


class PlanPhase04(unittest.TestCase):
    """Fixes of the plan review of 17 Oct 2026 (phase 0.4): host telemetry checked, quota stops, memory before restore, --reps."""
    class FakeHost:
        def __init__(self, answers):
            self.answers = answers  # substring of the command -> (rc, stdout, stderr)
        def ssh(self, ip, cmd, timeout=120):
            for key, (rc, out, err) in self.answers.items():
                if key in cmd:
                    return _NS(returncode=rc, stdout=out, stderr=err)
            return _NS(returncode=0, stdout="x\n", stderr="")

    def runner(self, answers):
        return q4.Runner(self.FakeHost(answers), None), Path(_tempfile.mkdtemp())

    def test_complete_telemetry(self):
        rn, d = self.runner({})
        self.assertEqual(rn.telemetry("ip", d, 100), [])
        self.assertEqual(sorted(_json.loads((d / "telemetry/status.json").read_text())), sorted(n for n, _, _ in q4.TELEMETRY))

    def test_failed_or_empty_telemetry_is_a_problem(self):
        rn, d = self.runner({"audit.log": (1, "", "sudo: a password is required"), "journalctl": (0, "", "")})
        problems = rn.telemetry("ip", d, 100)
        self.assertEqual(len(problems), 2, problems)
        self.assertIn("password", (d / "telemetry/audit.log.stderr").read_text())
        rn, d = self.runner({"nft list": (0, "", "")})
        self.assertEqual(rn.telemetry("ip", d, 100), [], "an empty nft ruleset is allowed; audit and journal are not")

    def test_quota_in_run_captures(self):
        qm = q4.load(SCRIPTS / "quota.py", "quota")
        tgz = _tgz({"q4-out/codex__none__description__r1/codex__none__r1__03-p2-end.txt": b"You've hit your usage limit."})
        self.assertIn("usage limit", q4.quota_in_outputs("codex", tgz, qm))
        self.assertIsNone(q4.quota_in_outputs("codex", _tgz({"q4-out/x/a.txt": b"ok"}), qm))

    def test_memory_wait(self):
        d = Path(_tempfile.mkdtemp())
        mem, buddy = d / "meminfo", d / "buddyinfo"
        buddy.write_text("Node 0, zone   Normal  100 50 20 10 5 4 15 10 0 0 0\n")
        mem.write_text("MemAvailable:    2048000 kB\n")
        self.assertEqual(q4.wait_for_memory(print, meminfo=mem, buddyinfo=buddy), (2000, 25))
        mem.write_text("MemAvailable:     500000 kB\n")
        clock = iter(range(0, 10000, 60))
        notes = []
        with self.assertRaises(SystemExit) as e:
            q4.wait_for_memory(lambda **k: notes.append(k), sleep=lambda s: None, now=lambda: next(clock), meminfo=mem, buddyinfo=buddy)
        self.assertEqual(e.exception.code, 4)
        self.assertEqual(notes[-1]["event"], "abort-memory")

    def test_reps_option(self):
        self.assertEqual(len(q4.plan(1, ["gemini"], reps=1)), 3)
        r = subprocess.run([sys.executable, "-I", str(SCRIPTS / "q4_events.py"), "--snapshot", "x", "--seed", "1", "--inventory", "/x",
                            "--out", "/nonexistent-dir", "--clients", "gemini", "--reps", "1", "--dry-run"], capture_output=True, text=True, check=True)
        self.assertEqual(len([l for l in r.stdout.splitlines() if "__r" in l]), 3)


class InspectionRound1(unittest.TestCase):
    """Fixes of the code inspection of 17 Oct 2026, round 1."""
    def test_timeout_becomes_a_failed_result(self):
        def boom(*a, **k):
            raise subprocess.TimeoutExpired(cmd="ssh", timeout=120, output=b"partial audit", stderr=b"")
        r = q4.safe(boom)
        self.assertEqual((r.returncode, r.stdout), (124, "partial audit"))
        self.assertIn("timeout", r.stderr)

    def test_telemetry_timeout_is_recorded_not_raised(self):
        class H:
            def ssh(self, ip, cmd, timeout=120):
                if "audit.log" in cmd:
                    raise subprocess.TimeoutExpired(cmd="ssh", timeout=timeout)
                return _NS(returncode=0, stdout="x\n", stderr="")
        d = Path(_tempfile.mkdtemp())
        problems = q4.Runner(H(), None).telemetry("ip", d, 1)
        self.assertTrue(any("audit.log" in p and "124" in p for p in problems), problems)
        self.assertTrue((d / "telemetry/status.json").exists())

    def test_interrupted_attempt_is_kept_before_a_rerun(self):
        d = Path(_tempfile.mkdtemp()) / "run"
        d.mkdir()
        (d / "cell.stdout.txt").write_text("half")
        kept = q4.preserve_interrupted(d)
        self.assertTrue((kept / "cell.stdout.txt").exists())
        self.assertEqual(_json.loads((kept / "attempt.json").read_text())["status"], "interrupted")
        self.assertIsNone(q4.preserve_interrupted(d), "an empty folder (only attempts/) is not an attempt")

    def test_memory_is_checked_before_every_revert(self):
        calls = {"wait": 0, "revert": 0}
        orig = q4.wait_for_memory
        q4.wait_for_memory = lambda note: calls.__setitem__("wait", calls["wait"] + 1) or (2000, 30)
        self.addCleanup(lambda: setattr(q4, "wait_for_memory", orig))
        class Q3:
            VIRSH, DOMAIN = ["virsh"], "agentlab"
            @staticmethod
            def run(cmd, **k):
                if "snapshot-revert" in cmd:
                    calls["revert"] += 1
                    return _NS(returncode=0 if calls["revert"] >= 3 else 1, stdout="", stderr="apparmor")
                return _NS(returncode=0, stdout="running", stderr="")
        class H:
            def order6_blocks(self): return 5
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=0, stdout=f"{__import__('time').time():.3f}\n" if cmd.startswith("date +%s") else "", stderr="")
        ip, _, skew = q4.fresh_vm_checked(H(), Q3, "snap", lambda **k: None, sleep=lambda s: None)
        self.assertLess(abs(skew), 2)
        self.assertEqual(ip, "1.2.3.4")
        self.assertEqual((calls["revert"], calls["wait"]), (3, 3), "one memory check per revert attempt")


class InspectionRound2(unittest.TestCase):
    def q3(self):
        class Q3:
            VIRSH, DOMAIN = ["virsh"], "agentlab"
            @staticmethod
            def run(cmd, **k): return _NS(returncode=0, stdout="running", stderr="")
        return Q3

    def test_clock_out_of_step_stops_before_the_run(self):
        orig = q4.wait_for_memory
        q4.wait_for_memory = lambda note: (2000, 30)
        self.addCleanup(lambda: setattr(q4, "wait_for_memory", orig))
        class H:
            def order6_blocks(self): return 30
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=0, stdout=f"{__import__('time').time() - 3600:.3f}\n" if cmd.startswith("date +%s") else "", stderr="")
        notes = []
        with self.assertRaises(SystemExit) as e:
            q4.fresh_vm_checked(H(), self.q3(), "snap", lambda **k: notes.append(k), sleep=lambda s: None)
        self.assertEqual(e.exception.code, 6)
        self.assertEqual(notes[-1]["event"], "abort-clock")

    def test_pending_attempt_with_unreachable_vm_stops_without_restoring(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        class H:
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120): return _NS(returncode=255, stdout="", stderr="no route")
        notes = []
        with self.assertRaises(SystemExit) as e:
            q4.recover_pending(d, H(), None, None, None, None, "codex", "true", lambda **k: notes.append(k))
        self.assertEqual(e.exception.code, 7)
        self.assertTrue((d / "pending.json").exists(), "nothing is discarded")

    def test_pending_attempt_is_recovered_from_a_reachable_vm(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        class H:
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120): return _NS(returncode=0, stdout="x\n", stderr="")
        class Rn:
            def client_logs(self, *a): return {"export": "ok"}
            def ssh_bin(self, ip, cmd, dest): Path(dest).write_bytes(b"tgz"); return 0, ""
            def telemetry(self, ip, d, since): return []
        kept = q4.recover_pending(d, H(), Rn(), None, None, None, "codex", "tar", lambda **k: None)
        self.assertTrue((kept / "vm-out.tgz").exists())
        self.assertEqual(_json.loads((kept / "attempt.json").read_text())["status"], "interrupted-recovered")
        self.assertFalse((d / "pending.json").exists())

    def test_journal_without_entries_is_empty(self):
        class H:
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=0, stdout="-- No entries --\n" if "journalctl" in cmd else "x\n", stderr="")
        problems = q4.Runner(H(), None).telemetry("ip", Path(_tempfile.mkdtemp()), 1)
        self.assertEqual(problems, ["telemetry journal.txt: empty"])
