"""vm_logs.py and collection_check.py on a fake home (D24 points 1-2). Run: python3 -m unittest discover -s telemetry/test"""
import importlib.util, io, json, os, subprocess, sys, tarfile, tempfile, time, unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPTS = HERE.parent / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


cc = load("collection_check")
CANDIDATES = {"_note": "x", "codex": ["~/.codex/sessions/**/*.jsonl", "~/.codex/log/**"], "gemini": ["~/.gemini/tmp/**/logs.json"],
              "goose": ["~/.local/state/goose/logs/**"]}


def run_vm(home, *args):
    env = dict(os.environ, HOME=str(home))
    cand = home / "candidates.json"
    cand.write_text(json.dumps(CANDIDATES))
    return subprocess.run([sys.executable, "-I", str(SCRIPTS / "vm_logs.py"), args[0], str(cand), *args[1:]], env=env,
                          capture_output=True, check=True).stdout


class Collection(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        old = self.home / ".codex/log/codex-tui.log"
        old.parent.mkdir(parents=True)
        old.write_text("old line\n")
        os.utime(old, (1000, 1000))
        new = self.home / ".codex/sessions/2026/10/17/rollout-x.jsonl"
        new.parent.mkdir(parents=True)
        new.write_text('{"type":"tool_call"}\n')
        self.start, self.end = int(time.time()) - 60, int(time.time()) + 1

    def test_inventory_lists_only_existing_files(self):
        inv = json.loads(run_vm(self.home, "inventory"))
        self.assertEqual(sorted(f["path"] for f in inv["clients"]["codex"]["files"]),
                         [".codex/log/codex-tui.log", ".codex/sessions/2026/10/17/rollout-x.jsonl"])
        self.assertEqual(inv["clients"]["gemini"]["files"], [])
        self.assertNotIn("_note", inv["clients"])

    def test_collect_and_check_ok(self):
        arc = self.home / "s.tgz"
        arc.write_bytes(run_vm(self.home, "collect", str(self.start), str(self.end)))
        inv = json.loads(run_vm(self.home, "inventory"))
        r = cc.check(str(arc), "codex", self.start, self.end, event_time=self.start + 10, inventory=inv)
        self.assertEqual(r["export"], "ok")
        self.assertEqual(r["client_logs"], "wrote")
        self.assertEqual(r["files_written_in_session"], 1, "the old log was not modified in the session")
        self.assertTrue(r["coverage"]["after_event"])

    def test_negative_observation_and_no_default_logs_are_distinguished(self):
        arc = self.home / "s.tgz"
        arc.write_bytes(run_vm(self.home, "collect", str(self.start), str(self.end)))
        inv = json.loads(run_vm(self.home, "inventory"))
        # gemini: no candidate location exists at all -> no-default-logs; codex outside the window -> wrote-nothing-in-session
        self.assertEqual(cc.check(str(arc), "gemini", self.start, self.end, inventory=inv)["client_logs"], "no-default-logs")
        later = cc.check(str(arc), "codex", self.end + 3600, self.end + 7200, inventory=inv)
        self.assertEqual(later["export"], "ok")
        self.assertEqual(later["client_logs"], "wrote-nothing-in-session", "a negative observation, not an export failure")
        quiet = cc.check(str(self.home / "s.tgz"), "goose", self.start, self.end, inventory=inv)
        self.assertEqual(quiet["client_logs"], "no-default-logs")

    def test_failed_export_is_detected(self):
        bad = self.home / "bad.tgz"
        bad.write_bytes(b"not a tar")
        self.assertEqual(cc.check(str(bad), "codex", self.start, self.end)["export"], "failed")
        # manifest lists a file that is not in the archive
        buf = io.BytesIO()
        with tarfile.open(fileobj=buf, mode="w:gz") as tar:
            data = json.dumps({"clients": {"codex": [{"path": ".codex/x.jsonl", "size": 1, "mtime": 1, "sha256": "0" * 64}]}}).encode()
            info = tarfile.TarInfo("manifest.json"); info.size = len(data)
            tar.addfile(info, io.BytesIO(data))
        miss = self.home / "miss.tgz"
        miss.write_bytes(buf.getvalue())
        r = cc.check(str(miss), "codex", self.start, self.end)
        self.assertEqual(r["export"], "failed")
        self.assertIn("missing", r["reason"])


if __name__ == "__main__":
    unittest.main()
