#!/usr/bin/env python3
"""Re-run, from the committed evidence, every scripted analysis behind the paper's figures, and check that each regenerated
output equals the committed one. The analyses are offline and read-only: outputs go to a temporary directory; no client, VM,
model, network call or write to $HOME. Needs Python >= 3.11 and Node >= 22 (tests only). Runs from a git clone or from a release
archive without .git. RQ1 reads its frozen inputs from the frame commit; without git history it reads them from the working
tree and accepts each only if its SHA-256 equals the hash recorded in rq1-sample-manifest.json. That manifest records the frame
and the sampler but not estimate.py, whose binding to the frame commit (D44) therefore needs the git history: without it the
RQ1 primary and D51 analyses stop (fail closed): the two analyses and their four output checks are reported as
failed. Every other check runs the same way in both settings.

Every line carries one of three labels:
  [recomputed from public data]  the output is regenerated here from files in this tree and compared with the committed output;
  [compared with a saved result] the check cannot regenerate a value and compares with one saved at the time (the RQ1 sample
                                 check trusts the stored drand value offline);
  [needs private data]           not run here: the inputs are private (listed at the end of the run; nothing is compared).

    python3 reproduce.py            # analyses only
    python3 reproduce.py --tests    # also every test suite (stubs only)

Compared byte for byte, except where a field records where or from what the original ran (each exception is named below):
RQ1 JSONs without "run_dir" (absolute path of the original run); RQ3 matrix.csv without the "dir" column (absolute paths of the
original lab); RQ4 coverage.json without "inputs_sha256" (hashes of the full private readings; the published CSVs are filtered
to the six servers). RQ2's summary takes the first run without its Codex rows (evidence/q5-run/NOTES.md).

Not covered: figures the paper reads directly from evidence tables rather than from an analysis script, namely the RQ2
current-version re-checks (evidence/q5-run/recheck-20261009/, including Gemini CLI 0.63.0), the RQ2 non-interactive and graphical
cells, and the RQ3 graphical clients (gui-20261017/); each has its own README with the counts and the files they come from.
Also read by hand rather than by a script: the composition of the RQ1 flags (rq1-flags.json reasons), the empty Gemma answers
(raw run files), run times, the pilot share, which answer each client pre-selects (captures, Appendix B) and log retention
(telemetry/inventory/sources.md).

The test suites (--tests) also run stubs only, with two declared exceptions: some tests run lab scripts (e.g. prepare_vm.py)
against a temporary HOME, and the open-weight proxy tests exchange HTTP with themselves on 127.0.0.1. Node suites are run with
node directly (no npm, which would write logs under $HOME), on a temporary copy of the tree.

Not regenerable here, by design: model-rater answers (need the models), human labels and codings, client captures (need the VM
and the clients), RQ5 inputs (need private log archives). SHA-256 manifests exist for the RQ1 advisory-query inputs, the RQ2 evidence
(environment.json) and the RQ3 evidence (SHA256SUMS); the private RQ5 archives are not hashed, except the second rule author's package.
"""
import csv, io, json, os, pathlib, shutil, subprocess, sys, tempfile

ROOT = pathlib.Path(__file__).resolve().parent
PY = [sys.executable, "-I", "-B"]
RUN = "preregistration/runs/rq1-confirmatory-20261027T142818Z"
RQ1_OUT = RUN + "-rq1-analysis"
Q3 = "tool-change/evidence/primary-20261015"
Q4 = "defence-coverage/results-20261024"
Q5 = "telemetry/evidence/scores-20261024"
Q2 = "trusting-a-repo/evidence/q5-run"


def sh(cmd, cwd=ROOT, stdin=None):
    r = subprocess.run(cmd, cwd=cwd, input=stdin, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    if r.returncode:
        raise RuntimeError(f"{' '.join(map(str, cmd))} exited {r.returncode}: {r.stderr.decode()[-800:]}")
    return r.stdout


def drop_key(key):
    def norm(b):
        d = json.loads(b)
        d.pop(key, None)
        return json.dumps(d, sort_keys=True)
    return norm


def drop_column(col):
    def norm(b):
        rows = list(csv.DictReader(io.StringIO(b.decode())))
        return [{k: v for k, v in r.items() if k != col} for r in rows]
    return norm


def q2_input():
    """Run 1 without its Codex rows (excluded, NOTES.md), with the run's own header and row format."""
    src = (ROOT / Q2 / "20261009-194314" / "matrix.csv").read_text()
    rows = list(csv.DictReader(io.StringIO(src)))
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=list(rows[0]), lineterminator="\r\n" if "\r\n" in src else "\n")
    w.writeheader()
    w.writerows(r for r in rows if r["client"] != "codex")
    return out.getvalue().encode()


PUBLIC, SAVED, PRIVATE = "recomputed from public data", "compared with a saved result", "needs private data"
NEEDS_PRIVATE = [  # printed, not run: each needs data that is not in this tree
    ("RQ4", "full readings behind coverage.json \"inputs_sha256\" (the published CSVs are filtered to the six published servers)"),
    ("RQ5", "the score inputs (input-*.json) themselves, extracted from the private log archives"),
]
FRAME_COMMIT = "e62676b31d12690365d67033aeed2fb09df9c78e"  # rq1-sample-manifest.json frame_commit


def has_history():
    """True when this tree is a git checkout that holds the RQ1 frame commit."""
    try:
        return subprocess.run(["git", "-C", str(ROOT), "cat-file", "-e", FRAME_COMMIT + "^{commit}"],
                              capture_output=True).returncode == 0
    except OSError:
        return False


def checks(tmp):
    """(RQ, label, committed file, function returning regenerated bytes, normaliser or None)."""
    t = pathlib.Path(tmp)
    rq1 = lambda name: lambda: (t / "rq1" / name).read_bytes()
    q3 = lambda name: lambda: (t / "q3" / name).read_bytes()
    q4 = lambda name: lambda: (t / "q4" / name).read_bytes()
    q2 = t / "q2.csv"
    return [
        ("RQ1", "primary analysis (JSON)", f"{RQ1_OUT}/RESULTS-RQ1.json", rq1("RESULTS-RQ1.json"), drop_key("run_dir")),
        ("RQ1", "primary analysis (report)", f"{RQ1_OUT}/RESULTS-RQ1.md", rq1("RESULTS-RQ1.md"), None),
        ("RQ1", "disagreement, exploratory D51 (JSON)", f"{RQ1_OUT}/EXPLORATORY-DISAGREEMENT.json",
         rq1("EXPLORATORY-DISAGREEMENT.json"), drop_key("run_dir")),
        ("RQ1", "disagreement, exploratory D51 (report)", f"{RQ1_OUT}/EXPLORATORY-DISAGREEMENT.md",
         rq1("EXPLORATORY-DISAGREEMENT.md"), None),
        ("RQ1", "provenance of R0's labels", f"{RQ1_OUT}/R0-PROVENANCE.txt",
         lambda: sh(PY + ["preregistration/rq1/r0_report.py"]), None),
        ("RQ2", "matrix summary", "trusting-a-repo/evidence/q5-summary.md",
         lambda: sh(PY + ["trusting-a-repo/scripts/summarize_matrix.py", str(q2), f"{Q2}/20261009-200610/matrix.csv"]), None),
        ("RQ3", "primary analysis", f"{Q3}/analysis/analysis.json", q3("analysis.json"), None),
        ("RQ3", "primary matrix", f"{Q3}/analysis/matrix.csv", q3("matrix.csv"), drop_column("dir")),
        ("RQ3", "preregistered coder agreement", f"{Q3}/coding/agreement.json",
         lambda: sh(PY + ["tool-change/scripts/agreement_q3.py", f"{Q3}/coding/coding-sheet.csv", f"{Q3}/coding/llm/llm-coding.csv",
                          f"{Q3}/coding/key.csv", Q3]), None),
        ("RQ3", "three-coder agreement", f"{Q3}/coding/codex/agreement-three.json", lambda: (t / "agreement-three.json").read_bytes(), None),
        ("RQ3", "positive control, exploratory D52", "tool-change/evidence/positive-control-20261028/coded.csv",
         lambda: (t / "pc-coded.csv").read_bytes(), drop_column("dir")),
        ("RQ3", "open-weight cells, exploratory D39", "tool-change/evidence/open-weight-20261024/RESULTS.json",
         lambda: sh(PY + ["tool-change/scripts/analyze_open_weight.py", "tool-change/evidence/open-weight-20261024"]), None),
        ("RQ4", "final census", f"{Q4}/final-census.csv", q4("final-census.csv"), None),
        ("RQ4", "coverage (JSON)", f"{Q4}/coverage.json", q4("coverage.json"), drop_key("inputs_sha256")),
        ("RQ4", "coverage (report)", f"{Q4}/COVERAGE.md", q4("COVERAGE.md"), None),
        *[("RQ5", f"scores, {who}", f"{Q5}/scores-{who}.json",
           (lambda w: lambda: sh(PY + ["telemetry/scripts/score.py", f"{Q5}/input-{w}.json"]))(who), None)
          for who in ("author", "second-author", "host")],
        *[("RQ5", f"H5 verdict, {who}", f"{Q5}/h5-{who}.json",
           (lambda w: lambda: sh(PY + ["telemetry/rules/h5.py", f"{Q5}/scores-{w}.json", f"{Q5}/input-{w}.json"]))(who), None)
          for who in ("author", "second-author")],
        ("RQ5", "agreement of the two rule authors", f"{Q5}/agreement.json",
         lambda: sh(PY + ["telemetry/rules/agreement.py", f"{Q5}/h5-author.json", f"{Q5}/h5-second-author.json"]), None),
    ]


def prepare(tmp):
    """Analyses that write files: run each once into tmp. Returns the analyses that failed, so the other checks still run (the
    checks that read a failed analysis's output then fail too)."""
    t = pathlib.Path(tmp)
    pc = sorted(str(p.relative_to(ROOT)) for p in (ROOT / "tool-change/evidence/positive-control-20261028").glob("*__name__r1"))
    steps = [
        ("RQ1 primary analysis", lambda: sh(PY + ["preregistration/rq1/analyze.py", RUN, str(t / "rq1")])),
        ("RQ1 disagreement analysis", lambda: sh(PY + ["preregistration/rq1/explore_disagreement.py", RUN, str(t / "rq1")])),
        ("RQ2 input", lambda: (t / "q2.csv").write_bytes(q2_input())),
        ("RQ3 primary analysis", lambda: sh(PY + ["tool-change/scripts/analyze_q3.py", Q3, "--out", str(t / "q3")])),
        ("RQ3 three-coder agreement", lambda: sh(PY + [str(ROOT / "tool-change/scripts/agreement_q3_three.py"), "--key", "key.csv",
             "--author", "coding-sheet.csv", "--local", "llm/llm-coding.csv", "--codex", "codex/codex-coding.csv",
             "--disagreements", "disagreements-resolved.csv", "--out", str(t / "agreement-three.json")], cwd=ROOT / Q3 / "coding")),
        ("RQ3 positive control", lambda: sh(PY + ["tool-change/scripts/code_q3.py", *pc, "--csv", str(t / "pc-coded.csv")])),
        ("RQ4 final census", lambda: sh(PY + ["defence-coverage/scripts/final_census.py", "--first", f"{Q4}/first-reading.csv",
             "--second", f"{Q4}/second-reading.csv", "--adjudication", f"{Q4}/adjudication.csv", "--servers",
             "azure-devops-mcp,github-mcp-server,sentry-mcp,aws-iac-mcp-server,mssql-mcp-server,oracle-mcp-server",
             "--out", str(t / "q4")])),
    ]
    failed = []
    for label, step in steps:
        try:
            step()
        except (RuntimeError, OSError) as e:
            failed.append((label, str(e).strip().splitlines()[-1] if str(e).strip() else repr(e)))
    return failed


TESTS = [  # (label, command, working directory); every suite runs on stubs and temporary directories only
    ("RQ1 (Python)", PY + ["-m", "unittest", "discover", "-s", "preregistration/test"], ""),
    ("RQ2 (Node)", "node-tests", "trusting-a-repo"),
    ("RQ3 (Node)", "node-tests", "tool-change"),
    ("RQ3 open-weight (Python)", PY + ["-m", "unittest", "discover", "-s", "test", "-p", "test_*.py"], "tool-change"),
    ("RQ4 (Python)", PY + ["-m", "unittest", "discover", "-s", "defence-coverage/test"], ""),
    ("RQ5 (Python)", PY + ["-m", "unittest", "discover", "-s", "telemetry/test"], ""),
]


def main(argv):
    failed = 0
    history = has_history()
    print("git history with the RQ1 frame commit: " + ("yes" if history else "no (release archive or shallow copy)"))
    with tempfile.TemporaryDirectory(prefix="reproduce-") as tmp:
        for step, why in prepare(tmp):
            failed += 1
            print(f"FAIL [{PUBLIC}] analysis did not run: {step} ({why})")
        for rq, label, committed, regen, norm in checks(tmp):
            status = None
            try:
                new, old = regen(), (ROOT / committed).read_bytes()
                same = (norm(new) == norm(old)) if norm else new == old
            except (RuntimeError, OSError, ValueError) as e:
                same, status, label = False, "FAIL", f"{label} ({str(e).strip().splitlines()[-1] if str(e).strip() else e})"
            failed += not same
            status = status or ("OK  " if same else "DIFF")
            print(f"{status} [{PUBLIC}] {rq}  {label}  [{committed}]{'  (normalised)' if norm and same else ''}")
    # the frozen frame, seed and sample recomputed (offline: the stored beacon value is trusted). With git history from the frame
    # commit (sample_frame.py verify); without it, from the working-tree frame accepted by its recorded hash (verify_archive.py)
    script, done = (("draw_gzip_safe.py", "sample verified") if history else ("verify_archive.py", "sample verified from the archive"))
    try:
        ok = done in sh(PY + [f"preregistration/rq1/{script}", "verify"] if history else PY + [f"preregistration/rq1/{script}"]).decode()
    except RuntimeError:
        ok = False
    failed += not ok
    print(f"{'OK  ' if ok else 'FAIL'} [{SAVED}] RQ1  frame hash, seed and sample of 120 (offline; drand value as stored; "
          f"frame {'from the frame commit' if history else 'from the working tree, accepted by its recorded SHA-256'})")
    for rq, what in NEEDS_PRIVATE:
        print(f"--   [{PRIVATE}] {rq}  {what}")
    if "--tests" in argv:
        with tempfile.TemporaryDirectory(prefix="reproduce-tests-") as ttmp:
            tree = pathlib.Path(ttmp) / "tree"  # suites run on a copy, so nothing they or their subprocesses write lands here
            shutil.copytree(ROOT, tree, ignore=shutil.ignore_patterns(".git", "__pycache__", "node_modules"))
            failed += run_tests(tree)
    print("all regenerated outputs equal the committed ones" if not failed else f"{failed} check(s) failed")
    return 1 if failed else 0


def run_tests(tree):
    failed = 0
    for label, cmd, cwd in TESTS:
        if cmd == "node-tests":  # the package.json "test" script, without npm
            cmd = ["node", "--test", "--test-concurrency=1", *sorted(str(p.relative_to(tree / cwd))
                                                                     for p in (tree / cwd / "test").glob("*.test.mjs"))]
        r = subprocess.run(cmd, cwd=tree / cwd, capture_output=True, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
        failed += r.returncode != 0
        print(f"{'OK  ' if r.returncode == 0 else 'FAIL'} tests {label}")
    return failed


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
