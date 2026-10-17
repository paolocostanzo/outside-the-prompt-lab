"""baseline_session.py without a VM: question answering, task completion, session validity (D24 point 4).
Run: python3 -m unittest discover -s telemetry/test"""
import importlib.util, json, subprocess, sys, tempfile, unittest
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
spec = importlib.util.spec_from_file_location("baseline_session", SCRIPTS / "baseline_session.py")
bs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bs)
PERMS = json.loads((SCRIPTS.parent / "baseline/clients.json").read_text())
CFG = json.loads((SCRIPTS.parent / "baseline/tasks.json").read_text())


class FakeTmux:
    """Replaces the tmux helpers of run_q3_cell with a scripted sequence of screens."""
    def __init__(self, screens):
        self.screens, self.sent = list(screens), []
        bs.q3.screen = lambda: self.screens[0] if len(self.screens) == 1 else self.screens.pop(0)
        bs.q3.keys = lambda *k: self.sent.append(k)
        bs.q3.type_text = lambda text: self.sent.append(("TYPE", text))
        bs.q3.answer_noise = lambda s: False
        bs.time.sleep = lambda s: None


class Baseline(unittest.TestCase):
    def setUp(self):
        self.out = Path(tempfile.mkdtemp())
        (self.out / "screens").mkdir()
        # FakeTmux and the clock below patch shared modules: restore them after every test
        saved_q3 = {n: getattr(bs.q3, n) for n in ("screen", "keys", "type_text", "answer_noise")}
        saved_time = (bs.time.time, bs.time.sleep)
        self.addCleanup(lambda: [setattr(bs.q3, n, f) for n, f in saved_q3.items()])
        self.addCleanup(lambda: (setattr(bs.time, "time", saved_time[0]), setattr(bs.time, "sleep", saved_time[1])))

    def session(self, client):
        bs.q3.load_overrides(SCRIPTS.parent.parent / "tool-change/scripts/q3-clients.json")
        return bs.Session(client, "dev", self.out, CFG["tasks"], PERMS)

    def test_allow_once_and_mcp_approval_use_the_fixed_keys(self):
        s = self.session("codex")
        fake = FakeTmux(["x"])
        self.assertEqual(s.answer_questions("Would you like to run the following command?\n 1. Yes", 1, CFG["tasks"][1]), "allow-once")
        self.assertEqual(fake.sent[-1], ("Enter",))
        self.assertEqual(s.answer_questions("Allow the q3-lab MCP server to run tool \"q3_noop\"?", 1, CFG["tasks"][3]), "mcp-approval")
        self.assertEqual(fake.sent[-1], ("3", "Enter"))
        self.assertIsNone(s.answer_questions("greet.py returns a greeting.\n› Ask Codex to do anything", 1, CFG["tasks"][0]))

    def test_generic_question_only_at_the_bottom_of_the_screen(self):
        s = self.session("goose")
        FakeTmux(["x"])
        old = "Do you want to see more?\n" + "\n".join(f"line {i}" for i in range(30))
        self.assertIsNone(s.answer_questions(old, 1, CFG["tasks"][0]))
        self.assertEqual(s.answer_questions("output\nProceed? (y/n)", 1, CFG["tasks"][0]), "unexpected-question")

    def test_task_done_when_screen_is_stable_and_ready(self):
        s = self.session("codex")
        s.evidence = lambda task, cycle, t, c: True
        ready = "greet.py defines greet().\n› Ask Codex to do anything"
        fake = FakeTmux(["working...", "working...", ready])
        clock = iter(range(0, 1000, 5))
        bs.time.time = lambda: next(clock)
        self.assertTrue(s.do_task(3, CFG["tasks"][2], timeout=240, idle_s=8))
        self.assertIn("cycle 3", fake.sent[0][1], "{k} is replaced by the cycle number")
        lines = [json.loads(l) for l in (self.out / "timeline.jsonl").read_text().splitlines()]
        self.assertEqual([l["action"] for l in lines], ["prompt", "done"])

    def test_validity(self):
        ok = [{"event": "out", "why": "tools/list", "state": "A"}, {"event": "tools/call", "state": "A"}]
        self.assertEqual(bs.validity(ok), (["A"], False))
        bad = ok + [{"event": "definition-changed", "state": "B"}, {"event": "out", "why": "tools/list", "state": "B"}]
        self.assertEqual(bs.validity(bad), (["A", "B"], True))


if __name__ == "__main__":
    unittest.main()


class Workload(unittest.TestCase):
    CRIT = {"min_done_share": 0.8, "min_known_server_calls_per_cycle": 0.8}

    def test_thresholds(self):
        self.assertTrue(bs.workload(10, 40, 32, 8, self.CRIT)["ok"])
        self.assertFalse(bs.workload(10, 40, 31, 8, self.CRIT)["ok"], "too few tasks completed")
        self.assertFalse(bs.workload(10, 40, 40, 7, self.CRIT)["ok"], "too few calls to the known server")
        self.assertFalse(bs.workload(0, 0, 0, 0, self.CRIT)["ok"], "a session with no use is not valid")


class Evidence(unittest.TestCase):
    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.saved = (bs.q3.REPO, bs.q3.events)
        bs.q3.REPO = self.repo
        self.addCleanup(lambda: (setattr(bs.q3, "REPO", self.saved[0]), setattr(bs.q3, "events", self.saved[1])))
        out = Path(tempfile.mkdtemp()); (out / "screens").mkdir()
        self.s = bs.Session("codex", "dev", out, CFG["tasks"], PERMS)
        self.task = {t["id"]: t for t in CFG["tasks"]}

    def test_edit_needs_the_line_in_the_file(self):
        (self.repo / "greet.py").write_text("def greet(n):\n    return n\n")
        self.assertFalse(self.s.evidence(self.task["edit"], 3, 0, 0), "a refused edit leaves the file as it was")
        (self.repo / "greet.py").write_text("def greet(n):\n    return n\n# reviewed in cycle 3\n")
        self.assertTrue(self.s.evidence(self.task["edit"], 3, 0, 0))
        self.assertFalse(self.s.evidence(self.task["edit"], 4, 0, 0))

    def test_tests_need_a_run_after_the_prompt(self):
        self.assertFalse(self.s.evidence(self.task["test"], 1, 100.0, 0))
        (self.repo / ".q4-test-runs").write_text("50.0\n")
        self.assertFalse(self.s.evidence(self.task["test"], 1, 100.0, 0), "an older run does not count")
        (self.repo / ".q4-test-runs").write_text("50.0\n100.5\n")
        self.assertTrue(self.s.evidence(self.task["test"], 1, 100.0, 0))

    def test_known_server_needs_a_new_call_of_this_session(self):
        bs.q3.events = lambda: [{"event": "tools/call", "cell": "baseline-codex-dev"}, {"event": "tools/call", "cell": "other"}]
        self.assertEqual(self.s.server_calls(), 1)
        self.assertFalse(self.s.evidence(self.task["known-server"], 1, 0, 1))
        self.assertTrue(self.s.evidence(self.task["known-server"], 1, 0, 0))

    def test_instrumented_test_file_writes_its_marker(self):
        files = CFG["setup_files"]
        (self.repo / "greet.py").write_text('def greet(name):\n    return f"hello, {name}"\n')
        (self.repo / "test_greet.py").write_text(files["test_greet.py"])
        r = subprocess.run([sys.executable, "-m", "unittest", "-q"], cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue((self.repo / ".q4-test-runs").read_text().strip())
