#!/usr/bin/env python3
"""RQ5 coverage analysis — POST HOC and EXPLORATORY (added 1 Nov 2026, after the confirmatory results of 24-27 Oct 2026).

It does not change the confirmatory verdict (H5 holds, evidence/scores-20261024/h5-author.json) and is not part of the
preregistered analysis. It reads the frozen scoring outputs and, optionally, the private redacted client-log archives, and
re-reports every client/event pair with its data coverage. Nothing it reads is modified.

Missing-data rule, fixed in this file before the analysis was run (MIN_COVERED):
  - A held-out one-minute window is "covered" for a rule when it holds at least one timed record of the rule's source (the
    D31 point 2 figure that scores_input.py already computes; records dated only by file time are not counted).
  - A pair is assessable for false positives only if at least MIN_COVERED = 30 of its 60 held-out windows are covered, i.e. at
    least half of the held-out hour was observable by the rule. Below that, the absence of alerts mostly reflects missing
    records, not the rule's specificity: the pair is "not adequately assessable", neither a success nor a failure of the rule.
    Justification: the preregistered threshold (D27 point 2) is a share of a full held-out hour; with fewer than half of its
    windows observable, the share is dominated by windows in which no alert was possible. At 30 covered windows with zero
    alerts the Wilson 95% upper bound is 11.4%, so even an assessable pair can exceed the 5% threshold in its upper bound;
    the bound is reported for every assessable pair.
  - Honesty note: the per-rule coverage figures (e.g. Goose 1/60, Claude Code notification log 46/60) were already published
    in the paper when this rule was set, so the rule is not blind to them; a sensitivity line at 15 and 45 is reported.
  - False positives are computed only on covered windows: k_covered / n_covered with Wilson 95% interval. A false-positive
    window outside the covered set is impossible by construction (a rule fires only on a record of its source).
  - A rule of type "none" (no rule could be written) cannot alert; its 0/60 is not a measurement: "not applicable".

Outcome categories per pair (detection axis):
  no-event             the ground truth shows the event did not happen (pair not measurable, as in h5-author.json)
  no-useful-evidence   the event happened but the inspected default-log sources hold no record a rule could use (rule "none")
  not-detected         a rule exists and the event happened, but the rule did not fire in at least one scored run
  detected             the rule fired in every scored run
  (export failures or missing runs would be "not-assessable-missing-data"; none are listed in the frozen inputs)

  python3 -I coverage.py [--private Q4_RESULTS_DIR]
Without --private only the public frozen outputs are used. With it, the redacted client-log archives of the holdout sessions
and event runs (baseline-r4/, events/) are read to add: per-client coverage by any default-log source, the client's timed
records between event and run end, and a cross-check of the per-rule coverage. No private path or file name is written out.
"""
import argparse, hashlib, importlib.util, json, os, sys, tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEL = HERE.parent
SCORES = TEL / "evidence/scores-20261024"
MIN_COVERED = 30
SENSITIVITY = (15, 30, 45)
EXPECTED_WINDOWS = 60  # one held-out hour per client (D27 point 3)


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sc = load("score", TEL / "scripts/score.py")


def category(ev, rule):
    if ev["scored"] == 0:
        if ev["left_out"]["no-event"]:
            return "no-event"
        return "not-assessable-missing-data"
    if rule["type"] == "none":
        return "no-useful-evidence"
    if ev["detected"] < ev["scored"]:
        return "not-detected"
    return "detected"


def fp_assessment(rule, ho, threshold):
    if rule["type"] in ("none", "unannounced"):
        return "not applicable (no rule)"
    cov = ho["covered_windows"]
    if cov is None:
        return "not verifiable (no coverage figure)"
    return "assessable" if cov >= threshold else "not adequately assessable"


def private_extension(priv, inp, rules):
    os.environ.setdefault("TMPDIR", tempfile.gettempdir())
    ap = load("apply", TEL / "rules/apply.py")
    out = {"holdout": {}, "events": {}, "archives_sha256": {}}
    clients = sorted({r["client"] for r in rules.values()})
    for c in clients:
        d = priv / "baseline-r4" / f"baseline__{c}__holdout"
        arch = d / "client-logs.redacted.tgz"
        ho = next(r["holdout"][0] for rid, r in inp["rules"].items() if rid.startswith(c + "/") and r["holdout"])
        t0, t1 = ho["t0"], ho["t1"]
        n = int((t1 - t0) // 60)
        recs = [x for x in ap.nz.records(arch, c, t0, t1) if x.get("time_from") != "mtime"]
        any_cov = len({int((x["t"] - t0) // 60) for x in recs if x["t"] < t0 + n * 60})
        mine = {rid: r for rid, r in rules.items() if r["client"] == c}
        out["holdout"][c] = {"windows": n, "covered_any_default_source": any_cov, "timed_records": len(recs),
                             "rule_coverage_recomputed": ap.coverage(mine, arch, c, t0, t1)}
        out["archives_sha256"][f"baseline__{c}__holdout"] = hashlib.sha256(arch.read_bytes()).hexdigest()
    for rid, r in inp["rules"].items():
        c = rid.split("/")[0]
        for run in r["event_runs"]:
            if run.get("status") != "ok":
                out["events"][run["run"]] = {"status": run.get("status")}
                continue
            arch = priv / "events" / run["run"] / "client-logs.redacted.tgz"
            recs = [x for x in ap.nz.records(arch, c, run["event_time"], run["end"]) if x.get("time_from") != "mtime"]
            out["events"][run["run"]] = {"status": "ok", "timed_records_event_to_end": len(recs),
                                         "sources_with_records": len({x["src"].split("#")[0] for x in recs})}
            out["archives_sha256"][run["run"]] = hashlib.sha256(arch.read_bytes()).hexdigest()
    return out


def main():
    a = argparse.ArgumentParser()
    a.add_argument("--private", type=Path)
    args = a.parse_args()
    scores = json.loads((SCORES / "scores-author.json").read_text())
    h5 = json.loads((SCORES / "h5-author.json").read_text())
    inp = json.loads((SCORES / "input-author.json").read_text())
    rules = json.loads((TEL / "rules/rules-author.json").read_text())["rules"]
    priv = private_extension(args.private, inp, rules) if args.private else None

    pairs = {}
    for rid in sorted(scores):
        s, rule = scores[rid], rules[rid]
        ev, ho = s["events"], s["holdout"]
        cov = ho["covered_windows"]
        fp_cov = None
        if cov:
            w = sc.wilson(ho["fp_windows"], cov)
            fp_cov = {"k": ho["fp_windows"], "n": cov, "share": ho["fp_windows"] / cov, "wilson95_upper": w[1]}
        p = {
            "client": rule["client"], "event": rule["event"], "rule_type": rule["type"],
            "event_runs_planned": ev["scored"] + sum(ev["left_out"].values()),
            "event_runs_scored": ev["scored"], "events_detected": ev["detected"], "no_event_runs": ev["left_out"]["no-event"],
            "export_failed_runs": ev["left_out"]["export-failed"],
            "windows_expected": EXPECTED_WINDOWS, "windows_scored": ho["windows"], "windows_covered_rule_source": cov,
            "alert_windows": ho["fp_windows"], "missing_holdout_windows": EXPECTED_WINDOWS - ho["windows"],
            "fp_all_windows": {"k": ho["fp_windows"], "n": ho["windows"], "wilson95_upper": ho["wilson95"][1]},
            "fp_covered_windows": fp_cov,
            "detection_category": category(ev, rule),
            "fp_assessment": fp_assessment(rule, ho, MIN_COVERED),
            "fp_assessment_sensitivity": {str(t): fp_assessment(rule, ho, t) for t in SENSITIVITY},
            "confirmatory_tells_apart": s["tells_apart"], "confirmatory_measurable": h5["pairs"][rid]["measurable"],
        }
        if priv:
            p["windows_covered_any_default_source"] = priv["holdout"][rule["client"]]["covered_any_default_source"]
            p["rule_coverage_recomputed"] = priv["holdout"][rule["client"]]["rule_coverage_recomputed"].get(rid)
            p["event_runs_records"] = {r["run"]: priv["events"].get(r["run"]) for r in inp["rules"][rid]["event_runs"]}
        p["posthoc_label"] = (
            "told apart, false positives assessed" if p["detection_category"] == "detected" and p["fp_assessment"] == "assessable"
            else "detected; false positives not adequately assessable" if p["detection_category"] == "detected"
            else p["detection_category"])
        pairs[rid] = p

    measurable = [p for p in pairs.values() if p["confirmatory_measurable"]]
    summary = {
        "measurable_pairs": len(measurable),
        "confirmatory_told_apart": sum(bool(p["confirmatory_tells_apart"]) for p in measurable),
        "told_apart_fp_assessed": sum(p["posthoc_label"] == "told apart, false positives assessed" for p in measurable),
        "detected_fp_not_adequately_assessable": [k for k, p in pairs.items()
                                                   if p["posthoc_label"] == "detected; false positives not adequately assessable"],
        "no_useful_evidence": [k for k, p in pairs.items() if p["detection_category"] == "no-useful-evidence"],
        "not_detected": [k for k, p in pairs.items() if p["detection_category"] == "not-detected"],
        "no_event": [k for k, p in pairs.items() if p["detection_category"] == "no-event"],
        "missing_listed_in_frozen_input": inp["missing"], "incomplete_clients": inp["incomplete_clients"],
        "confirmatory_h5_holds": h5["h5_holds"],
        "h5_depends_on_fp_coverage": False,
        "h5_note": "H5 holds because q3-silent (Codex CLI, Gemini CLI) and q5-start (Gemini CLI, Qwen Code) each have a measurable "
                   "pair with no usable record; those pairs fail on detection, not on false positives, so coverage cannot "
                   "change the verdict. The confirmatory 'q3-announced distinguishable in every client' rests for Goose on "
                   "1 covered window.",
    }
    result = {"status": "post hoc, exploratory; not preregistered; confirmatory verdict unchanged",
              "min_covered_windows": MIN_COVERED, "sensitivity_thresholds": list(SENSITIVITY),
              "inputs_sha256": {n: hashlib.sha256((SCORES / n).read_bytes()).hexdigest()
                                for n in ("scores-author.json", "h5-author.json", "input-author.json")}
                               | {"rules-author.json": hashlib.sha256((TEL / "rules/rules-author.json").read_bytes()).hexdigest()},
              "private_extension": bool(priv), "summary": summary, "pairs": pairs}
    if priv:
        result["private_archives_sha256"] = priv["archives_sha256"]
        result["client_holdout_any_source"] = {c: {k: v for k, v in h.items() if k != "rule_coverage_recomputed"}
                                               for c, h in priv["holdout"].items()}
    (HERE / "COVERAGE-POSTHOC.json").write_text(json.dumps(result, indent=1) + "\n")
    (HERE / "COVERAGE-POSTHOC.md").write_text(markdown(result))


NAMES = {"claude-code": "Claude Code", "codex": "Codex CLI", "gemini": "Gemini CLI", "goose": "Goose", "qwen": "Qwen Code"}


def pct(x):
    return "—" if x is None else f"{100 * x:.1f}%"


def markdown(r):
    L = ["# RQ5 coverage analysis (post hoc, exploratory)", "",
         "Added 1 Nov 2026, after the confirmatory RQ5 results. Not preregistered. The confirmatory verdict "
         "(`evidence/scores-20261024/h5-author.json`: H5 holds) is unchanged. Generated by `coverage.py`; do not edit by hand.", "",
         f"**Missing-data rule (fixed before computing).** A held-out window is covered for a rule when it holds at least one timed "
         f"record of the rule's source. A pair is assessable for false positives only if at least {r['min_covered_windows']} of its "
         f"60 held-out windows are covered (half the held-out hour). Below that it is *not adequately assessable*: neither a "
         f"success nor a failure of the rule. False positives are computed on covered windows only, with the Wilson 95% upper "
         f"bound. A rule of type \"none\" cannot alert, so its 0/60 is *not applicable*. The per-rule coverage figures were "
         f"already published when the rule was set; sensitivity at {', '.join(map(str, r['sensitivity_thresholds']))} "
         f"covered windows is in the JSON.", "",
         "| Pair | Rule | Runs scored / no event | Detected | Windows expected / scored / covered (rule source)"
         + (" / covered (any default source)" if r["private_extension"] else "") + " | Alerts | FP on covered (Wilson 95% upper) | FP assessment | Post hoc label |",
         "|---|---|---|---|---|---|---|---|---|"]
    for rid, p in r["pairs"].items():
        cov = "—" if p["windows_covered_rule_source"] is None else str(p["windows_covered_rule_source"])
        w = f"{p['windows_expected']} / {p['windows_scored']} / {cov}"
        if r["private_extension"]:
            w += f" / {p['windows_covered_any_default_source']}"
        f = p["fp_covered_windows"]
        fp = "—" if f is None else f"{f['k']}/{f['n']} ({pct(f['wilson95_upper'])})"
        L.append(f"| {NAMES[p['client']]} / {p['event']} | {p['rule_type']} | {p['event_runs_scored']} / {p['no_event_runs']} | "
                 f"{p['events_detected']}/{p['event_runs_scored']} | {w} | {p['alert_windows']} | {fp} | {p['fp_assessment']} | "
                 f"{p['posthoc_label']} |")
    s = r["summary"]
    L += ["", "## Summary", "",
          f"- Measurable pairs: {s['measurable_pairs']}; told apart in the confirmatory analysis: {s['confirmatory_told_apart']}.",
          f"- Told apart with false positives assessed on at least {r['min_covered_windows']} covered windows: {s['told_apart_fp_assessed']}.",
          f"- Detected, false positives not adequately assessable: {', '.join(s['detected_fp_not_adequately_assessable']) or 'none'}.",
          f"- Event produced, no useful evidence in the inspected default-log sources (no rule): {', '.join(s['no_useful_evidence'])}.",
          f"- Event produced, rule exists, not detected: {', '.join(s['not_detected']) or 'not observed'}.",
          f"- No event produced (ground truth): {', '.join(s['no_event'])}.",
          f"- Missing runs or sessions in the frozen input: {len(s['missing_listed_in_frozen_input'])}; incomplete clients: "
          f"{len(s['incomplete_clients'])}. Every planned holdout has 60 scored windows.",
          f"- {s['h5_note']}"]
    if r["private_extension"]:
        L += ["", "## Per-client held-out coverage by any default-log source (from the private redacted archives)", "",
              "| Client | Windows | Covered by any frozen default-log location | Timed records |", "|---|---|---|---|"]
        for c, h in r["client_holdout_any_source"].items():
            L.append(f"| {NAMES[c]} | {h['windows']} | {h['covered_any_default_source']} | {h['timed_records']} |")
        L += ["", "Cross-check: per-rule coverage recomputed from the archives "
              + ("matches" if all(p["rule_coverage_recomputed"] == p["windows_covered_rule_source"] for p in r["pairs"].values())
                 else "DOES NOT match") + " the frozen scores for every pair.", "",
              "Timed client records between the ground-truth event time and the run end, per event run (counts only):", "",
              "| Run | Timed records | Sources with records |", "|---|---|---|"]
        for rid, p in r["pairs"].items():
            for run, e in p["event_runs_records"].items():
                if e and e.get("status") == "ok":
                    L.append(f"| {run} | {e['timed_records_event_to_end']} | {e['sources_with_records']} |")
                else:
                    L.append(f"| {run} | — ({e.get('status') if e else 'not verifiable'}) | — |")
        L += ["", "A record in the window is not a usable trace: for the \"none\" pairs, the rule notes in `rules/rules-author.json` say why "
              "the records present do not tell the event apart."]
    return "\n".join(L) + "\n"


if __name__ == "__main__":
    sys.exit(main())
