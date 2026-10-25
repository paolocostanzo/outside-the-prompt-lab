#!/usr/bin/env python3
"""RQ1 model raters (local Ollama) and agreement with the author's labels (R0). Canonical copy (deviations D4, D14 point 4, D41, D42, D43).

Usage (GPU instance on, Ollama reachable at 127.0.0.1:11434 through `infra/ai-lab.sh tunnel`):
    python3 preregistration/classify.py run    --cases CASES.json [--r0 rq1-r0.json] [--models a,b,c] [--runs 3] [--out DIR]
    python3 preregistration/classify.py agree  --results DIR [--human R0.json] [--exclude MODEL] [--allow-missing]

`run` writes, in a new directory (never overwriting): `manifest.json` (models and their digests, hashes of the cases, the criteria
and — for a confirmatory run — the committed R0 file, run configuration) and one `<model>.json` per model (every answer, raw text,
modal class, prompt size). A confirmatory run (`--r0`) refuses to start unless the R0 file exists: the author's labels come first
(D3, D42 point 4). `agree` reads a run directory: with a manifest it requires every listed model, exactly once, with the manifest's
digest, cases and criteria; without a manifest (the pilot of 10 Oct 2026, run before manifests existed) it reads the files present.
No dependencies beyond the standard library.
"""
import argparse, json, re, subprocess, sys, urllib.request, collections, datetime, pathlib, hashlib

HERE = pathlib.Path(__file__).resolve().parent
PILOT = HERE / "pilot"
OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODELS = ["qwen3.8:27b-q8_0", "gemma4:26b-a4b-it-q8_0", "nemotron-3.5-lightning:30b-a3b-q4_K_M"]
# Frozen roster of the confirmatory run: R1–R3 and their approved digests (preregistration section 4; R2 replaced by D43).
ROSTER = {
    "qwen3.8:27b-q8_0": "8f5fb6b71ea00052cbe8545738c55ce61112c4e571cb60ca4dad00b131766039",
    "gemma4:26b-a4b-it-q8_0": "7473a33e49f186a27812ba7cb434b2b2b26e377714ad49f9abe9cdd7089ac4f7",
    "nemotron-3.5-lightning:30b-a3b-q4_K_M": "e7a64ff15fb174c42b4f463e5c888c4f2c7b9cabf9e8d65a1c0874405426c1b2",
}
CONFIRMATORY_RUNS = 3  # preregistration §4: three runs per case, seeds 1-3
MODES = ("confirmatory", "exploratory")  # exploratory: timing checks, the pilot, secondary runs; never confirmatory agreement
CASE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")
TEMPERATURE = 0
NUM_CTX = 16384  # explicit context window: Ollama's default is small and truncates silently
CTX_MARGIN = 512  # answer room; a prompt larger than NUM_CTX - CTX_MARGIN aborts the run

CRITERIA = """You are classifying a public security disclosure about an AI agent or one of its connectors.
Assign exactly one class by trigger point:
1. Before trust - runs at startup or before the user's trust decision. Includes flaws in the agent's own startup and execution
   machinery (sandbox boundaries, background tool invocations, path resolution) that let repository content run code without
   any user or model decision.
2. Interaction layer - the approval or confirmation step misrepresents or skips what happens.
3. Plumbing - classic authentication, authorization or origin flaws in the services around the agent: MCP servers, SDKs,
   connectors, bridges.
4. Authority - the model is manipulated; the impact is set by the privileges it holds.
Decision rule: if the attack only works because the model follows instructions it should not have trusted, the case is
class 4, whatever the delivery channel. Otherwise, the case goes to the earliest step that fails without any model decision:
before the trust decision (1), in what the user is shown or asked to approve (2), or in the authentication and authorization
of the services around the agent (3).
Counting rule: one disclosure is one case, regardless of how many findings it bundles. If the disclosure bundles several
findings, apply the decision rule across them: if at least one finding works without the model following instructions it should
not have trusted, give the earliest of classes 1-3 among those findings; give class 4 only if every finding needs the model to
follow such instructions.
Answer with one JSON object only: {"class": <1|2|3|4>, "confidence": <0-1>, "reason": "<one sentence>"}"""
CRITERIA_VERSION = "v3 (preregistration v2 + bundle sentence of D41 point 1, 25 Oct 2026)"
CRITERIA_SHA256 = hashlib.sha256(CRITERIA.encode()).hexdigest()
# Preregistration section 3; whole-word match, so "classic" does not trip it.
CLASS_WORDS = ["before trust", "approval", "injection", "authority", "plumbing", "class"]


def sha256_file(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def bare(d):
    return (d or "").removeprefix("sha256:")


def validate_cases(cases):
    """A non-empty list of {id, summary} with unique, well-formed ids; returns the id list."""
    if not isinstance(cases, list) or not cases:
        sys.exit("no cases")
    ids = [c.get("id") for c in cases]
    if bad := [i for i in ids if not isinstance(i, str) or not CASE_ID.match(i)]:
        sys.exit(f"invalid case ids: {bad[:10]}")
    if dup := sorted({i for i in ids if ids.count(i) > 1}):
        sys.exit(f"duplicate case ids: {dup[:10]}")
    if empty := [c["id"] for c in cases if not isinstance(c.get("summary"), str) or not c["summary"].strip()]:
        sys.exit(f"cases without a summary: {empty[:10]}")
    return ids


def load_r0(path, case_ids=None):
    """R0 labels: {"classes": {id: 1..4}}, every class an integer 1-4, ids exactly the case set when given."""
    d = json.loads(pathlib.Path(path).read_text())
    cl = d.get("classes") if isinstance(d, dict) else None
    if not isinstance(cl, dict) or not cl:
        sys.exit(f"{path}: no R0 classes")
    if bad := sorted(k for k, v in cl.items() if type(v) is not int or not 1 <= v <= 4):
        sys.exit(f"{path}: R0 classes must be integers 1-4: {bad[:10]}")
    if case_ids is not None and set(cl) != set(case_ids):
        sys.exit(f"{path}: R0 cases differ from the case set (missing {sorted(set(case_ids) - set(cl))[:10]}, "
                 f"extra {sorted(set(cl) - set(case_ids))[:10]})")
    return cl


def committed(path):
    """Commit of `path` if it is tracked and unchanged since that commit, else None (R0 must be committed before the run)."""
    path = pathlib.Path(path).resolve()
    try:
        top = subprocess.run(["git", "-C", str(path.parent), "rev-parse", "--show-toplevel"], capture_output=True, text=True, check=True).stdout.strip()
        rel = str(path.relative_to(top))
        subprocess.run(["git", "-C", top, "ls-files", "--error-unmatch", rel], capture_output=True, check=True)
        if subprocess.run(["git", "-C", top, "diff", "--quiet", "HEAD", "--", rel]).returncode != 0:
            return None
        return subprocess.run(["git", "-C", top, "log", "-1", "--format=%H", "--", rel], capture_output=True, text=True, check=True).stdout.strip() or None
    except (subprocess.CalledProcessError, ValueError):
        return None


def leak_check(cases):
    """Refuse to run if a case summary contains a class word (preregistration section 3)."""
    bad = [(c["id"], w) for c in cases for w in CLASS_WORDS
           if re.search(r"\b" + re.escape(w) + r"(es)?\b", c["summary"].lower())]
    if bad:
        sys.exit(f"class-word leak in summaries: {bad}")


def http_json(path, body=None, timeout=60):
    """The only network call: GET (body None) or POST JSON to the local Ollama. Tests monkeypatch this."""
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(OLLAMA + path, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.load(r)


def parse_answer(text):
    """Strict: the whole answer must be one JSON object whose "class" is the int 1-4 or the string "1".."4".
    Anything else ("12", 4.5, "1 or 4", prose around the JSON, true) is invalid and returns None."""
    try: d = json.loads(text)
    except (ValueError, TypeError): return None
    if not isinstance(d, dict): return None
    v = d.get("class")
    if type(v) is int and 1 <= v <= 4: return v  # type(), not isinstance: rejects True/False
    if isinstance(v, str) and v in ("1", "2", "3", "4"): return int(v)
    return None


class Truncated(Exception):
    pass


def ask(model, case, seed):
    body = {"model": model, "stream": False, "format": "json",
            "options": {"temperature": TEMPERATURE, "seed": seed, "num_ctx": NUM_CTX},
            "messages": [{"role": "system", "content": CRITERIA},
                         {"role": "user", "content": f"Summary: {case['summary']}"}]}  # summary only (preregistration section 4; D4)
    d = http_json("/api/chat", body, timeout=1800)
    prompt_tokens = d.get("prompt_eval_count")
    if prompt_tokens is None or prompt_tokens > NUM_CTX - CTX_MARGIN:
        raise Truncated(f"{case['id']}: prompt of {prompt_tokens} tokens against num_ctx {NUM_CTX}")
    text = d["message"]["content"]
    cls = parse_answer(text)
    return {"raw": text, "class": cls, "valid": cls is not None, "eval_count": d.get("eval_count"),
            "prompt_tokens": prompt_tokens}


def model_digest(model):
    """Full sha256 of the local model, from /api/tags (the 12-character id in the preregistration is its prefix)."""
    tags = http_json("/api/tags")["models"]
    return next((m["digest"] for m in tags if m["name"] == model), None)


def modal_class(classes):
    """Most frequent class, or (None, True) on a tie for the top count; never depends on answer order."""
    top = collections.Counter(classes).most_common()
    if not top: return None, False
    if len(top) > 1 and top[0][1] == top[1][1]: return None, True
    return top[0][0], False


def summarise(answers):
    classes = [a["class"] for a in answers if a["class"] is not None]
    n_invalid = len(answers) - len(classes)
    modal, tie = modal_class(classes)
    return {"answers": answers, "classes": classes, "n_invalid": n_invalid, "modal": modal, "tie": tie,
            "stable": n_invalid == 0 and len(set(classes)) == 1}


def out_name(model):
    return model.replace(":", "_").replace("/", "_") + ".json"


def run(models, runs, cases_file=PILOT / "cases.json", out=None, r0=None, mode="exploratory"):
    if mode not in MODES:
        sys.exit(f"mode must be one of {MODES}")
    if len(set(models)) != len(models):
        sys.exit(f"duplicate model in {models}")
    if type(runs) is not int or runs < 1:
        sys.exit("runs must be a positive integer")
    if mode == "confirmatory" and runs != CONFIRMATORY_RUNS:
        sys.exit(f"a confirmatory run has exactly {CONFIRMATORY_RUNS} runs per case (seeds 1-{CONFIRMATORY_RUNS})")
    cases_file = pathlib.Path(cases_file); raw = cases_file.read_bytes()
    cases = json.loads(raw); case_ids = validate_cases(cases); leak_check(cases)
    r0_commit = None
    if mode == "confirmatory":
        if sorted(models) != sorted(ROSTER):
            sys.exit(f"a confirmatory run uses exactly the frozen roster {sorted(ROSTER)}")
        if r0 is None or not pathlib.Path(r0).is_file():
            sys.exit("a confirmatory run needs the R0 file: the author's labels are committed before any model run (D3, D42)")
        load_r0(r0, case_ids)
        r0_commit = committed(r0)
        if not r0_commit:
            sys.exit(f"{r0}: not committed, or changed since its last commit; commit it before any model run")
    # Digests first: a model without one aborts the whole run before anything is asked or written.
    digests = {m: model_digest(m) for m in models}
    if missing := [m for m, d in digests.items() if not d]:
        sys.exit(f"no digest from {OLLAMA}/api/tags for {missing}: model not pulled or name wrong; aborting")
    if mode == "confirmatory" and (wrong := [m for m in models if bare(digests[m]) != ROSTER[m]]):
        sys.exit(f"digest differs from the frozen roster for {wrong}: the model behind the tag changed; aborting")
    started = datetime.datetime.now(datetime.timezone.utc)
    out = pathlib.Path(out) if out else HERE / "runs" / ("run-" + started.strftime("%Y%m%dT%H%M%SZ"))
    if out.exists() and any(out.iterdir()):
        sys.exit(f"refusing to write into non-empty {out}")
    out.mkdir(parents=True, exist_ok=True)
    manifest = {"models": [{"name": m, "digest": digests[m], "file": out_name(m)} for m in models],
                "criteria": CRITERIA_VERSION, "criteria_sha256": CRITERIA_SHA256,
                "mode": mode, "case_ids": case_ids,
                "cases_file": cases_file.name, "cases_sha256": hashlib.sha256(raw).hexdigest(), "n_cases": len(cases),
                "r0_file": pathlib.Path(r0).name if r0 else None, "r0_sha256": sha256_file(r0) if r0 else None,
                "r0_commit": r0_commit,
                "runs": runs, "temperature": TEMPERATURE, "num_ctx": NUM_CTX,
                "started": started.isoformat(timespec="seconds"), "complete": False}
    with open(out / "manifest.json", "x") as f:
        f.write(json.dumps(manifest, indent=2))
    for model in models:
        res = {"model": model, "digest": digests[model], "criteria": CRITERIA_VERSION, "criteria_sha256": CRITERIA_SHA256,
               "cases_file": cases_file.name, "cases_sha256": manifest["cases_sha256"],
               "started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
               "runs": runs, "temperature": TEMPERATURE, "num_ctx": NUM_CTX, "cases": {}}
        for c in cases:
            try:
                answers = [ask(model, c, seed) for seed in range(1, runs + 1)]
            except Truncated as e:
                sys.exit(f"aborting: {e}; nothing is written for {model}")
            if (now := model_digest(model)) != digests[model]:  # the tag is mutable: a pull during the run would change the build
                sys.exit(f"aborting: digest of {model} changed during the run ({bare(digests[model])[:12]} -> {bare(now)[:12]}); "
                         f"nothing is written for {model}")
            s = res["cases"][c["id"]] = summarise(answers)
            print(f"{model:40} {c['id']} -> {s['classes']} invalid={s['n_invalid']} modal={s['modal']}"
                  + (" TIE" if s["tie"] else ""), flush=True)
        with open(out / out_name(model), "x") as f:  # "x": fail rather than overwrite
            f.write(json.dumps(res, indent=2, ensure_ascii=False))
    if changed := [m for m in models if model_digest(m) != digests[m]]:
        sys.exit(f"aborting: digest changed before completion for {changed}; the run stays incomplete")
    manifest["complete"] = True
    manifest["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    (out / "manifest.json").write_text(json.dumps(manifest, indent=2))
    print(f"results in {out}")
    return out


def cohen(a, b):
    """Cohen's kappa on the cases both raters classified; None (undefined) when pe == 1 or there are no cases."""
    keys = [k for k in a if k in b and a[k] and b[k]]
    n = len(keys)
    if n == 0: return None, 0
    po = sum(a[k] == b[k] for k in keys) / n
    ca, cb = collections.Counter(a[k] for k in keys), collections.Counter(b[k] for k in keys)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    return ((po - pe) / (1 - pe) if pe < 1 else None), n


def fleiss(ratings):  # ratings: dict case -> list of classes (one per rater); None (undefined) when pe == 1
    cats = [1, 2, 3, 4]; N = len(ratings); n = len(next(iter(ratings.values())))
    P = []; pj = collections.Counter()
    for r in ratings.values():
        cnt = collections.Counter(r); pj.update(cnt)
        P.append((sum(v * v for v in cnt.values()) - n) / (n * (n - 1)))
    Pbar = sum(P) / N; pe = sum((pj[c] / (N * n)) ** 2 for c in cats)
    return (Pbar - pe) / (1 - pe) if pe < 1 else None


def fmt(k):
    return "undefined" if k is None else f"{k:.2f}"


def load_models(results, exclude=(), skip=(), allow_exploratory=False):
    """Model ratings from a run directory. Outside the historical pilot a manifest is required: every listed model exactly once,
    with the manifest's digest, cases and criteria, exactly the manifest's case ids; a confirmatory manifest must hold the frozen
    roster with its approved digests. The pilot (run before manifests existed) is read from its fixed files only."""
    results = pathlib.Path(results)
    if not results.is_dir():
        sys.exit(f"{results}: no such run directory")
    skip = {pathlib.Path(x).resolve() for x in skip}
    files = {f.name: f for f in sorted(results.glob("*.json"))
             if f.name not in ("manifest.json", "agreement.json") and f.resolve() not in skip}
    raters = {}
    mf = results / "manifest.json"
    if not mf.exists():
        if results.resolve() != (PILOT / "results").resolve():
            sys.exit(f"{results}: no manifest.json; only the historical pilot is read without one")
        for f in files.values():
            d = json.loads(f.read_text())
            if d["model"] in raters:
                sys.exit(f"duplicate rater {d['model']}")
            if d["model"] not in exclude:
                raters[d["model"]] = {k: v["modal"] for k, v in d["cases"].items()}
        return raters, None
    m = json.loads(mf.read_text())
    if not m.get("complete"):
        sys.exit(f"{mf}: run not complete")
    if m.get("mode") != "confirmatory" and not allow_exploratory:
        sys.exit(f"{mf}: not a confirmatory run (mode {m.get('mode')}); pass --exploratory to read it as such")
    if m.get("mode") == "confirmatory":
        roster = {e["name"]: bare(e["digest"]) for e in m["models"]}
        if roster != ROSTER:
            sys.exit(f"{mf}: models or digests differ from the frozen roster")
        if m.get("runs") != CONFIRMATORY_RUNS:
            sys.exit(f"{mf}: a confirmatory run has {CONFIRMATORY_RUNS} runs per case, not {m.get('runs')}")
    listed = {e["file"]: e for e in m["models"]}
    if missing := sorted(set(listed) - set(files)):
        sys.exit(f"model result files missing: {missing}")
    if extra := sorted(set(files) - set(listed)):
        sys.exit(f"result files not in the manifest: {extra}")
    ids = set(m.get("case_ids") or [])
    if not ids or len(ids) != m.get("n_cases"):
        sys.exit(f"{mf}: case ids missing or inconsistent with n_cases")
    for name, e in listed.items():
        d = json.loads(files[name].read_text())
        bad = [k for k, v in (("model", e["name"]), ("digest", e["digest"]), ("cases_sha256", m["cases_sha256"]),
                               ("criteria_sha256", m["criteria_sha256"]), ("runs", m["runs"])) if d.get(k) != v]
        if bad:
            sys.exit(f"{name}: provenance differs from the manifest in {bad}")
        if set(d["cases"]) != ids:
            sys.exit(f"{name}: cases differ from the manifest's case ids")
        if short := sorted(k for k, v in d["cases"].items() if len(v.get("answers") or []) != m["runs"]):
            sys.exit(f"{name}: cases without {m['runs']} answers: {short[:10]}")
        if d["model"] in raters:
            sys.exit(f"duplicate rater {d['model']}")
        if badc := sorted(k for k, v in d["cases"].items() if v["modal"] is not None and (type(v["modal"]) is not int or not 1 <= v["modal"] <= 4)):
            sys.exit(f"{name}: invalid modal classes for {badc[:10]}")
        if d["model"] not in exclude:
            raters[d["model"]] = {k: v["modal"] for k, v in d["cases"].items()}
    return raters, m


def agree(results=PILOT / "results", human_file=PILOT / "human.json", allow_missing=False, write=True, exclude=(),
          allow_exploratory=False):
    results = pathlib.Path(results)
    human_file = pathlib.Path(human_file).resolve()
    models, manifest = load_models(results, exclude, skip=(human_file,), allow_exploratory=allow_exploratory)
    human = load_r0(human_file, manifest["case_ids"] if manifest else None)
    if manifest and manifest.get("mode") == "confirmatory" and manifest.get("r0_sha256") != sha256_file(human_file):
        sys.exit("the R0 file differs from the one committed and recorded in the manifest before the run")
    if not models:
        sys.exit("no model raters to compare")
    raters = {"R0 human": human, **models}
    # Every rater must cover exactly the human's cases with a class; a gap is an error unless --allow-missing.
    if extra := {name: sorted(set(cl) - set(human)) for name, cl in raters.items() if set(cl) - set(human)}:
        sys.exit(f"cases outside the R0 case set (provenance error, never allowed): {extra}")
    gaps = {name: {"missing": sorted(c for c in human if cl.get(c) is None), "extra": []} for name, cl in raters.items()}
    gaps = {k: v for k, v in gaps.items() if v["missing"]}
    if gaps and not allow_missing:
        sys.exit("case sets differ or modal class missing (tie/invalid); rerun or pass --allow-missing:\n"
                 + "\n".join(f"  {k}: missing {v['missing']} extra {v['extra']}" for k, v in gaps.items()))
    title = f"# Agreement on {len(human)} cases" + (f" (excluding {', '.join(exclude)})" if exclude else "")
    lines = [title, "", f"Raters: {len(raters)} (human + {len(raters)-1} models). Generated {datetime.date.today()}.", "",
             "| Rater | Cohen's kappa vs human | n | Share in classes 1-3 |", "|---|---|---|---|"]
    kappas = {}
    for name, cl in raters.items():
        if name == "R0 human": k = 1.0; n = len([v for v in cl.values() if v])
        else: k, n = cohen(human, cl)
        kappas[name] = k
        rated = [cl.get(c) for c in human if cl.get(c) is not None]  # denominator: the R0 case set, cases this rater classified
        share = sum(1 for v in rated if v in (1, 2, 3)) / max(1, len(rated))
        lines.append(f"| {name} | {fmt(k)} | {n} | {share:.0%} |")
    common = [c for c in human if all(cl.get(c) for cl in raters.values())]
    fk = fleiss({c: [cl[c] for cl in raters.values()] for c in common}) if len(raters) > 1 and common else None
    lines += ["", f"Fleiss' kappa across all raters on {len(common)} cases: **{fmt(fk)}** "
              f"({len(human) - len(common)} cases without complete ratings left out, D41 point 5)"]
    if gaps:
        lines += ["", f"Missing or extra cases (excluded, --allow-missing): "
                  + "; ".join(f"{k}: {len(v['missing'])} missing {v['missing']}, {len(v['extra'])} extra" for k, v in gaps.items())]
    lines += ["", "| Case | " + " | ".join(raters) + " |", "|---|" + "---|" * len(raters)]
    for c in human:
        lines.append(f"| {c} | " + " | ".join(str(cl.get(c, "-")) for cl in raters.values()) + " |")
    if write and results.resolve() == (PILOT / "results").resolve():
        write = False  # the pilot's published files are never rewritten
    if write:
        name = "agreement.md" if not exclude else "agreement-without-" + "-".join(e.split(":")[0] for e in exclude) + ".md"
        (results / name).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    return {"cohen": kappas, "fleiss": fk, "n_common": len(common), "gaps": gaps}


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["run", "agree"])
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS)); ap.add_argument("--runs", type=int, default=3)
    ap.add_argument("--cases", default=str(PILOT / "cases.json")); ap.add_argument("--human", default=str(PILOT / "human.json"))
    ap.add_argument("--r0", default=None, help="run: the committed R0 file; required for a confirmatory run")
    ap.add_argument("--mode", choices=MODES, default="exploratory", help="run: confirmatory needs the roster and committed R0")
    ap.add_argument("--exploratory", action="store_true", help="agree: read an exploratory run (never confirmatory agreement)")
    ap.add_argument("--out", default=None, help="run: output dir (default: new runs/run-<UTC timestamp>/)")
    ap.add_argument("--results", default=str(PILOT / "results"), help="agree: run directory (default: the pilot)")
    ap.add_argument("--exclude", action="append", default=[], help="agree: leave a model out (e.g. D43, without R2)")
    ap.add_argument("--allow-missing", action="store_true", help="agree: report, instead of refusing, missing cases")
    a = ap.parse_args()
    if a.cmd == "run":
        run(a.models.split(","), a.runs, a.cases, a.out, a.r0, a.mode)
    else:
        agree(a.results, a.human, a.allow_missing, exclude=tuple(a.exclude), allow_exploratory=a.exploratory)
