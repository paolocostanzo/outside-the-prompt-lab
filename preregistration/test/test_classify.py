#!/usr/bin/env python3
"""Offline tests for preregistration/classify.py. Run: python3 -m unittest discover -s preregistration/test
No network: urlopen is replaced by a function that fails, and http_json is monkeypatched per test.
The pilot (cases.json, human.json, results/) is only read, and its hashes are checked before and after."""
import importlib.util, json, pathlib, tempfile, unittest, urllib.request, hashlib, io, contextlib

HERE = pathlib.Path(__file__).resolve().parent.parent / "pilot"
spec = importlib.util.spec_from_file_location("classify", HERE.parent / "classify.py")
classify = importlib.util.module_from_spec(spec); spec.loader.exec_module(classify)


def _no_network(*a, **k): raise AssertionError("network call attempted in tests")
urllib.request.urlopen = _no_network
PILOT = [HERE / "cases.json", HERE / "human.json"] + sorted((HERE / "results").glob("*"))


def snapshot():
    return {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in PILOT if p.is_file()}


def fake_ollama(answers, models=("m:1",)):
    """http_json stand-in: /api/tags lists `models`; /api/chat returns the next canned answer."""
    it = iter(answers)
    def http_json(path, body=None, timeout=60):
        if path == "/api/tags": return {"models": [{"name": m, "digest": "sha256:" + "0" * 64} for m in models]}
        return {"message": {"content": next(it)}, "eval_count": 1, "prompt_eval_count": 100}
    return http_json


ZERO = "0" * 64


@contextlib.contextmanager
def confirmatory_env(models=("a:1", "b:1")):
    """A test roster with the fake digests of fake_ollama, and R0 treated as committed."""
    roster, comm = classify.ROSTER, classify.committed
    classify.ROSTER = {m: ZERO for m in models}; classify.committed = lambda p: "c0ffee"
    try: yield
    finally: classify.ROSTER, classify.committed = roster, comm


def make_run(t, answers, cases=("X1", "X2"), r0=None, models=("a:1", "b:1"), runs=3, mode="confirmatory"):
    cf = t / "cases.json"; cf.write_text(json.dumps([{"id": c, "summary": "a summary " + c} for c in cases]))
    human = t / "r0.json"; human.write_text(json.dumps({"classes": r0 or {c: 1 for c in cases}}))
    classify.http_json = fake_ollama(answers, models=models)
    with contextlib.redirect_stdout(io.StringIO()):
        out = classify.run(list(models), runs, cf, t / "out", human, mode)
    return out, human


class Parser(unittest.TestCase):
    def test_valid(self):
        for text, want in [('{"class": 3}', 3), ('{"class": "2", "reason": "x"}', 2), (' {"class": 4} \n', 4), ('{"class": 1, "reason": "class 4?"}', 1)]:
            self.assertEqual(classify.parse_answer(text), want, text)

    def test_invalid(self):
        for text in ['{"class": 12}', '{"class": 4.5}', '{"class": "1 or 4"}', '{"class": 0}', '{"class": 5}', '{"class": true}',
                     '{"class": 4.0}', '{"class": " 1"}', '{"class": null}', '{"klass": 1}', '[1]', '3', '',
                     'I think "class": 3 fits', 'Answer: {"class": 3}', '{"class": 3} and more', None]:
            self.assertIsNone(classify.parse_answer(text), repr(text))


class Summarise(unittest.TestCase):
    def a(self, *cls): return [{"class": c} for c in cls]

    def test_invalid_counted_and_unstable(self):
        s = classify.summarise(self.a(3, None, 3))
        self.assertEqual((s["n_invalid"], s["modal"], s["stable"], s["classes"]), (1, 3, False, [3, 3]))

    def test_all_invalid(self):
        s = classify.summarise(self.a(None, None, None))
        self.assertEqual((s["n_invalid"], s["modal"], s["stable"], s["tie"]), (3, None, False, False))

    def test_tie_is_none_regardless_of_order(self):
        for order in [(1, 4), (4, 1), (2, 3, None)]:
            s = classify.summarise(self.a(*order))
            self.assertEqual((s["modal"], s["tie"], s["stable"]), (None, True, False), order)

    def test_stable(self):
        s = classify.summarise(self.a(2, 2, 2))
        self.assertEqual((s["modal"], s["tie"], s["stable"], s["n_invalid"]), (2, False, True, 0))

    def test_ask_uses_strict_parser(self):
        classify.http_json = fake_ollama(['{"class": 12}'])
        r = classify.ask("m:1", {"summary": "x"}, 1)
        self.assertEqual((r["class"], r["valid"], r["raw"]), (None, False, '{"class": 12}'))


class Kappa(unittest.TestCase):
    def test_cohen_undefined(self):
        k, n = classify.cohen({"A": 4, "B": 4}, {"A": 4, "B": 4})
        self.assertIsNone(k); self.assertEqual(n, 2); self.assertEqual(classify.fmt(k), "undefined")

    def test_fleiss_undefined(self):
        self.assertIsNone(classify.fleiss({"A": [2, 2], "B": [2, 2]}))


class Agree(unittest.TestCase):
    def setUp(self): self.before = snapshot()
    def tearDown(self): self.assertEqual(snapshot(), self.before, "pilot files changed")

    def quiet(self, *a, **k):
        with contextlib.redirect_stdout(io.StringIO()): return classify.agree(*a, **k)

    def test_pilot_reproduces(self):
        r = self.quiet(HERE / "results", HERE / "human.json", write=False)
        c = r["cohen"]
        self.assertEqual(round(c["gemma4:26b-a4b-it-q8_0"], 3), 0.863)
        self.assertEqual(round(c["qwen3.8:27b-q8_0"], 3), 0.863)
        self.assertEqual(round(c["nemotron-3.5-lightning:30b-a3b-q4_K_M"], 2), 1.00)
        self.assertEqual(round(r["fleiss"], 2), 0.91); self.assertEqual(r["n_common"], 10); self.assertEqual(r["gaps"], {})

    def test_missing_case_refused(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            with confirmatory_env():
                out, human = make_run(t, answers=['{"class": 1}'] * 3 + ['no class here'] * 3 + ['{"class": 1}'] * 3 + ['no class here'] * 3,
                                      cases=["A", "B"], r0={"A": 1, "B": 2})
                with self.assertRaises(SystemExit) as e: self.quiet(out, human)
                self.assertIn("missing ['B']", str(e.exception.code))
                self.assertFalse((out / "agreement.md").exists())
                r = self.quiet(out, human, allow_missing=True)
                self.assertEqual(r["gaps"]["a:1"]["missing"], ["B"]); self.assertEqual(r["n_common"], 1)

    def test_no_manifest_outside_pilot_refused(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            (t / "human.json").write_text(json.dumps({"classes": {"A": 1}}))
            (t / "m.json").write_text(json.dumps({"model": "m", "cases": {"A": {"modal": 1}}}))
            with self.assertRaises(SystemExit) as e: self.quiet(t, t / "human.json")
            self.assertIn("no manifest", str(e.exception.code))
            with self.assertRaises(SystemExit) as e: self.quiet(t / "nope", t / "human.json")
            self.assertIn("no such run directory", str(e.exception.code))


class Run(unittest.TestCase):
    def setUp(self): self.before = snapshot()
    def tearDown(self): self.assertEqual(snapshot(), self.before, "pilot files changed")

    def cases(self, t):
        p = t / "cases.json"; p.write_text(json.dumps([{"id": "X1", "summary": "a sandbox escape"}, {"id": "X2", "summary": "a bad token"}])); return p

    def test_digest_none_aborts(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            classify.http_json = fake_ollama([], models=("other:1",))  # no chat answers: any ask() would raise StopIteration
            with self.assertRaises(SystemExit) as e: classify.run(["m:1"], 3, self.cases(t), t / "out")
            self.assertIn("no digest", str(e.exception.code)); self.assertFalse((t / "out").exists())

    def test_run_records_provenance_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); cases = self.cases(t)
            classify.http_json = fake_ollama(['{"class": 1}', '{"class": 12}', '{"class": 1}', '{"class": 2}', '{"class": 3}'])
            with contextlib.redirect_stdout(io.StringIO()): out = classify.run(["m:1"], 2, cases, t / "out")
            d = json.loads((out / "m_1.json").read_text())
            self.assertEqual(d["criteria_sha256"], hashlib.sha256(classify.CRITERIA.encode()).hexdigest())
            self.assertEqual(d["cases_sha256"], hashlib.sha256(cases.read_bytes()).hexdigest())
            for k in ("criteria", "digest", "started", "runs", "temperature"): self.assertIn(k, d)
            self.assertEqual((d["cases"]["X1"]["n_invalid"], d["cases"]["X1"]["modal"], d["cases"]["X1"]["stable"]), (1, 1, False))
            self.assertEqual((d["cases"]["X2"]["modal"], d["cases"]["X2"]["tie"]), (None, True))
            classify.http_json = fake_ollama(['{"class": 1}'] * 4)
            with self.assertRaises(SystemExit): classify.run(["m:1"], 2, cases, out)  # non-empty dir: refused

    def test_default_out_is_new_timestamped_dir(self):
        # Only the path is checked: HERE is redirected so nothing is created under the real results/.
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); here = classify.HERE; classify.HERE = t
            try:
                classify.http_json = fake_ollama(['{"class": 4}'] * 2)
                with contextlib.redirect_stdout(io.StringIO()): out = classify.run(["m:1"], 1, self.cases(t))
            finally: classify.HERE = here
            self.assertEqual(out.parent, t / "runs"); self.assertRegex(out.name, r"^run-\d{8}T\d{6}Z$")


class Manifest(unittest.TestCase):
    """A0: run manifest, R0 committed before models, frozen roster and digests, complete rater and case sets, valid classes."""
    def setUp(self): self.before = snapshot()
    def tearDown(self): self.assertEqual(snapshot(), self.before, "pilot files changed")

    def quiet(self, *a, **k):
        with contextlib.redirect_stdout(io.StringIO()): return classify.agree(*a, **k)

    def run_ok(self, t):
        return make_run(t, (['{"class": 1}'] * 3 + ['{"class": 3}'] * 3) * 2, r0={"X1": 1, "X2": 3})

    def test_manifest_written_and_complete(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            m = json.loads((out / "manifest.json").read_text())
            self.assertTrue(m["complete"]); self.assertEqual(m["mode"], "confirmatory"); self.assertEqual(m["case_ids"], ["X1", "X2"])
            self.assertEqual(m["r0_sha256"], hashlib.sha256(human.read_bytes()).hexdigest()); self.assertEqual(m["r0_commit"], "c0ffee")
            self.assertEqual(m["num_ctx"], classify.NUM_CTX)
            r = self.quiet(out, human, write=False)
            self.assertEqual(set(r["cohen"]), {"R0 human", "a:1", "b:1"})

    def test_confirmatory_needs_committed_valid_r0(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            t = pathlib.Path(t); cf = t / "c.json"; cf.write_text(json.dumps([{"id": "X1", "summary": "x"}]))
            classify.http_json = fake_ollama([], models=("a:1", "b:1"))
            with self.assertRaises(SystemExit) as e: classify.run(["a:1", "b:1"], 3, cf, t / "out", None, "confirmatory")
            self.assertIn("needs the R0 file", str(e.exception.code))
            (t / "r0.json").write_text(json.dumps({"classes": {}}))
            with self.assertRaises(SystemExit): classify.run(["a:1", "b:1"], 3, cf, t / "out", t / "r0.json", "confirmatory")
            (t / "r0.json").write_text(json.dumps({"classes": {"X1": "1"}}))
            with self.assertRaises(SystemExit) as e: classify.run(["a:1", "b:1"], 3, cf, t / "out", t / "r0.json", "confirmatory")
            self.assertIn("integers 1-4", str(e.exception.code))
            (t / "r0.json").write_text(json.dumps({"classes": {"X1": 1}}))
            classify.committed = lambda p: None
            with self.assertRaises(SystemExit) as e: classify.run(["a:1", "b:1"], 3, cf, t / "out", t / "r0.json", "confirmatory")
            self.assertIn("not committed", str(e.exception.code)); self.assertFalse((t / "out").exists())

    def test_roster_and_digests_enforced(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            t = pathlib.Path(t); cf = t / "c.json"; cf.write_text(json.dumps([{"id": "X1", "summary": "x"}]))
            (t / "r0.json").write_text(json.dumps({"classes": {"X1": 1}}))
            classify.http_json = fake_ollama([], models=("a:1", "b:1"))
            with self.assertRaises(SystemExit) as e: classify.run(["a:1"], 3, cf, t / "out", t / "r0.json", "confirmatory")
            self.assertIn("frozen roster", str(e.exception.code))
            classify.ROSTER = {"a:1": "1" * 64, "b:1": ZERO}
            with self.assertRaises(SystemExit) as e: classify.run(["a:1", "b:1"], 3, cf, t / "out", t / "r0.json", "confirmatory")
            self.assertIn("digest differs", str(e.exception.code)); self.assertFalse((t / "out").exists())

    def test_exploratory_run_not_read_as_confirmatory(self):
        with tempfile.TemporaryDirectory() as t:
            out, human = make_run(pathlib.Path(t), ['{"class": 1}'] * 4, mode="exploratory", runs=1)
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("not a confirmatory run", str(e.exception.code))
            self.quiet(out, human, write=False, allow_exploratory=True)

    def test_missing_model_file_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            (out / "b_1.json").unlink()
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("missing", str(e.exception.code))

    def test_unlisted_or_mismatched_file_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            d = json.loads((out / "a_1.json").read_text()); d["cases_sha256"] = "0" * 64
            (out / "a_1.json").write_text(json.dumps(d))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("provenance", str(e.exception.code))
            (out / "c_1.json").write_text(json.dumps({"model": "c:1", "cases": {}}))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("not in the manifest", str(e.exception.code))

    def test_incomplete_run_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            m = json.loads((out / "manifest.json").read_text()); m["complete"] = False
            (out / "manifest.json").write_text(json.dumps(m))
            with self.assertRaises(SystemExit): self.quiet(out, human, write=False)

    def test_r0_changed_after_run_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            human.write_text(json.dumps({"classes": {"X1": 4, "X2": 3}}))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("R0 file differs", str(e.exception.code))

    def test_extra_or_foreign_cases_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            d = json.loads((out / "a_1.json").read_text()); d["cases"]["X9"] = {"modal": 1}
            (out / "a_1.json").write_text(json.dumps(d))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False, allow_missing=True)
            self.assertIn("case ids", str(e.exception.code))

    def test_duplicate_and_invalid_case_ids_refused(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t)
            for cases in ([], [{"id": "X1", "summary": "a"}, {"id": "X1", "summary": "b"}], [{"id": "bad id", "summary": "a"}],
                          [{"id": "X1", "summary": " "}]):
                cf = t / "c.json"; cf.write_text(json.dumps(cases))
                with self.assertRaises(SystemExit): classify.run(["a:1"], 1, cf, t / "out")
            self.assertFalse((t / "out").exists())

    def test_duplicate_model_refused(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); cf = t / "c.json"; cf.write_text(json.dumps([{"id": "X1", "summary": "x"}]))
            with self.assertRaises(SystemExit): classify.run(["a:1", "a:1"], 1, cf, t / "out")

    def test_exclude_model(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            r = self.quiet(out, human, write=True, exclude=("b:1",))
            self.assertEqual(set(r["cohen"]), {"R0 human", "a:1"})
            self.assertTrue((out / "agreement-without-b.md").exists())

    def test_truncated_prompt_aborts(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); cf = t / "c.json"; cf.write_text(json.dumps([{"id": "X1", "summary": "x"}]))
            def http_json(path, body=None, timeout=60):
                if path == "/api/tags": return {"models": [{"name": "a:1", "digest": "sha256:" + ZERO}]}
                return {"message": {"content": '{"class": 1}'}, "prompt_eval_count": classify.NUM_CTX}
            classify.http_json = http_json
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e:
                classify.run(["a:1"], 1, cf, t / "out")
            self.assertIn("num_ctx", str(e.exception.code)); self.assertFalse((t / "out" / "a_1.json").exists())

    def test_confirmatory_needs_three_runs(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            t = pathlib.Path(t); cf = t / "c.json"; cf.write_text(json.dumps([{"id": "X1", "summary": "x"}]))
            (t / "r0.json").write_text(json.dumps({"classes": {"X1": 1}}))
            for runs in (1, 2, 4):
                with self.assertRaises(SystemExit) as e: classify.run(["a:1", "b:1"], runs, cf, t / "out", t / "r0.json", "confirmatory")
                self.assertIn("exactly 3 runs", str(e.exception.code))
            for runs in (0, -1):
                with self.assertRaises(SystemExit): classify.run(["a:1"], runs, cf, t / "out")
            self.assertFalse((t / "out").exists())

    def test_short_or_one_run_result_refused(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            out, human = self.run_ok(pathlib.Path(t))
            d = json.loads((out / "a_1.json").read_text()); d["cases"]["X1"]["answers"].pop()
            (out / "a_1.json").write_text(json.dumps(d))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("without 3 answers", str(e.exception.code))
            m = json.loads((out / "manifest.json").read_text()); m["runs"] = 1
            (out / "manifest.json").write_text(json.dumps(m))
            with self.assertRaises(SystemExit) as e: self.quiet(out, human, write=False)
            self.assertIn("3 runs per case", str(e.exception.code))

    def test_digest_change_during_run_aborts(self):
        with tempfile.TemporaryDirectory() as t:
            t = pathlib.Path(t); cf = t / "c.json"
            cf.write_text(json.dumps([{"id": "X1", "summary": "x"}, {"id": "X2", "summary": "y"}]))
            calls = {"tags": 0}
            def http_json(path, body=None, timeout=60):
                if path == "/api/tags":
                    calls["tags"] += 1  # first answer is the preflight; the tag is re-pulled after the first case
                    return {"models": [{"name": "a:1", "digest": "sha256:" + (ZERO if calls["tags"] == 1 else "1" * 64)}]}
                return {"message": {"content": '{"class": 1}'}, "prompt_eval_count": 100}
            classify.http_json = http_json
            with contextlib.redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as e:
                classify.run(["a:1"], 1, cf, t / "out")
            self.assertIn("changed during the run", str(e.exception.code))
            self.assertFalse((t / "out" / "a_1.json").exists())
            self.assertFalse(json.loads((t / "out" / "manifest.json").read_text())["complete"])

    def test_r0_nonresponse_null_outside_the_case_set(self):
        with tempfile.TemporaryDirectory() as t, confirmatory_env():
            t = pathlib.Path(t)
            out, human = make_run(t, (['{"class": 1}'] * 3 + ['{"class": 3}'] * 3) * 2, r0={"X1": 1, "X2": 3, "X9": None})
            r = self.quiet(out, human, write=False)
            self.assertEqual(r["r0_nonresponse"], ["X9"]); self.assertEqual(set(r["cohen"]), {"R0 human", "a:1", "b:1"})
            (t / "r2.json").write_text(json.dumps({"classes": {"X1": 1, "X2": None}}))
            with self.assertRaises(SystemExit): classify.load_r0(t / "r2.json", ["X1", "X2"])  # null inside the case set
            (t / "r3.json").write_text(json.dumps({"classes": {"X1": "1"}}))
            with self.assertRaises(SystemExit): classify.load_r0(t / "r3.json")  # non-null labels still integers 1-4
            (t / "r4.json").write_text(json.dumps({"classes": {"X1": None}}))
            with self.assertRaises(SystemExit): classify.load_r0(t / "r4.json")  # nothing labelled

    def test_frozen_roster(self):
        self.assertEqual(set(classify.ROSTER), set(classify.DEFAULT_MODELS))
        self.assertTrue(classify.ROSTER["gemma4:26b-a4b-it-q8_0"].startswith("7473a33e49f1"))  # D43
        self.assertTrue(classify.ROSTER["qwen3.8:27b-q8_0"].startswith("8f5fb6b71ea0"))
        self.assertTrue(classify.ROSTER["nemotron-3.5-lightning:30b-a3b-q4_K_M"].startswith("e7a64ff15fb1"))

    def test_criteria_have_bundle_rule(self):
        self.assertIn("If the disclosure bundles several", classify.CRITERIA)
        self.assertIn("D41", classify.CRITERIA_VERSION)


if __name__ == "__main__":
    unittest.main(verbosity=2)
