"""q4_baseline.py: plan, commands and the holdout gap (D13 point 2, D24 point 4). No VM. Run: python3 -m unittest discover -s telemetry/test"""
import importlib.util, json, tempfile, time, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("q4_baseline", SCRIPTS / "q4_baseline.py")
qb = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qb)
qb.ev.STATE = Path(tempfile.mkdtemp())  # never the real ~/.agentlab-q4 of the host


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
        self.assertEqual(c, qb.ev.watched("python3 ~/lab/telemetry/scripts/baseline_session.py --client gemini --part holdout "
                                         "--minutes 60 --out ~/q4-out", "gemini", "q3run"))
        self.assertIn("quota_watch.py --client gemini --session q3run", c)

    def test_holdout_waits_for_the_gap(self):
        out = Path(tempfile.mkdtemp())
        (out / "baseline__codex__dev").mkdir()
        (out / "baseline__codex__dev" / "run.json").write_text(json.dumps({"t1": time.time() - 3600}))  # complete record
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


import io as _io, tarfile as _tarfile


def _tgz(files):
    buf = _io.BytesIO()
    with _tarfile.open(fileobj=buf, mode="w:gz") as tar:
        for name, data in files.items():
            info = _tarfile.TarInfo(name); info.size = len(data)
            tar.addfile(info, _io.BytesIO(data))
    return buf.getvalue()


class BaselineOutputs(unittest.TestCase):
    S = {"client": "codex", "part": "dev", "name": "baseline__codex__dev"}

    def files(self, session):
        b = "q4-out/baseline__codex__dev/"
        return {b + "session.json": json.dumps(session).encode(), b + "timeline.jsonl": b"", "q3-server.log": b"",
                "q4-out/quota-watch.jsonl": b'{"ts": 1, "event": "started"}\n{"ts": 5, "event": "heartbeat"}\n{"ts": 9, "event": "stopped"}\n',
                "q4-out/command-bounds.json": b'{"start": 2, "end": 8, "rc": 0, "observer_rc": 0}'}

    def test_valid_session_passes_and_invalid_is_not_counted(self):
        good = {"valid": True, "workload": {"ok": True}}
        sess, problems = qb.check_outputs(self.S, _tgz(self.files(good)))
        self.assertEqual(problems, [])
        _, problems = qb.check_outputs(self.S, _tgz(self.files({"valid": False, "workload": {"ok": False}})))
        self.assertTrue(problems)
        f = self.files(good); f.pop("q3-server.log")
        self.assertTrue(qb.check_outputs(self.S, _tgz(f))[1])

    def test_local_parts_do_not_exist(self):
        with self.assertRaises(SystemExit):
            qb.plan(1, parts=("local-dev", "local-holdout"))

    def test_holdout_without_a_valid_dev_session_stops(self):
        out = Path(tempfile.mkdtemp())
        with self.assertRaises(SystemExit):
            qb.wait_for_gap(out, {"client": "qwen", "part": "holdout", "name": "x"}, 6, print, lambda s: None)


class QuotaStops(BaselineOutputs):
    def test_quota_session_is_not_counted(self):
        _, problems = qb.check_outputs(self.S, _tgz(self.files({"valid": False, "quota_exhausted": True,
                                                                 "quota_message": "usage limit", "workload": {"ok": True}})))
        self.assertTrue(any("quota" in p for p in problems))


class ObserverAndSetup(BaselineOutputs):
    def test_observer_record_is_required_and_read(self):
        f = self.files({"valid": True, "workload": {"ok": True}})
        f.pop("q4-out/quota-watch.jsonl")
        self.assertTrue(any("did not run" in p for p in qb.check_outputs(self.S, _tgz(f))[1]))
        f = self.files({"valid": True, "workload": {"ok": True}})
        f["q4-out/quota-watch.jsonl"] = b'{"ts": 1, "event": "started"}\n{"ts": 2, "event": "quota", "message": "rate limit"}\n{"ts": 9, "event": "stopped"}\n'
        self.assertTrue(any("observer" in p for p in qb.check_outputs(self.S, _tgz(f))[1]))

    def test_setup_goes_on_only_for_workload_problems(self):
        self.assertTrue(qb.setup_can_continue("setup", ["session not valid: workload ..."]))
        self.assertFalse(qb.setup_can_continue("setup", ["session not valid: x", "quota or rate limit reached (observer): 'x'"]))
        self.assertFalse(qb.setup_can_continue("dev", ["session not valid: workload ..."]), "never outside the set-up")
        self.assertFalse(qb.setup_can_continue("setup", []))
