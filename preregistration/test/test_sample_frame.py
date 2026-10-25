"""Tests for rq1/sample_frame.py (D44). Offline: no git commit or drand request is made. Run:
python3 -m unittest discover -s preregistration/test"""
import collections, csv, io, pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import sample_frame as sf  # noqa: E402

SEED = "ab" * 32


def frame(counts, timeline=1, extra=(), lineterm="\r\n"):
    buf = io.StringIO(); w = csv.DictWriter(buf, fieldnames=sf.COLUMNS, lineterminator=lineterm); w.writeheader()
    i = 0
    base = {"date": "2026-07-01", "product": "p", "primary_source": "https://example.org", "note": "", "reason": "I"}
    for t, k in counts.items():
        for _ in range(k):
            i += 1; w.writerow({**base, "case_id": f"Q{i:04d}", "records": f"CVE-2026-{i:05d}", "decision": "include",
                                "source": "query only", "product_type": t})
    for j in range(timeline):
        w.writerow({**base, "case_id": f"T{j:02d}", "records": f"GHSA-t{j}", "decision": "include", "source": "timeline",
                    "product_type": "SDK"})
    w.writerow({**base, "case_id": "X00", "records": "CVE-2026-99999", "decision": "exclude", "reason": "E1", "source": "",
                "product_type": "n/a"})
    for row in extra: w.writerow({**base, **row})
    return buf.getvalue().encode()


REAL = {"agent client": 126, "MCP server or connector": 338, "SDK": 38}


class Sample(unittest.TestCase):
    def test_real_sizes_proportional(self):
        sizes, alloc, out = sf.sample(sf.read_frame(frame(REAL, timeline=0)), SEED)
        self.assertEqual(sum(alloc.values()), 120)
        self.assertEqual(alloc, {"agent client": 30, "MCP server or connector": 81, "SDK": 9})  # quotas 30.1, 80.8, 9.1
        self.assertFalse(any(r["case_id"] == "X00" for r in out))

    def test_timeline_cases_sit_in_their_type(self):
        sizes, alloc, out = sf.sample(sf.read_frame(frame({"agent client": 80, "MCP server or connector": 210, "SDK": 25})), SEED)
        t = [r for r in out if r["case_id"] == "T00"][0]
        self.assertEqual((t["product_type"], t["source"]), ("SDK", "timeline"))
        self.assertEqual(sizes["SDK"], 26); self.assertEqual(sum(alloc.values()), 120)

    def test_deterministic_and_seed_dependent(self):
        rows = sf.read_frame(frame(REAL))
        self.assertEqual(sf.sample(rows, SEED), sf.sample(rows, SEED))
        self.assertNotEqual(sf.sample(rows, SEED)[2], sf.sample(rows, "cd" * 32)[2])
        self.assertNotEqual(sf.seed_of("f" * 64, "a"), sf.seed_of("f" * 64, "b"))

    def test_small_frame_taken_whole_and_minimum_one(self):
        _, _, out = sf.sample(sf.read_frame(frame({"agent client": 30, "MCP server or connector": 60, "SDK": 5})), SEED)
        self.assertTrue(all(r["sampled"] == "yes" for r in out)); self.assertEqual(len(out), 96)
        _, alloc, _ = sf.sample(sf.read_frame(frame({"agent client": 10, "MCP server or connector": 1000, "SDK": 0})), SEED)
        self.assertEqual(alloc["SDK"], 1); self.assertEqual(sum(alloc.values()), 120)

    def test_too_few_places(self):
        with self.assertRaises(SystemExit): sf.allocate({"a": 5, "b": 1, "c": 1}, 2)

    def test_replacement_order_complete(self):
        _, _, out = sf.sample(sf.read_frame(frame(REAL)), SEED)
        by = collections.defaultdict(list)
        for r in out: by[r["product_type"]].append(r["rank"])
        for ranks in by.values(): self.assertEqual(ranks, list(range(1, len(ranks) + 1)))

    def test_bad_frames_refused(self):
        bad = [{"case_id": "U1", "records": "CVE-1", "decision": "uncertain", "source": "query only", "product_type": "SDK"},
               {"case_id": "U2", "records": "CVE-2", "decision": "Include", "source": "query only", "product_type": "SDK"},
               {"case_id": "U3", "records": "CVE-3", "decision": "include", "source": "query only", "product_type": "library"},
               {"case_id": "U4", "records": "CVE-4", "decision": "include", "source": "blog", "product_type": "SDK"},
               {"case_id": "U5", "records": "CVE-2026-59950", "decision": "include", "source": "query only", "product_type": "SDK"},
               {"case_id": "Q0001", "records": "CVE-5", "decision": "include", "source": "query only", "product_type": "SDK"},
               {"case_id": "U6", "records": "CVE-6", "decision": "exclude", "reason": " ", "source": "", "product_type": "n/a"}]
        for row in bad:
            with self.assertRaises(SystemExit, msg=row["case_id"]): sf.read_frame(frame({"SDK": 2}, extra=[row]))
        with self.assertRaises(SystemExit): sf.read_frame(b"\xef\xbb\xbf" + frame({"SDK": 2}))
        with self.assertRaises(SystemExit): sf.read_frame(frame({"SDK": 2}).replace(b"primary_source", b"source_url", 1))

    def test_line_endings_change_the_bytes(self):
        # why the frame is committed with -text and hashed from the commit: same rows, different bytes, different seed
        a, b = frame(REAL), frame(REAL, lineterm="\n")
        self.assertEqual(sf.read_frame(a), sf.read_frame(b)); self.assertNotEqual(a, b)

    def test_round_times(self):  # a 20:00:00 UTC time falls exactly on a mainnet round
        import datetime
        r = (int(datetime.datetime(2026, 10, 26, 20, tzinfo=datetime.timezone.utc).timestamp()) - sf.DRAND_GENESIS) // 30 + 1
        self.assertEqual(datetime.datetime.fromtimestamp(sf.round_time(r), datetime.timezone.utc).hour, 20)


class Main(unittest.TestCase):
    """draw and verify with git, GitHub events, the Internet Archive and drand replaced by stand-ins."""
    def setUp(self):
        import calendar, tempfile
        self.tmp = tempfile.TemporaryDirectory(); d = pathlib.Path(self.tmp.name)
        self.saved = (sf.HERE, sf.FRAME, sf.git, sf.git_ok, sf.fetch_round, sf.push_events, sf.first_capture, sf.archived_event,
                      sf.frame_commits)
        self.ev_capture = None; sf.archived_event = lambda sha, push_ts: self.ev_capture
        self.raw = frame(REAL); (d / "rq1-frame.csv").write_bytes(self.raw)
        sf.HERE, sf.FRAME = d, d / "rq1-frame.csv"
        self.script = pathlib.Path(sf.__file__).read_bytes()
        self.commit_t = calendar.timegm((2026, 10, 20, 11, 0, 0))
        self.ancestor = True; self.history = {"c0ffee": ["c0ffee"]}  # head -> commits touching the frame in its history
        self.frames = {"c0ffee": self.raw}  # head -> frame at that head (absent: no frame)
        self.events = [{"type": "PushEvent", "created_at": "2026-10-20T12:00:00Z", "payload": {"head": "c0ffee"}}]
        self.capture = calendar.timegm((2026, 10, 20, 12, 10, 0)); self.fetched = []
        def git(*a):
            if a[0] in ("fetch",): return b""
            if a[0] == "rev-parse": return b"c0ffee\n"
            if a[0] == "ls-remote": return b"m4st3r\trefs/heads/master\n"
            if a[0] == "show" and a[1] == "-s": return str(self.commit_t).encode()
            if a[0] == "show" and a[1].endswith(sf.SCRIPT_IN_REPO): return self.script
            if a[0] == "show" and ":" in a[1]: return self.frames[a[1].split(":")[0]]
            raise AssertionError(a)
        def git_ok(*a):
            if a[0] == "merge-base": return self.ancestor
            if a[0] == "cat-file":
                h, _, path = a[2].partition(":")
                return h in self.history and (not path or h in self.frames)
            raise AssertionError(a)
        sf.git, sf.git_ok = git, git_ok
        sf.frame_commits = lambda h: self.history[h]  # the real function is tested on real repositories in History
        sf.push_events = lambda: self.events
        sf.first_capture = lambda url: self.capture
        def fetch(r, chain=None): self.fetched.append(r); return "beef" * 16
        sf.fetch_round = fetch
        self.r20 = (calendar.timegm((2026, 10, 20, 20, 0, 0)) - sf.DRAND_GENESIS) // 30 + 1

    def tearDown(self):
        (sf.HERE, sf.FRAME, sf.git, sf.git_ok, sf.fetch_round, sf.push_events, sf.first_capture,
         sf.archived_event, sf.frame_commits) = self.saved; self.tmp.cleanup()

    def quiet(self, *a):
        import contextlib
        with contextlib.redirect_stdout(io.StringIO()): return sf.main(*a)

    def refused(self):
        with self.assertRaises(SystemExit): self.quiet("c0ffee")
        self.assertEqual(self.fetched, []); self.assertFalse((sf.HERE / "rq1-sample.csv").exists())

    def test_draw_once_and_verify(self):
        import contextlib, json
        self.quiet("c0ffee")
        m = json.loads((sf.HERE / "rq1-sample-manifest.json").read_text())
        self.assertEqual(m["sampled"], 120); self.assertEqual(m["drand_round"], self.r20); self.assertEqual(self.fetched, [self.r20])
        self.assertEqual(m["seed"], sf.seed_of(m["frame_sha256"], "beef" * 16))
        with contextlib.redirect_stdout(io.StringIO()): sf.verify()
        with self.assertRaises(SystemExit): self.quiet("c0ffee")
        rows = (sf.HERE / "rq1-sample.csv").read_text().replace(",yes", ",no", 1); (sf.HERE / "rq1-sample.csv").write_text(rows)
        with self.assertRaises(SystemExit): sf.verify()

    def test_only_the_first_round_after_the_capture(self):
        import calendar
        T = calendar.timegm((2026, 10, 20, 20, 0, 0)); R = (T - sf.DRAND_GENESIS) // 30 + 1
        self.assertEqual(sf.first_round_after(T - 3600 * 8), R)
        self.assertEqual(sf.first_round_after(T - 3600), R)
        self.assertEqual(sf.first_round_after(T - 3599), R + 2880)
        self.capture = calendar.timegm((2026, 10, 20, 19, 30, 0)); self.events[0]["created_at"] = "2026-10-20T19:10:00Z"
        self.quiet("c0ffee"); self.assertEqual(self.fetched, [R + 2880])

    def push(self, head, when, touching, frame=None):
        self.history[head] = touching
        if frame is not None: self.frames[head] = frame
        self.events.append({"type": "PushEvent", "created_at": when, "payload": {"head": head}})

    def test_other_pushed_head_with_a_frame_commit_voids(self):
        self.push("side", "2026-10-20T13:00:00Z", ["side"]); self.refused()

    def test_intermediate_frame_commit_in_the_same_push_voids(self):
        self.history["c0ffee"] = ["c0ffee", "a1a1a1"]; self.refused()  # A added a frame, B (the head) replaced it

    def test_other_pushed_heads_without_frame_or_descending_pass(self):
        self.push("code", "2026-10-20T13:00:00Z", []); self.push("later", "2026-10-20T14:00:00Z", ["c0ffee"], self.raw)
        self.quiet("c0ffee"); self.assertEqual(self.fetched, [self.r20])

    def test_merge_that_changes_the_frame_voids(self):
        self.push("evil", "2026-10-20T13:00:00Z", ["c0ffee"], self.raw.replace(b"Q0001", b"Q9999")); self.refused()

    def test_unknown_pushed_head_refused(self):
        self.events.append({"type": "PushEvent", "created_at": "2026-10-20T13:00:00Z", "payload": {"head": "gone"}})
        self.refused()

    def test_not_head_of_a_push_refused(self):
        self.events[0]["payload"]["head"] = "later"; self.history["later"] = ["c0ffee"]; self.refused()

    def test_capture_is_evidence_never_a_reason_to_redraw(self):
        import json
        self.capture = None; self.quiet("c0ffee"); self.assertEqual(self.fetched, [self.r20])
        m = json.loads((sf.HERE / "rq1-sample-manifest.json").read_text())
        self.assertEqual(m["capture"], {"utc": None, "within_30_min_after_push": False, "events_page_utc": None})

    def test_verifiability_reported(self):
        import contextlib
        self.capture = None; self.quiet("c0ffee")
        out = io.StringIO()
        with contextlib.redirect_stdout(out): sf.verify()
        self.assertIn("not independently verifiable", out.getvalue())
        self.assertTrue(sf.independently_verifiable({"within_30_min_after_push": False, "events_page_utc": "2026-10-20T12:05:00+00:00"}))
        self.assertTrue(sf.independently_verifiable({"within_30_min_after_push": True, "events_page_utc": None}))

    def test_late_capture_keeps_the_push_round(self):
        self.capture = self.commit_t + 3600 * 9; self.quiet("c0ffee"); self.assertEqual(self.fetched, [self.r20])

    def test_frame_pushed_after_the_round_does_not_void(self):
        self.push("later", "2026-10-20T21:00:00Z", ["later", "c0ffee"])
        self.quiet("c0ffee"); self.assertEqual(self.fetched, [self.r20])

    def test_verify_online_detects_a_wrong_beacon(self):
        import contextlib
        self.quiet("c0ffee")
        sf.fetch_round = lambda r, chain=None: "dead" * 16
        with self.assertRaises(SystemExit), contextlib.redirect_stdout(io.StringIO()): sf.verify(online=True)

    def test_backdated_unpushed_or_changed_script_refused(self):
        import calendar
        self.commit_t = calendar.timegm((2026, 10, 20, 12, 0, 1)); self.refused()
        self.commit_t -= 3600; self.ancestor = False; self.refused()
        self.ancestor = True; self.script = b"# edited after the commit"; self.refused()

    def test_round_not_drawn_yet(self):
        self.capture = 4102444800; self.events[0]["created_at"] = "2099-12-31T23:50:00Z"; self.commit_t = 0
        self.refused()


class History(unittest.TestCase):
    """frame_commits on real git repositories: no merge may hide a frame change."""
    def setUp(self):
        import os, subprocess, tempfile
        self.tmp = tempfile.TemporaryDirectory(); self.d = d = pathlib.Path(self.tmp.name); self.saved = sf.HERE
        env = {"GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t",
               "PATH": os.environ["PATH"], "HOME": str(d)}
        self.run = lambda *a: subprocess.run(["git", "-C", str(d), *a], check=True, capture_output=True, env=env).stdout.decode().strip()
        self.f = d / sf.FRAME_IN_REPO; self.f.parent.mkdir(parents=True)
        self.run("init", "-q", "-b", "master"); (d / "README").write_text("x"); self.run("add", "."); self.run("commit", "-qm", "base")
        self.f.write_text("F\n"); self.run("add", "."); self.run("commit", "-qm", "frame F"); self.F = self.run("rev-parse", "HEAD")
        sf.HERE = d

    def tearDown(self):
        sf.HERE = self.saved; self.tmp.cleanup()

    def commit_other(self, name):
        (self.d / name).write_text(name); self.run("add", "."); self.run("commit", "-qm", name)

    def test_merge_does_not_hide_a_side_branch_frame_change(self):
        run = self.run
        run("checkout", "-qb", "side"); self.f.write_text("X\n"); run("commit", "-qam", "frame X"); X = run("rev-parse", "HEAD")
        run("checkout", "-q", "master"); run("merge", "-q", "-s", "ours", "--no-edit", "side"); M = run("rev-parse", "HEAD")
        self.assertNotIn(X, run("log", "--format=%H", M, "--", sf.FRAME_IN_REPO).split())  # default simplification hides X
        self.assertEqual(set(sf.frame_commits(M)), {self.F, X})

    def test_intermediate_merges_that_change_and_restore_the_frame(self):
        run = self.run
        run("checkout", "-qb", "b1"); self.commit_other("a"); run("checkout", "-q", "master")
        run("merge", "-q", "--no-commit", "--no-ff", "b1"); self.f.write_text("CHANGED\n"); run("add", "."); run("commit", "-qm", "M1")
        M1 = run("rev-parse", "HEAD")
        run("checkout", "-qb", "b2"); self.commit_other("b"); run("checkout", "-q", "master")
        run("merge", "-q", "--no-commit", "--no-ff", "b2"); self.f.write_text("F\n"); run("add", "."); run("commit", "-qm", "M2")
        M2 = run("rev-parse", "HEAD")
        self.assertEqual(run("show", f"{M2}:{sf.FRAME_IN_REPO}"), "F")
        got = set(sf.frame_commits(M2)); self.assertIn(M1, got); self.assertIn(M2, got)

    def test_ordinary_merges_pass(self):
        run = self.run
        run("checkout", "-qb", "b1"); self.commit_other("a"); run("checkout", "-q", "master"); self.commit_other("c")
        run("merge", "-q", "--no-edit", "b1"); M = run("rev-parse", "HEAD")
        self.assertEqual(sf.frame_commits(M), [self.F])


class Archive(unittest.TestCase):
    """verify_archive.py works on a folder without git history and refuses a changed frame or sample."""
    def test_verify_from_folder(self):
        import contextlib, csv as _csv, hashlib, json, tempfile
        import verify_archive as va
        with tempfile.TemporaryDirectory() as d:
            d = pathlib.Path(d); raw = frame(REAL); (d / "rq1-frame.csv").write_bytes(raw)
            F = hashlib.sha256(raw).hexdigest(); B = "beef" * 16; seed = sf.seed_of(F, B)
            push = "2026-10-20T12:00:00Z"; rnd = sf.first_round_after(sf.ts(push))
            _, _, out = sf.sample(sf.read_frame(raw), seed)
            with open(d / "rq1-sample.csv", "w", newline="") as f:
                w = _csv.DictWriter(f, fieldnames=sf.SAMPLE_COLUMNS); w.writeheader(); w.writerows(out)
            (d / "rq1-sample-manifest.json").write_text(json.dumps({"frame_sha256": F, "drand_randomness": B, "seed": seed,
                "push_event": {"created_at": push}, "drand_chain": sf.DRAND_CHAIN, "drand_round": rnd,
                "capture": {"utc": None, "within_30_min_after_push": True, "events_page_utc": None}}))
            with contextlib.redirect_stdout(io.StringIO()): va.main(folder=d)
            (d / "rq1-sample.csv").write_text((d / "rq1-sample.csv").read_text().replace(",yes", ",no", 1))
            with self.assertRaises(SystemExit): va.main(folder=d)
            (d / "rq1-frame.csv").write_bytes(raw.replace(b"Q0001", b"Q9999"))
            with self.assertRaises(SystemExit): va.main(folder=d)


class Relays(unittest.TestCase):
    def setUp(self): self.saved = sf.urllib.request.urlopen
    def tearDown(self): sf.urllib.request.urlopen = self.saved

    def fake(self, answers):
        import contextlib, json
        it = iter(answers)
        @contextlib.contextmanager
        def urlopen(url, timeout=30): yield io.BytesIO(json.dumps(next(it)).encode())
        sf.urllib.request.urlopen = urlopen

    def test_agree(self):
        self.fake([{"round": 5, "randomness": "aa"}, {"round": 5, "randomness": "aa"}]); self.assertEqual(sf.fetch_round(5), "aa")

    def test_disagree_or_wrong_round(self):
        self.fake([{"round": 5, "randomness": "aa"}, {"round": 5, "randomness": "bb"}])
        with self.assertRaises(SystemExit): sf.fetch_round(5)
        self.fake([{"round": 6, "randomness": "aa"}])
        with self.assertRaises(SystemExit): sf.fetch_round(5)

    def test_pilot_ids_normalised(self):
        row = {"case_id": "U9", "records": "CVE-1; cve-2026-59950", "decision": "include", "source": "query only", "product_type": "SDK"}
        with self.assertRaises(SystemExit): sf.read_frame(frame({"SDK": 2}, extra=[row]))

if __name__ == "__main__":
    unittest.main()
