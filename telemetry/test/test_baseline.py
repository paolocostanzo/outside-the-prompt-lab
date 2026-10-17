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


class OverlappingQuestions(unittest.TestCase):
    """Claude Code asks "Do you want to proceed?" both for a command and for an MCP tool; only the tool question may get the
    frozen Q3 approval (option 2, "don't ask again"), every command gets "allow once"."""
    def setUp(self):
        saved = {n: getattr(bs.q3, n) for n in ("keys",)}
        self.addCleanup(lambda: [setattr(bs.q3, n, f) for n, f in saved.items()])
        self.sent = []
        bs.q3.keys = lambda *k: self.sent.append(k)
        bs.q3.load_overrides(SCRIPTS.parent.parent / "tool-change/scripts/q3-clients.json")
        out = Path(tempfile.mkdtemp()); (out / "screens").mkdir()
        self.s = bs.Session("claude-code", "dev", out, CFG["tasks"], PERMS)

    def test_command_question_is_answered_once(self):
        screen = ("Bash command\n\n  python3 -m unittest -q\n  Run the tests\n\nDo you want to proceed?\n"
                  " ❯ 1. Yes\n   2. Yes, and don't ask again for python3 commands in /home/lab/q3-repo\n   3. No")
        self.assertEqual(self.s.answer_questions(screen, 1, CFG["tasks"][1]), "allow-once")
        self.assertEqual(self.sent[-1], ("Enter",), "option 1, never option 2")

    def test_lab_tool_question_gets_the_frozen_approval(self):
        screen = ("Tool use\n\n  q3-lab - q3_noop() (MCP)\n\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again for q3-lab - q3_noop\n   3. No")
        self.assertEqual(self.s.answer_questions(screen, 1, CFG["tasks"][3]), "mcp-approval")
        self.assertEqual(self.sent[-1], ("2",))

    def test_old_lab_tool_text_above_does_not_count(self):
        screen = "earlier: q3_noop returned ok\n" + "\n".join(f"line {i}" for i in range(40)) + \
                 "\nBash command\n  python3 -m unittest -q\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again"
        self.assertEqual(self.s.answer_questions(screen, 2, CFG["tasks"][1]), "allow-once")


class Quota(unittest.TestCase):
    def setUp(self):
        out = Path(tempfile.mkdtemp()); (out / "screens").mkdir()
        self.s = bs.Session("codex", "dev", out, CFG["tasks"], PERMS)
        saved = bs.q3.screen
        self.addCleanup(lambda: setattr(bs.q3, "screen", saved))
        bs.q3.screen = lambda: "x"

    def test_messages_are_recognised(self):
        for client, text in [("codex", "■ You've hit your usage limit. Upgrade or try again at 9:41 PM."),
                             ("claude-code", "Claude usage limit reached. Your limit will reset at 7pm"),
                             ("gemini", "API Error: [429] Quota exceeded for metric generate_content_free_tier_requests"),
                             ("qwen", "RESOURCE_EXHAUSTED"), ("goose", "Request failed: HTTP 429 Too Many Requests")]:
            self.assertIsNotNone(bs.quota.find(client, text), text)

    def test_ordinary_text_is_not_a_quota_message(self):
        for text in ["greet.py returns a greeting for the given name.", "Ran 1 test in 0.001s\n\nOK", "line 429 of the log",
                     "the function has a limit on the name length", "# reviewed in cycle 4"]:
            self.assertIsNone(bs.quota.find("codex", text), text)

    def test_session_stops_and_records_the_message(self):
        self.assertTrue(self.s.quota_hit("You've hit your usage limit", 3, "edit"))
        self.assertEqual(self.s.quota_message, "You've hit your usage limit")
        lines = [json.loads(l) for l in (self.s.out / "timeline.jsonl").read_text().splitlines()]
        self.assertEqual(lines[-1]["action"], "quota")


class DialogDetection(OverlappingQuestions):
    def test_recent_tool_output_above_a_command_dialog(self):
        screen = ("⏺ q3-lab - q3_noop (MCP)\n  ⎿  ok\n\n⏺ ok\n\n> Run the tests\n\nBash command\n\n  python3 -m unittest -q\n"
                  "  Run the tests\n\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again for python3 commands\n   3. No")
        self.assertEqual(self.s.answer_questions(screen, 2, CFG["tasks"][1]), "allow-once")
        self.assertEqual(self.sent[-1], ("Enter",))

    def test_lab_tool_name_inside_a_command(self):
        screen = "Bash command\n\n  grep -n q3_noop greet.py\n\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again"
        self.assertEqual(self.s.answer_questions(screen, 2, CFG["tasks"][1]), "allow-once")


class QuotaAtCycleEdges(unittest.TestCase):
    def test_quota_next_to_the_ready_marker_invalidates(self):
        out = Path(tempfile.mkdtemp()); (out / "screens").mkdir()
        bs.q3.load_overrides(SCRIPTS.parent.parent / "tool-change/scripts/q3-clients.json")
        s = bs.Session("codex", "dev", out, CFG["tasks"], PERMS)
        saved = {n: getattr(bs.q3, n) for n in ("launch", "wait_ready", "screen", "kill")}
        saved_sleep = bs.time.sleep
        self.addCleanup(lambda: ([setattr(bs.q3, n, f) for n, f in saved.items()], setattr(bs.time, "sleep", saved_sleep)))
        bs.q3.launch = lambda cmd: None
        bs.q3.wait_ready = lambda *a, **k: True
        bs.q3.screen = lambda: "■ You've hit your usage limit.\n› Ask Codex to do anything"
        bs.q3.kill = lambda: None
        bs.time.sleep = lambda x: None
        cycles, prompted, done = s.run(0.05, CFG)
        self.assertEqual(cycles, 1, "the session ends at the first quota message")
        self.assertIsNotNone(s.quota_message)


class PositiveMcpIdentification(OverlappingQuestions):
    def test_long_command_pushes_its_heading_out_of_the_dialog_window(self):
        body = "\n".join(f"  echo step {i}" for i in range(14))
        screen = f"Bash command\n\n{body}\n  grep q3_noop greet.py\n\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again\n   3. No"
        self.assertEqual(self.s.answer_questions(screen, 3, CFG["tasks"][1]), "allow-once")
        self.assertEqual(self.sent[-1], ("Enter",))

    def test_lab_tool_without_mcp_marker_is_not_trusted(self):
        screen = "Something about q3_noop\nDo you want to proceed?\n ❯ 1. Yes\n   2. Yes, and don't ask again"
        self.assertEqual(self.s.answer_questions(screen, 3, CFG["tasks"][3]), "allow-once")


class FullPaneCaptures(unittest.TestCase):
    """tmux captures the whole 50-line pane: the question can sit at line 20-24 with blank lines below (setup captures of
    15 Oct 2026, Gemini CLI and Cursor CLI). Synthetic replicas of those layouts."""
    def setUp(self):
        saved = bs.q3.keys
        self.addCleanup(lambda: setattr(bs.q3, "keys", saved))
        self.sent = []
        bs.q3.keys = lambda *k: self.sent.append(k)
        bs.q3.load_overrides(SCRIPTS.parent.parent / "tool-change/scripts/q3-clients.json")

    def session(self, client):
        out = Path(tempfile.mkdtemp()); (out / "screens").mkdir()
        return bs.Session(client, "dev", out, CFG["tasks"], PERMS)

    def test_gemini_question_above_blank_lines(self):
        head = ["", "", "", "", "", "", "", " > Call the q3_noop tool of the q3-lab MCP server once.", "", "",
                "  Calling q3_noop.", "", "", "", "", "", "│ ?  q3_noop (q3-lab MCP Server)", "│", "│ MCP Server: q3-lab",
                "│ Tool: q3_noop", "│", "│ MCP Tool Details:", "│ (press Ctrl+O to expand MCP tool details)",
                '│ Allow execution of MCP tool "q3_noop" from server "q3-lab"?', "│", "│ ● 1. Allow once", "│   2. Allow tool for this session"]
        screen = "\n".join(head + [""] * (50 - len(head)))
        self.assertEqual(self.session("gemini").answer_questions(screen, 1, CFG["tasks"][3]), "mcp-approval")
        self.assertEqual(self.sent[-1], ("2", "Enter"))

    def test_cursor_question_above_blank_lines(self):
        head = [""] * 7 + ["  Call the q3_noop tool of the q3-lab MCP server once.", "", "", "  I'll call q3_noop.", "",
                "    Explored available MCP tools q3-lab · q3_noop", "", "    q3-lab q3_noop", "", "", " q3-lab: q3_noop", "",
                " Run this MCP tool?", "", "    Allowlist MCP Tool (tab)", "    Run (y)", "    Skip (n)"]
        screen = "\n".join(head + [""] * (50 - len(head)))
        self.assertEqual(self.session("cursor-agent").answer_questions(screen, 1, CFG["tasks"][3]), "mcp-approval")
        self.assertEqual(self.sent[-1], ("Tab",))
