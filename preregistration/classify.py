#!/usr/bin/env python3
"""Independent classification of the disclosures by local models, and agreement with the human rater.

Usage (with the GPU machine on and `infra/ai-lab.sh tunnel` running in another terminal):
    python3 preprint/classify/classify.py run    [--models qwen3.8:27b-q8_0,gemma4:26b-a4b-it-q8_0,...] [--runs 3]
    python3 preprint/classify/classify.py agree

`run` writes results/<model>.json (every run, raw answers, modal class). `agree` prints pairwise Cohen's kappa against
human.json and Fleiss' kappa across all raters, and writes results/agreement.md. No dependencies beyond the standard library.
"""
import argparse, json, re, sys, urllib.request, collections, datetime, pathlib

HERE = pathlib.Path(__file__).resolve().parent
OLLAMA = "http://127.0.0.1:11434"
DEFAULT_MODELS = ["qwen3.8:27b-q8_0", "gemma4:26b-a4b-it-q8_0", "nemotron-3.5-lightning:30b-a3b-q4_K_M"]

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
Counting rule: one disclosure is one case, regardless of how many findings it bundles.
Answer with one JSON object only: {"class": <1|2|3|4>, "confidence": <0-1>, "reason": "<one sentence>"}"""
CRITERIA_VERSION = "v2 (preregistration, 11 Oct 2026)"
# Preregistration section 3; whole-word match, so "classic" does not trip it.
CLASS_WORDS = ["before trust", "approval", "injection", "authority", "plumbing", "class"]


def leak_check(cases):
    """Refuse to run if a case summary contains a class word (preregistration section 3)."""
    bad = [(c["id"], w) for c in cases for w in CLASS_WORDS
           if re.search(r"\b" + re.escape(w) + r"(es)?\b", c["summary"].lower())]
    if bad:
        sys.exit(f"class-word leak in summaries: {bad}")


def ask(model, case, seed):
    body = {"model": model, "stream": False, "format": "json",
            "options": {"temperature": 0, "seed": seed},
            "messages": [{"role": "system", "content": CRITERIA},
                         {"role": "user", "content": f"Summary: {case['summary']}"}]}  # summary only (preregistration section 4; deviation D4)
    req = urllib.request.Request(OLLAMA + "/api/chat", data=json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=1800) as r:
        d = json.load(r)
    text = d["message"]["content"]
    m = re.search(r'"class"\s*:\s*"?([1-4])', text)
    return {"raw": text, "class": int(m.group(1)) if m else None, "eval_count": d.get("eval_count")}


def model_digest(model):
    """Full sha256 of the local model, from /api/tags (the 12-character id in the preregistration is its prefix)."""
    with urllib.request.urlopen(OLLAMA + "/api/tags", timeout=60) as r:
        tags = json.load(r)["models"]
    return next((m["digest"] for m in tags if m["name"] == model), None)


def run(models, runs, cases_file="cases.json"):
    cases = json.loads((HERE / cases_file).read_text()); leak_check(cases)
    out = HERE / "results"; out.mkdir(exist_ok=True)
    for model in models:
        res = {"model": model, "digest": model_digest(model), "criteria": CRITERIA_VERSION, "started": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"), "runs": runs, "cases": {}}
        for c in cases:
            answers = [ask(model, c, seed) for seed in range(1, runs + 1)]
            classes = [a["class"] for a in answers if a["class"]]
            modal = collections.Counter(classes).most_common(1)[0][0] if classes else None
            res["cases"][c["id"]] = {"answers": answers, "classes": classes, "modal": modal, "stable": len(set(classes)) == 1}
            print(f"{model:40} {c['id']} -> {classes} modal={modal}", flush=True)
        (out / (model.replace(":", "_").replace("/", "_") + ".json")).write_text(json.dumps(res, indent=2, ensure_ascii=False))


def cohen(a, b):
    keys = [k for k in a if k in b and a[k] and b[k]]
    n = len(keys); po = sum(a[k] == b[k] for k in keys) / n
    ca, cb = collections.Counter(a[k] for k in keys), collections.Counter(b[k] for k in keys)
    pe = sum(ca[c] * cb[c] for c in set(ca) | set(cb)) / (n * n)
    return (po - pe) / (1 - pe) if pe < 1 else 1.0, n


def fleiss(ratings):  # ratings: dict case -> list of classes (one per rater)
    cats = [1, 2, 3, 4]; N = len(ratings); n = len(next(iter(ratings.values())))
    P = []; pj = collections.Counter()
    for r in ratings.values():
        cnt = collections.Counter(r); pj.update(cnt)
        P.append((sum(v * v for v in cnt.values()) - n) / (n * (n - 1)))
    Pbar = sum(P) / N; pe = sum((pj[c] / (N * n)) ** 2 for c in cats)
    return (Pbar - pe) / (1 - pe) if pe < 1 else 1.0


def agree():
    human = json.loads((HERE / "human.json").read_text())["classes"]
    raters = {"R0 human": human}
    for f in sorted((HERE / "results").glob("*.json")):
        if f.name == "agreement.json": continue
        d = json.loads(f.read_text()); raters[d["model"]] = {k: v["modal"] for k, v in d["cases"].items()}
    lines = ["# Agreement on the ten disclosures", "", f"Raters: {len(raters)} (human + {len(raters)-1} models). Generated {datetime.date.today()}.", "",
             "| Rater | Cohen's kappa vs human | n | Share in classes 1-3 |", "|---|---|---|---|"]
    for name, cl in raters.items():
        if name == "R0 human": k = 1.0; n = len(cl)
        else: k, n = cohen(human, cl)
        share = sum(1 for v in cl.values() if v in (1, 2, 3)) / max(1, len([v for v in cl.values() if v]))
        lines.append(f"| {name} | {k:.2f} | {n} | {share:.0%} |")
    common = [c for c in human if all(cl.get(c) for cl in raters.values())]
    fk = fleiss({c: [cl[c] for cl in raters.values()] for c in common}) if len(raters) > 1 and common else float("nan")
    lines += ["", f"Fleiss' kappa across all raters on {len(common)} cases: **{fk:.2f}**", "",
              "| Case | " + " | ".join(raters) + " |", "|---|" + "---|" * len(raters)]
    for c in human:
        lines.append(f"| {c} | " + " | ".join(str(cl.get(c, "-")) for cl in raters.values()) + " |")
    (HERE / "results" / "agreement.md").write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    ap = argparse.ArgumentParser(); ap.add_argument("cmd", choices=["run", "agree"])
    ap.add_argument("--models", default=",".join(DEFAULT_MODELS)); ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    run(a.models.split(","), a.runs) if a.cmd == "run" else agree()
