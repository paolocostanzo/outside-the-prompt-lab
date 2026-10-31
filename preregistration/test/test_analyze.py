"""Tests for rq1/analyze.py on synthetic labels (no real R0 or model output exists). Run:
python3 -m unittest discover -s preregistration/test"""
import pathlib, sys, unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "rq1"))
import analyze as an  # noqa: E402

M = ["qwen3.8:27b-q8_0", "gemma4:26b-a4b-it-q8_0", "nemotron-3.5-lightning:30b-a3b-q4_K_M"]


def world(r0_of, models_of, n=(10, 20, 4), sizes=(30, 60, 8), flagged=(), late=(), doubtful=(), bundle=None, timeline=()):
    types = an.TYPES; frame, sample, ids = [], [], []
    k = 0
    for t, nt, st in zip(types, n, sizes):
        for i in range(st):
            k += 1; cid = f"C{k:03d}"
            src = "timeline" if cid in timeline else "query only"
            frame.append({"case_id": cid, "decision": "include", "product_type": t, "source": src,
                          "reason": "I?" if cid in doubtful else "I"})
            sample.append({"case_id": cid, "product_type": t, "source": src, "sampled": "yes" if i < nt else "no"})
            if i < nt: ids.append(cid)
    r0 = {"classes": {c: r0_of(c) for c in ids}, "bundle_model_finding": bundle or {}}
    models = {m: {c: models_of(m, c) for c in ids} for m in M}
    erratum = [{"case_id": c, "kind": "late ineligible (iii)"} for c in late]
    return frame, sample, r0, models, {"flagged": list(flagged), "late_ineligible": list(late)}, erratum, ids


class Analyze(unittest.TestCase):
    def test_majority(self):
        self.assertEqual(an.majority([1, 1, 4]), 1); self.assertIsNone(an.majority([1, 2, 4]))
        self.assertIsNone(an.majority([1, None, None])); self.assertIsNone(an.majority([1, 4]))  # two raters: both must agree
        self.assertEqual(an.majority([3, 3]), 3)

    def test_all_agree_supported(self):
        w = world(lambda c: 3, lambda m, c: 3)
        res = an.analyse(*w[:6])
        self.assertEqual(res["primary"]["R0"]["share"], 1.0); self.assertTrue(res["primary"]["verdict"].startswith("supported"))
        self.assertEqual(res["contested"], []); self.assertIsNone(res["H1a"]["fleiss_all_raters"])  # pe == 1: undefined

    def test_not_supported_and_unlabelled_against(self):
        w = world(lambda c: 4 if int(c[1:]) % 2 else 2, lambda m, c: 4)
        res = an.analyse(*w[:6])
        self.assertEqual(res["primary"]["verdict"], "not supported")
        w2 = world(lambda c: None if c == "C001" else 1, lambda m, c: 1)
        r2 = an.analyse(*w2[:6])
        self.assertEqual(r2["unlabelled"]["R0"], ["C001"]); self.assertLess(r2["primary"]["R0"]["share"], 1.0)
        self.assertIn("C001", r2["contested"])

    def test_variants_move_as_specified(self):
        w = world(lambda c: 2, lambda m, c: 2, flagged=("C001", "C002"), bundle={"C003": True})
        res = an.analyse(*w[:6])
        v = res["variants"]
        self.assertLess(v["D41 p6: contested cases against H1"]["R0"]["share"], res["primary"]["R0"]["share"])
        self.assertEqual(v["D41 p6: contested cases in favour of H1"]["R0"]["share"], 1.0)
        self.assertLess(v["D45/D41 p1: mixed bundles as class 4"]["R0"]["share"], 1.0)
        self.assertEqual(res["mixed_bundles"], ["C003"])

    def test_without_r2_and_drops(self):
        def mo(m, c): return 4 if m == "gemma4:26b-a4b-it-q8_0" else 1
        w = world(lambda c: 1, mo, late=("C001",), doubtful=("C002",))
        res = an.analyse(*w[:6])
        self.assertEqual(res["primary"]["model majority"]["share"], 1.0)
        self.assertEqual(res["variants"]["D43: model majority without R2"]["model majority"]["share"], 1.0)
        st = res["variants"]["D44 p5: without late-ineligible cases"]["R0"]["strata"]["agent client"]
        self.assertEqual(st[:2], [29, 9])
        st = res["variants"]["D44 p1: without the flagged (I?) cases"]["R0"]["strata"]["agent client"]
        self.assertEqual(st[:2], [29, 9])

    def test_stratum_dependence(self):
        w = world(lambda c: 3 if int(c[1:]) > 30 else 4, lambda m, c: 3 if int(c[1:]) > 30 else 4)
        res = an.analyse(*w[:6])
        s = res["by_product_type"]
        self.assertEqual(s["agent client"]["stratum"]["R0"]["share"], 0.0)
        self.assertFalse(s["SDK"]["interpreted"])  # 4 sampled < 10
        if res["primary"]["verdict"] != "not supported":
            self.assertTrue(s["MCP server or connector"]["H1 depends on it"])

    def test_refuses_wrong_r0_set_or_roster(self):
        w = list(world(lambda c: 1, lambda m, c: 1))
        bad = dict(w[2]); bad["classes"] = dict(bad["classes"]); bad["classes"].pop("C001")
        with self.assertRaises(SystemExit): an.analyse(w[0], w[1], bad, *w[3:6])
        models = dict(w[3]); models.pop(M[0])
        with self.assertRaises(SystemExit): an.analyse(w[0], w[1], w[2], models, *w[4:6])

    def test_invalid_answers_make_a_case_contested(self):
        w = world(lambda c: 3, lambda m, c: 3)
        quality = {m: {c: {"n_invalid": 1 if (m == M[0] and c == "C005") else 0, "tie": False, "answers": [0, 0, 0]} for c in w[6]} for m in M}
        res = an.analyse(*w[:6], quality)
        self.assertIn("C005", res["contested"])
        self.assertAlmostEqual(res["per_model"][M[0]]["invalid_answer_rate"], 1 / (3 * len(w[6])))
        self.assertFalse(res["per_model"][M[0]]["over_10_percent_invalid"])

    def test_per_model_shares_and_cohen_counts(self):
        def mo(m, c): return None if (m == M[1] and c == "C002") else 3
        w = world(lambda c: 3, mo)
        res = an.analyse(*w[:6])
        self.assertEqual(res["per_model"][M[1]]["unlabelled"], ["C002"])
        self.assertEqual(res["H1a"]["cohen_vs_R0"][M[1]]["left_out"], 1)
        self.assertEqual(res["H1a"]["cohen_vs_R0"][M[0]]["left_out"], 0)

    def test_grouping_erratum_stops(self):
        w = list(world(lambda c: 1, lambda m, c: 1))
        with self.assertRaises(SystemExit): an.analyse(*w[:5], [{"case_id": "C001", "kind": "grouping error"}])

    def test_source_split(self):
        w = world(lambda c: 3, lambda m, c: 3, timeline=("C001", "C060"))
        s = an.analyse(*w[:6])["source_split"]
        self.assertEqual(s["timeline_in_frame"], ["C001", "C060"]); self.assertEqual(s["timeline"]["sampled"], 1)
        d = s["timeline"]["domain"]["R0"]; self.assertFalse(s["interpreted"]); self.assertFalse(d["exact"])
        # AN-007: the unsampled timeline case C060 (another stratum) may be either class: the interval covers 1/2 and 1
        self.assertLessEqual(d["interval"][0], 0.5); self.assertGreaterEqual(d["interval"][1], 1.0)
        self.assertEqual(sum(d["observed"].values()), 1); self.assertEqual(d["unweighted"], 1.0)  # AN-009: one real observation
        w2 = world(lambda c: 3, lambda m, c: 3, timeline=("C060",))
        self.assertEqual(an.analyse(*w2[:6])["source_split"]["timeline"]["domain"], "not available")

    def test_no_majority_anywhere_still_reports(self):
        # AN-008: each model gives a different class on every case: no majority, labelled-only variant not available
        w = world(lambda c: 2, lambda m, c: M.index(m) + 1)
        res = an.analyse(*w[:6])
        self.assertEqual(res["primary"]["model majority"]["share"], 0.0)
        v = res["variants"]["D44 p6: labelled cases only"]
        self.assertFalse(v["model majority"]["available"]); self.assertTrue(v["verdict"].startswith("not available"))
        self.assertIn("n/a", an.markdown(res))

    def test_unweighted_counts_only_real_observations(self):
        # AN-009: all SDK cases without a majority; labelled-only drops them and must not count artificial SDK observations
        def mo(m, c): return (M.index(m) + 1) if int(c[1:]) > 90 else 3
        w = world(lambda c: 3, mo)
        v = an.analyse(*w[:6])["variants"]["D44 p6: labelled cases only"]["model majority"]
        self.assertEqual(v["unweighted"], 1.0); self.assertEqual(v["observed"]["SDK"], 0)
        self.assertEqual(sum(v["observed"].values()), 30)

    def test_stratum_estimates_ignore_other_strata(self):
        w = world(lambda c: 3, lambda m, c: 3)
        s = an.analyse(*w[:6])["by_product_type"]["agent client"]
        self.assertEqual(s["stratum"]["R0"]["share"], 1.0); self.assertEqual(s["frame without it"]["R0"]["share"], 1.0)

    def test_main_guards(self):
        import tempfile
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(SystemExit): an.main(d, d)  # never write into the run directory

    def test_markdown_renders(self):
        w = world(lambda c: 3, lambda m, c: 3)
        self.assertIn("**H1:", an.markdown(an.analyse(*w[:6])))


if __name__ == "__main__":
    unittest.main()

    def test_robustness_and_instability(self):
        # all agree on class 2, two flagged cases: contested against H1 still supported → robust
        w = world(lambda c: 2, lambda m, c: 2, flagged=("C001",))
        self.assertTrue(an.analyse(*w[:6])["h1_robust"]["robust"])
        # half the cases flagged: counting them against H1 flips the verdict → not robust (D41 point 6)
        w = world(lambda c: 2, lambda m, c: 2, flagged=tuple(f"C{k:03d}" for k in range(1, 99, 2)))
        r = an.analyse(*w[:6])
        self.assertFalse(r["h1_robust"]["robust"])
        # instability: differing valid classes and invalid answers are listed separately, per model
        ans = lambda *k: [{"class": x} for x in k]
        quality = {m: {c: {"n_invalid": 0, "tie": False, "answers": ans(3, 3, 3)} for c in w[6]} for m in M}
        quality[M[1]]["C002"] = {"n_invalid": 0, "tie": False, "answers": ans(1, 3, 3)}
        quality[M[1]]["C003"] = {"n_invalid": 1, "tie": False, "answers": ans(3, 3, None)}
        inst = an.analyse(*w[:6], quality)["instability"]
        self.assertEqual(inst[M[1]], {"differing_valid_classes": ["C002"], "with_invalid_answer": ["C003"]})
        self.assertEqual(inst[M[0]], {"differing_valid_classes": [], "with_invalid_answer": []})


class WithoutGit(unittest.TestCase):
    """Frozen inputs without git history: read from the working tree only when the SHA-256 recorded in the sample manifest
    matches; otherwise, or with no recorded hash, the analysis stops (fails closed)."""
    def setUp(self):
        import hashlib, json, tempfile
        self.tmp = tempfile.TemporaryDirectory(); root = pathlib.Path(self.tmp.name)
        self.saved = (an.HERE, an.ROOT, an.es.bound_to)
        an.ROOT, an.HERE = root, root / "preregistration" / "rq1"; an.HERE.mkdir(parents=True)
        self.frame = b"case_id,decision\nC001,include\n"; (root / an.sf.FRAME_IN_REPO).write_bytes(self.frame)
        self.sampler = pathlib.Path(an.sf.__file__).resolve().read_bytes()
        self.man = {"frame_commit": "f" * 40, "frame_sha256": hashlib.sha256(self.frame).hexdigest(),
                    "script_sha256": hashlib.sha256(self.sampler).hexdigest()}
        (an.HERE / "rq1-sample-manifest.json").write_text(json.dumps(self.man))

    def tearDown(self):
        an.HERE, an.ROOT, an.es.bound_to = self.saved; self.tmp.cleanup()

    def no_git(self):
        import subprocess
        def fail(commit): raise subprocess.CalledProcessError(128, ["git"])
        an.es.bound_to = fail

    def test_frame_accepted_by_recorded_hash(self):
        c = self.man["frame_commit"]
        self.assertEqual(an.git_show(c, an.sf.FRAME_IN_REPO), self.frame)
        self.assertEqual(an.git_show(c, an.sf.FRAME_IN_REPO, self.man["frame_sha256"]), self.frame)

    def test_changed_frame_refused(self):
        (an.ROOT / an.sf.FRAME_IN_REPO).write_bytes(self.frame.replace(b"C001", b"C999"))
        with self.assertRaises(SystemExit): an.git_show(self.man["frame_commit"], an.sf.FRAME_IN_REPO)

    def test_missing_file_or_other_commit_refused(self):
        (an.ROOT / an.sf.FRAME_IN_REPO).unlink()
        with self.assertRaises(SystemExit): an.git_show(self.man["frame_commit"], an.sf.FRAME_IN_REPO)
        with self.assertRaises(SystemExit): an.git_show("e" * 40, an.sf.FRAME_IN_REPO)  # no hash recorded for that commit

    def test_no_recorded_hash_refused(self):
        p = an.ROOT / an.ESTIMATE_IN_REPO; p.write_bytes(b"x")
        self.assertIsNone(an.recorded_sha256(self.man["frame_commit"], an.ESTIMATE_IN_REPO))
        with self.assertRaises(SystemExit): an.git_show(self.man["frame_commit"], an.ESTIMATE_IN_REPO)

    def test_estimate_binding_fails_closed_without_git(self):
        self.no_git()
        with self.assertRaises(SystemExit): an.estimate_binding(self.man["frame_commit"])

    def test_estimate_binding_uses_bound_to_with_git(self):
        an.es.bound_to = lambda commit: "ab" * 32
        self.assertEqual(an.estimate_binding(self.man["frame_commit"]), "ab" * 32)

    def test_sampler_hash(self):
        an.check_sampler(self.man)
        with self.assertRaises(SystemExit): an.check_sampler({**self.man, "script_sha256": "0" * 64})

    def test_git_history_wins_over_working_tree(self):
        import os, subprocess
        root = an.ROOT
        env = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_SYSTEM": os.devnull, "GIT_AUTHOR_NAME": "t",
               "GIT_AUTHOR_EMAIL": "t@t", "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t"}
        run = lambda *a: subprocess.run(["git", "-C", str(root), *a], check=True, capture_output=True, env=env).stdout
        run("init", "-q"); run("add", an.sf.FRAME_IN_REPO); run("commit", "-q", "-m", "frame")
        c = run("rev-parse", "HEAD").decode().strip()
        (root / an.sf.FRAME_IN_REPO).write_bytes(b"changed\n")  # the commit is read, not the working tree
        self.assertEqual(an.git_show(c, an.sf.FRAME_IN_REPO), self.frame)
