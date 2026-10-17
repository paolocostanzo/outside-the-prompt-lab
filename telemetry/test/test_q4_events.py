"""q4_events.py: the plan and the commands (D24 point 3). No VM is touched. Run: python3 -m unittest discover -s telemetry/test"""
import collections, importlib.util, os, subprocess, sys, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("q4_events", SCRIPTS / "q4_events.py")
q4 = importlib.util.module_from_spec(spec)
spec.loader.exec_module(q4)
import tempfile as _tmpstate
q4.STATE = Path(_tmpstate.mkdtemp())  # never the real ~/.agentlab-q4 of the host
import hashlib as _hl, secrets as _sec
_FULL_FPS = [{"kind": k, "source": "x", "length": 48, "prefix": "abcd", "sha256": _hl.sha256(_sec.token_bytes(16)).hexdigest()}
             for k in q4.sg.REQUIRED_KINDS]  # a complete fingerprint set of random values (D26: the gate needs every kind)


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
        self.assertEqual(rn.telemetry("ip", d, 100), ([], True))
        self.assertEqual(sorted(_json.loads((d / "telemetry/status.json").read_text())), sorted(n for n, _, _ in q4.TELEMETRY))

    def test_failed_or_empty_telemetry_is_a_problem(self):
        rn, d = self.runner({"audit.log": (1, "", "sudo: a password is required"), "journalctl": (0, "", "")})
        problems, copied = rn.telemetry("ip", d, 100)
        self.assertEqual(len(problems), 2, problems)
        self.assertFalse(copied, "the audit copy failed")
        self.assertIn("password", (d / "telemetry/audit.log.stderr").read_text())
        rn, d = self.runner({"nft list": (0, "", "")})
        self.assertEqual(rn.telemetry("ip", d, 100), ([], True), "an empty nft ruleset is allowed; audit and journal are not")

    def test_quota_in_run_captures(self):
        qm = q4.load(SCRIPTS / "quota.py", "quota")
        started = {"q4-out/quota-watch.jsonl": b'{"ts": 1, "event": "started"}\n{"ts": 5, "event": "heartbeat"}\n{"ts": 9, "event": "stopped"}\n',
                "q4-out/command-bounds.json": b'{"start": 2, "end": 8, "rc": 0, "observer_rc": 0}'}
        tgz = _tgz({**started, "q4-out/codex__none__description__r1/codex__none__r1__03-p2-end.txt": b"You've hit your usage limit."})
        self.assertIn("usage limit", q4.quota_in_outputs("codex", tgz, qm))
        self.assertIsNone(q4.quota_in_outputs("codex", _tgz({**started, "q4-out/x/a.txt": b"ok"}), qm))
        self.assertIn("did not run", q4.quota_in_outputs("codex", _tgz({"q4-out/x/a.txt": b"ok"}), qm))
        seen = {"q4-out/quota-watch.jsonl": b'{"ts": 1, "event": "started"}\n{"ts": 2, "event": "quota", "message": "rate limit"}\n{"ts": 9, "event": "stopped"}\n',
                "q4-out/command-bounds.json": b'{"start": 1.5, "end": 8, "rc": 0, "observer_rc": 0}'}
        self.assertIn("(observer): 'rate limit'", q4.quota_in_outputs("codex", _tgz({**seen, "q4-out/x/a.txt": b"ok"}), qm),
                      "a message the client recovered from still counts")

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
        problems, copied = q4.Runner(H(), None).telemetry("ip", d, 1)
        self.assertTrue(any("audit.log" in p and "124" in p for p in problems), problems)
        self.assertFalse(copied)
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
            def ssh(self, ip, cmd, timeout=120):
                if "secret_gate.py fingerprints" in cmd:
                    return _NS(returncode=0, stdout=_json.dumps({"fingerprints": _FULL_FPS, "unreadable": []}), stderr="")
                return _NS(returncode=0, stdout="x\n", stderr="")
        class Rn:
            def client_logs(self, *a): return {"export": "ok", "collect_rc": 0}
            def ssh_bin(self, ip, cmd, dest):  # a real (empty) archive: an unreadable one would stop the secret gate
                import tarfile as _tf
                with _tf.open(dest, "w:gz"):
                    pass
                return 0, ""
            def telemetry(self, ip, d, since): return [], True
        kept = q4.recover_pending(d, H(), Rn(), None, None, None, "codex", "tar", lambda **k: None)
        self.assertTrue((kept / "vm-out.tgz").exists())
        self.assertEqual(_json.loads((kept / "attempt.json").read_text())["status"], "interrupted-recovered")
        self.assertFalse((d / "pending.json").exists())

    def test_recovered_attempt_with_a_secret_is_quarantined_and_stops(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        leaked = "AI" + "za" + "Q" * 35  # assembled at run time: the test file itself stays clean
        class H:
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120):
                if "secret_gate.py fingerprints" in cmd:
                    return _NS(returncode=0, stdout=_json.dumps({"fingerprints": _FULL_FPS, "unreadable": []}), stderr="")
                return _NS(returncode=0, stdout="x\n", stderr="")
        class Rn:
            def client_logs(self, *a): return {"export": "ok", "collect_rc": 0}
            def ssh_bin(self, ip, cmd, dest): Path(dest).write_text("log " + leaked); return 0, ""
            def telemetry(self, ip, d, since): return [], True
        notes = []
        with self.assertRaises(SystemExit) as cm:
            q4.recover_pending(d, H(), Rn(), None, None, None, "codex", "tar", lambda **k: notes.append(k))
        self.assertEqual(cm.exception.code, 9)
        att = d / "attempts" / "1"
        self.assertEqual(_json.loads((att / "attempt.json").read_text())["status"], "secret-found")
        self.assertEqual(notes[-1]["event"], "abort-secret")
        self.assertNotIn(leaked, _json.dumps(notes) + (att / "attempt.json").read_text())

    def test_journal_without_entries_is_empty(self):
        class H:
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=0, stdout="-- No entries --\n" if "journalctl" in cmd else "x\n", stderr="")
        problems, copied = q4.Runner(H(), None).telemetry("ip", Path(_tempfile.mkdtemp()), 1)
        self.assertEqual(problems, ["telemetry journal.txt: empty"])
        self.assertTrue(copied, "copied, but empty: safe to restore, not usable")


class InspectionRound3(unittest.TestCase):
    def test_failed_copy_during_recovery_keeps_the_obligation(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        class H:
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120): return _NS(returncode=0, stdout="x\n", stderr="")
        class Rn:
            def client_logs(self, *a): return {"export": "ok", "collect_rc": 0}
            def ssh_bin(self, ip, cmd, dest): return 255, "connection reset"
            def telemetry(self, ip, d, since): return [], True
        with self.assertRaises(SystemExit) as e:
            q4.recover_pending(d, H(), Rn(), None, None, None, "codex", "tar", lambda **k: None)
        self.assertEqual(e.exception.code, 7)
        self.assertTrue((d / "pending.json").exists(), "the next invocation must try the copy again before any restore")
        self.assertFalse((d / "attempts").exists())

    def test_writer_that_survives_recovery_stops_it(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        class H:
            def ip(self): return "1.2.3.4"
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=1 if "stop_clients" in cmd else 0, stdout="still running: 42", stderr="")
        with self.assertRaises(SystemExit) as e:
            q4.recover_pending(d, H(), None, None, None, None, "codex", "tar", lambda **k: None)
        self.assertEqual(e.exception.code, 7)
        self.assertTrue((d / "pending.json").exists())


class InspectionRound4(unittest.TestCase):
    def setUp(self):
        q4.STATE = Path(_tempfile.mkdtemp())

    def test_vm_wide_pending_blocks_another_folder(self):
        a, b = Path(_tempfile.mkdtemp()) / "events-run", Path(_tempfile.mkdtemp()) / "baseline-session"
        a.mkdir(); b.mkdir()
        q4.mark_pending(a, run="x", t0=1)
        notes = []
        with self.assertRaises(SystemExit) as e:
            q4.guard_vm(b, lambda **k: notes.append(k))
        self.assertEqual(e.exception.code, 7)
        q4.guard_vm(a, print)  # the folder that owns the attempt may proceed to its recovery

    def test_stale_vm_record_is_cleared_once_the_folder_kept_its_attempt(self):
        a, b = Path(_tempfile.mkdtemp()) / "r1", Path(_tempfile.mkdtemp()) / "r2"
        a.mkdir(); b.mkdir()
        q4.mark_pending(a, run="x", t0=1)
        q4.keep_attempt(a, "not-usable", {})
        self.assertFalse((q4.STATE / "pending.json").exists())
        q4.guard_vm(b, print)

    def test_lock_is_exclusive(self):
        fh = q4.vm_lock(print)
        r = subprocess.run([sys.executable, "-c", f"import fcntl; f=open({str(q4.STATE / 'vm.lock')!r},'w');"
                            "import sys\ntry:\n fcntl.flock(f, fcntl.LOCK_EX|fcntl.LOCK_NB); print('got')\nexcept BlockingIOError: print('busy')"],
                           capture_output=True, text=True)
        self.assertEqual(r.stdout.strip(), "busy")
        fh.close()

    def test_malformed_completion_record_goes_through_recovery(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        (d / "run.json").write_text('{"rep": 1, "t0"')
        self.assertFalse(q4.completed(d))
        self.assertTrue(list(d.glob("run.json.malformed-*")))
        q4.write_json_atomic(d / "run.json", {"t1": 5})
        self.assertTrue(q4.completed(d))
        self.assertFalse((d / "run.json.tmp").exists())


class InspectionRound5(unittest.TestCase):
    def setUp(self):
        q4.STATE = Path(_tempfile.mkdtemp())

    def test_completed_run_with_a_leftover_pending_record_is_reconciled(self):
        d = Path(_tempfile.mkdtemp()) / "run"; d.mkdir()
        q4.mark_pending(d, run="x", t0=1)
        q4.write_json_atomic(d / "run.json", {"t1": 9})  # interrupted right here, before clear_pending
        self.assertTrue(q4.completed(d))
        q4.clear_pending(d)
        self.assertFalse((d / "pending.json").exists())
        self.assertFalse((q4.STATE / "pending.json").exists())
        other = Path(_tempfile.mkdtemp()) / "next"; other.mkdir()
        q4.guard_vm(other, print)  # the next run is not blocked


class QuotaObserver(unittest.TestCase):
    def test_observer_records_a_transient_message(self):
        w = q4.load(SCRIPTS / "quota_watch.py", "quota_watch")
        screens = iter([(True, "working", None), (True, "API Error: Quota exceeded for metric", None), (False, "", None),
                        (True, "done", None)])
        out = Path(_tempfile.mkdtemp()) / "qw.jsonl"
        w.watch("gemini", "q3run", out, interval=0, rounds=4, read=lambda s: next(screens), sleep=lambda x: None)
        recs = [_json.loads(l) for l in out.read_text().splitlines()]
        self.assertEqual([r["event"] for r in recs], ["started", "quota", "stopped"])
        self.assertEqual((recs[-1]["captures"], recs[-1]["absent"]), (3, 1), "a missing session between restarts is not an error")

    def test_observer_health_is_required(self):
        P = q4.observer_problems
        B = '{"start": 2, "end": 14, "rc": 0, "observer_rc": 0}'
        self.assertEqual(P('{"ts": 1, "event": "started"}\n{"ts": 11, "event": "heartbeat"}\n{"ts": 15, "event": "stopped"}\n', B), [])
        early = '{"ts": 1, "event": "started"}\n{"ts": 5, "event": "stopped"}\n'
        self.assertTrue(any("before the command ended" in p for p in P(early, B)), "an early SIGTERM")
        self.assertTrue(any("failed" in p for p in P('{"ts": 1, "event": "started"}\n{"ts": 3, "event": "failed", "error": "OSError"}\n', B)))
        self.assertTrue(any("no command bounds" in p for p in P('{"ts": 1, "event": "started"}\n{"ts": 15, "event": "stopped"}\n')))
        self.assertTrue(any("exit status" in p for p in
                            P('{"ts": 1, "event": "started"}\n{"ts": 15, "event": "stopped"}\n', '{"start": 2, "end": 14, "rc": 0, "observer_rc": 1}')))
        self.assertTrue(any("orderly end" in p for p in P('{"ts": 1, "event": "started"}\n{"ts": 11, "event": "heartbeat"}\n')),
                        "an observer killed part-way")
        self.assertTrue(any("gap" in p for p in P('{"ts": 1, "event": "started"}\n{"ts": 200, "event": "stopped"}\n')))
        self.assertTrue(any("capture error" in p for p in
                            P('{"ts": 1, "event": "started"}\n{"ts": 2, "event": "capture-error", "error": "x"}\n{"ts": 3, "event": "stopped"}\n')))
        self.assertEqual(P(""), ["quota observer: did not start"])

    def test_heartbeats_and_orderly_end(self):
        w = q4.load(SCRIPTS / "quota_watch.py", "quota_watch")
        clock = iter(range(0, 1000, 4))
        out = Path(_tempfile.mkdtemp()) / "qw.jsonl"
        w.watch("codex", "q3run", out, interval=0, rounds=10, read=lambda s: (True, "ok", None), clock=lambda: next(clock),
                sleep=lambda x: None)
        recs = [_json.loads(l) for l in out.read_text().splitlines()]
        self.assertIn("heartbeat", [r["event"] for r in recs])
        self.assertEqual(q4.observer_problems(out.read_text(), '{"start": 1, "end": 30, "rc": 0, "observer_rc": 0}'), [])

    def test_cell_commands_run_the_observer_on_the_right_session(self):
        self.assertIn("--session q5run", q4.cell_command({"client": "codex", "event": "q5-start", "rep": 1}))
        c = q4.cell_command({"client": "codex", "event": "q3-silent", "rep": 1})
        self.assertIn("--session q3run", c)
        self.assertTrue(c.endswith("exit $rc"), "the cell's own exit code is kept")


class WrapperEndToEnd(unittest.TestCase):
    def test_watched_command_in_a_shell(self):
        """The real wrapper and observer, in a temporary home, around a harmless command; the observer only reads tmux
        (has-session / capture-pane) on a session that does not exist. Nothing is stopped or killed except the observer."""
        import shutil as _sh
        if not (_sh.which("bash") and _sh.which("tmux")):
            self.skipTest("needs bash and tmux")
        home = Path(_tempfile.mkdtemp())
        (home / "lab").mkdir(); (home / "q4-out").mkdir()
        (home / "lab" / "telemetry").symlink_to(SCRIPTS.parent)
        cmd = q4.watched("sleep 2; exit 3", "codex", "q4-test-no-such-session")
        r = subprocess.run(["bash", "-c", cmd], env={**os.environ, "HOME": str(home)}, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 3, r.stderr)
        bounds = (home / "q4-out/command-bounds.json").read_text()
        self.assertEqual(_json.loads(bounds)["observer_rc"], 0, bounds)
        self.assertEqual(q4.observer_problems((home / "q4-out/quota-watch.jsonl").read_text(), bounds), [])
