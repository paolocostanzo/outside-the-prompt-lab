"""secret_gate.py (D26): fingerprints, exact and format matching, archives, git ranges, failing closed, and the orchestrators' use
of it. Fake secrets are built at run time, so that this file itself contains nothing the gate would flag.
Run: python3 -m unittest discover -s telemetry/test"""
import gzip, importlib.util, io, json, os, secrets, subprocess, sys, tarfile, tempfile, unittest, zipfile
from pathlib import Path
from types import SimpleNamespace as _NS

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"


def _load(name):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sg = _load("secret_gate")
q4 = _load("q4_events")
q4.STATE = Path(tempfile.mkdtemp())  # never the real ~/.agentlab-q4 of the host


def fake(kind):
    """A value with the shape of a real secret, assembled at run time."""
    r = secrets.token_urlsafe(48).replace("-", "a").replace("_", "b")
    return {"anthropic": "sk-" + "ant-" + "oat01-" + r,
            "google": "AI" + "za" + r[:35],
            "jwt": "ey" + "J" + r[:20] + ".ey" + "J" + r[20:40] + "." + r[40:60],
            "github": "gh" + "p_" + (r * 2)[:36],
            "opaque": secrets.token_hex(24)}[kind]


def tgz(members):
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as t:
        for name, data in members.items():
            info = tarfile.TarInfo(name)
            info.size = len(data)
            t.addfile(info, io.BytesIO(data))
    return buf.getvalue()


class Formats(unittest.TestCase):
    def kinds(self, text):
        return {k for k, _ in sg.scan_bytes(text.encode())}

    def test_each_known_format_is_found(self):
        self.assertIn("anthropic-token", self.kinds("x " + fake("anthropic") + " y"))
        self.assertIn("google-api-key", self.kinds("key=" + fake("google")))
        self.assertIn("jwt", self.kinds('{"a": "' + fake("jwt") + '"}'))
        self.assertIn("github-token", self.kinds(fake("github")))
        self.assertIn("private-key", self.kinds("-----BEGIN " + "OPENSSH PRIVATE KEY-----\nabc"))
        self.assertIn("token-field", self.kinds('{"refresh_' + 'token": "' + fake("opaque") + '"}'))
        self.assertIn("secret-env", self.kinds("export CLAUDE_CODE_OAUTH_" + "TOKEN=" + fake("opaque")))

    def test_names_and_placeholders_are_not_secrets(self):
        for text in ("set CLAUDE_CODE_OAUTH_TOKEN in a file readable only by the lab user",
                     "printf 'export CLAUDE_CODE_OAUTH_TOKEN=%s\\n' \"$T\"",
                     "GEMINI_API_KEY=$GEMINI_API_KEY", '"refresh_token": ""', "sk-ant- is the prefix of Anthropic tokens",
                     "the token starts with sk-ant-oat"):
            self.assertEqual(self.kinds(text), set(), text)

    def test_line_numbers_and_no_value_in_the_report(self):
        v = fake("google")
        found = sg.scan_bytes(("a\nb\n" + v + "\n").encode())
        self.assertEqual(found, [("google-api-key", 3)])
        out = io.StringIO()
        sg.report([{"path": "f", "member": None, "kind": "google-api-key", "line": 3}], [], out)
        self.assertNotIn(v, out.getvalue())


class Fingerprints(unittest.TestCase):
    def setUp(self):
        self.home = Path(tempfile.mkdtemp())
        self.claude, self.codex, self.gem = fake("opaque"), fake("opaque"), fake("opaque")
        (self.home / ".agentlab_claude_token").write_text(self.claude + "\n")
        (self.home / ".codex").mkdir()
        (self.home / ".codex/auth.json").write_text(json.dumps({"auth_mode": "chatgpt", "tokens": {"refresh_token": self.codex}}))
        (self.home / ".agentlab_secrets").write_text(f"export GEMINI_API_KEY='{self.gem}'\nSHORT=abc\n")

    def test_values_are_fingerprinted_never_kept(self):
        d = sg.fingerprints(self.home)
        self.assertEqual(d["unreadable"], [])
        self.assertEqual({f["kind"] for f in d["fingerprints"]}, {"claude-oauth-token", "codex-login", "lab-secret"})
        blob = json.dumps(d)
        for v in (self.claude, self.codex, self.gem):
            self.assertNotIn(v, blob)
        self.assertNotIn("abc", [f["prefix"] for f in d["fingerprints"]], "values shorter than MIN_LEN are not fingerprinted")
        self.assertIn(".codex/auth.json", [f["source"] for f in d["fingerprints"]])

    def test_exact_match_finds_an_opaque_secret_in_a_nested_archive(self):
        fps = sg.fingerprints(self.home)["fingerprints"]
        inner = tgz({"logs/session.jsonl": ('{"msg": "ran with ' + self.codex + '"}\n').encode()})
        outer = tgz({"client-logs.tgz": inner})
        run = Path(tempfile.mkdtemp())
        (run / "vm-out.tgz").write_bytes(outer)
        (run / "clean.txt").write_text("nothing here")
        findings, failures = sg.scan_paths([run], fps)
        self.assertEqual(failures, [])
        self.assertEqual([(f["kind"], f["member"]) for f in findings], [("codex-login", "client-logs.tgz/logs/session.jsonl")])
        self.assertEqual(sg.scan_paths([run], [])[0], [], "an opaque value is found only by its fingerprint")

    def test_unreadable_store_is_reported_and_refused(self):
        (self.home / ".config/cursor").mkdir(parents=True)
        (self.home / ".config/cursor/auth.json").write_text("{not json")
        d = sg.fingerprints(self.home)
        self.assertEqual([u["source"] for u in d["unreadable"]], [".config/cursor/auth.json"])
        f = self.home / "fp.json"
        f.write_text(json.dumps(d))
        with self.assertRaises(SystemExit):
            sg.load_fps(str(f))

    def test_merge_keeps_a_renewed_secret_and_the_old_one(self):
        a = {"fingerprints": [sg.fingerprint(fake("opaque"), "codex-login", "x")]}
        b = {"fingerprints": [sg.fingerprint(fake("opaque"), "codex-login", "x")], "created": 2}
        m = sg.merge_fingerprints(a, b)
        self.assertEqual(len(m["fingerprints"]), 2)
        self.assertEqual(len(sg.merge_fingerprints(m, b)["fingerprints"]), 2)


class FailsClosed(unittest.TestCase):
    def test_corrupt_archive_and_unsupported_format(self):
        d = Path(tempfile.mkdtemp())
        (d / "broken.tgz").write_bytes(b"\x1f\x8b" + os.urandom(64))
        (d / "x.7z").write_bytes(b"7z")
        findings, failures = sg.scan_paths([d])
        self.assertEqual(findings, [])
        self.assertEqual(sorted(Path(f["path"]).name for f in failures), ["broken.tgz", "x.7z"])
        self.assertEqual(sg.report(findings, failures, io.StringIO()), 2)

    def test_missing_path(self):
        self.assertEqual(sg.scan_paths(["/nonexistent/q4"])[1][0]["error"], "does not exist")

    def test_zip_gzip_and_skip(self):
        d = Path(tempfile.mkdtemp())
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as zf:
            zf.writestr("a/b.txt", "key " + fake("google"))
        (d / "e.zip").write_bytes(z.getvalue())
        (d / "j.log.gz").write_bytes(gzip.compress(fake("jwt").encode()))
        (d / "attempts").mkdir()
        (d / "attempts/old.txt").write_text(fake("anthropic"))
        kinds = {f["kind"] for f in sg.scan_paths([d], skip={"attempts"})[0]}  # a stored zip is also found in its raw bytes
        self.assertEqual(kinds, {"google-api-key", "jwt"})


class Git(unittest.TestCase):
    def git(self, *a):
        subprocess.run(["git", "-C", str(self.repo), "-c", "user.email=t@t", "-c", "user.name=t", *a], check=True,
                       capture_output=True)

    def setUp(self):
        self.repo = Path(tempfile.mkdtemp())
        self.git("init", "-q")
        (self.repo / "a.txt").write_text("hello")
        self.git("add", ".")
        self.git("commit", "-qm", "first")

    def head(self):
        return subprocess.run(["git", "-C", str(self.repo), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()

    def test_secret_added_then_removed_is_still_found(self):
        base = self.head()
        (self.repo / "doc.md").write_text("token " + fake("anthropic"))
        self.git("add", ".")
        self.git("commit", "-qm", "add")
        (self.repo / "doc.md").write_text("token removed")
        self.git("add", ".")
        self.git("commit", "-qm", "remove")
        findings, failures = sg.scan_git(self.repo, base, self.head())
        self.assertEqual(failures, [])
        self.assertEqual([f["kind"] for f in findings], ["anthropic-token"])

    def test_commit_message_and_whole_history(self):
        (self.repo / "b.txt").write_text("fine")
        self.git("add", ".")
        self.git("commit", "-qm", "note: " + fake("google"))
        findings, _ = sg.scan_git(self.repo, sg.EMPTY_TREE, self.head())
        self.assertEqual([(f["kind"], "message" in f["path"]) for f in findings], [("google-api-key", True)])

    def test_clean_range_and_bad_revision(self):
        self.assertEqual(sg.scan_git(self.repo, sg.EMPTY_TREE, self.head()), ([], []))
        self.assertEqual(len(sg.scan_git(self.repo, "nonexistent", self.head())[1]), 1)

    def test_cli_exit_codes(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "secret_gate.py"), "scan-git", "--repo", str(self.repo), sg.EMPTY_TREE,
                            "HEAD"], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stderr)


class Orchestrator(unittest.TestCase):
    """q4_events.secret_problems: fingerprints come from the VM over ssh; the host state keeps them; findings stop the run."""

    def host(self, fps, rc=0):
        class H:
            def ssh(self, ip, cmd, timeout=120):
                assert "secret_gate.py fingerprints" in cmd
                return _NS(returncode=rc, stdout=json.dumps(fps), stderr="")
        return H()

    def test_clean_run_and_state_file(self):
        d = Path(tempfile.mkdtemp())
        (d / "cell.stdout.txt").write_text("ok")
        v = fake("opaque")
        self.assertEqual(q4.secret_problems(self.host({"fingerprints": [sg.fingerprint(v, "lab-secret", "s")], "unreadable": []}),
                                            "ip", d), [])
        st = q4.STATE / "secret-fingerprints.json"
        self.assertEqual(oct(st.stat().st_mode & 0o777), "0o600")
        self.assertNotIn(v, st.read_text())

    def test_finding_names_file_and_kind_only(self):
        d = Path(tempfile.mkdtemp())
        v = fake("opaque")
        (d / "client-logs.tgz").write_bytes(tgz({"home/.gemini/tmp/chat.json": ("using " + v).encode()}))
        probs = q4.secret_problems(self.host({"fingerprints": [sg.fingerprint(v, "lab-secret", "s")], "unreadable": []}), "ip", d)
        self.assertEqual(len(probs), 1)
        self.assertIn("client-logs.tgz", probs[0])
        self.assertIn("lab-secret", probs[0])
        self.assertNotIn(v, probs[0])

    def test_fails_closed_without_fingerprints(self):
        d = Path(tempfile.mkdtemp())
        self.assertTrue(q4.secret_problems(self.host({"fingerprints": [], "unreadable": [{"source": ".codex/auth.json"}]}, rc=2),
                                           "ip", d))

        class Broken:
            def ssh(self, ip, cmd, timeout=120):
                return _NS(returncode=255, stdout="", stderr="no route")
        self.assertTrue(q4.secret_problems(Broken(), "ip", d))


if __name__ == "__main__":
    unittest.main()
