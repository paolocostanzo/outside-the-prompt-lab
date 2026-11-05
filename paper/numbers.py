#!/usr/bin/env python3
"""The quantities that the paper (paper/main.pdf) cites, read or computed from the evidence files of this repository.

Prints one JSON object on stdout, the results file paper/results/numbers.json when run through `osaudit run`:

    osaudit run $(python3 -I paper/numbers.py --inputs | sed 's/^/--input /') \
        -o paper/results/numbers.json -- python3 -I -B paper/numbers.py

(`--inputs` lists the files it reads.) osaudit.toml traces the paper's numbers to these values; numbers the study does
not produce (dates, years, identifiers, preregistered thresholds) are listed there as [[numbers.allow]] with a reason.

Every value is read from an evidence file (JSON, CSV, Markdown table or log) or computed from one; no result is typed in
here. Names follow the paper: `rq1.*` (Section 5), `rq2.*` (Section 6), `rq3.*` (Section 7), `rq4.*` (Section 8),
`rq5.*` (Section 9), `design.*` (Section 4). The RQ1 shares that are not stored in a JSON file (post hoc variants of
AUDIT.md, the bound of the flagged cases) are recomputed with the frozen estimator `preregistration/rq1/estimate.py`,
unmodified. No clock, no file time, no network. Standard library only; run with python3 -I from the repository root.
"""
import csv
import json
import pathlib
import re
import sys
from collections import Counter
from fractions import Fraction

ROOT = pathlib.Path(__file__).resolve().parent.parent
RQ1 = ROOT / "preregistration" / "rq1"
RUN = ROOT / "preregistration" / "runs" / "rq1-confirmatory-20261027T142818Z"
RQ1A = ROOT / "preregistration" / "runs" / "rq1-confirmatory-20261027T142818Z-rq1-analysis"
Q2E = ROOT / "trusting-a-repo" / "evidence"
Q3E = ROOT / "tool-change" / "evidence"
Q4R = ROOT / "defence-coverage"
Q5 = ROOT / "telemetry"

MODELS = {"qwen": "qwen3.8_27b-q8_0", "gemma": "gemma4_26b-a4b-it-q8_0",
          "nemotron": "nemotron-3.5-lightning_30b-a3b-q4_K_M"}

# Every file this instrument reads (the --input list of `osaudit run`).
INPUTS = [
    "preregistration/chronology.csv",
    "preregistration/pilot/human.json",
    "preregistration/pilot/results/agreement.md",
    "preregistration/rq1/estimate.py",
    "preregistration/rq1/candidates-20261025.json",
    "preregistration/rq1/screening-20261025.csv",
    "preregistration/rq1/rq1-frame.csv",
    "preregistration/rq1/rq1-sample.csv",
    "preregistration/rq1/rq1-sample-manifest.json",
    "preregistration/rq1/rq1-flags.json",
    "preregistration/rq1/rq1-r0.json",
    "preregistration/rq1/summary-checks.csv",
    "preregistration/rq1/fisher-flags.json",
    "preregistration/rq1/audit-posthoc/rq1-audit-cases.csv",
    "preregistration/rq1/audit-posthoc/rq1-class3-residual-map.csv",
    "preregistration/rq1/audit-posthoc/rq1-class3-second-check.csv",
    "preregistration/rq1/agreement-posthoc/AGREEMENT-POSTHOC.json",
    "preregistration/rq1/source-audit-posthoc/COMPARE-RATERS.json",
    "preregistration/rq1/source-audit-posthoc/frame-check.md",
    "preregistration/runs/rq1-confirmatory-20261027T142818Z/manifest.json",
    *(f"preregistration/runs/rq1-confirmatory-20261027T142818Z/{m}.json" for m in MODELS.values()),
    "preregistration/runs/rq1-confirmatory-20261027T142818Z-rq1-analysis/RESULTS-RQ1.json",
    "preregistration/runs/rq1-confirmatory-20261027T142818Z-rq1-analysis/EXPLORATORY-DISAGREEMENT.json",
    "trusting-a-repo/evidence/q5-run/20261009-194314/matrix.csv",
    "trusting-a-repo/evidence/q5-run/20261009-200610/matrix.csv",
    "trusting-a-repo/evidence/q5-run/recheck-20261009/matrix-current-versions/matrix.csv",
    "trusting-a-repo/evidence/q5-run/recheck-20261009/gemini-x3/matrix.csv",
    "trusting-a-repo/evidence/q5-run/recheck-20261009/non-interactive/ptest.log",
    "trusting-a-repo/evidence/q5-run/recheck-20261009/claude-p-clean",
    "trusting-a-repo/evidence/gui-20261009",
    "tool-change/evidence/primary-20261015/analysis/analysis.json",
    "tool-change/evidence/primary-20261015/coding/agreement.json",
    "tool-change/evidence/primary-20261015/coding/disagreements-resolved.csv",
    "tool-change/evidence/primary-20261015/coding/codex/agreement-three.json",
    "tool-change/evidence/positive-control-20261028/coded.csv",
    "tool-change/evidence/open-weight-20261024/RESULTS.json",
    "tool-change/states-posthoc/STATES.json",
    "defence-coverage/results-20261024/coverage.json",
    "defence-coverage/results-20261024/adjudication.csv",
    "defence-coverage/partial-posthoc/PARTIAL-DETAIL.csv",
    "defence-coverage/partial-posthoc/RECLASSIFICATION-SUGGESTIONS-v1.md",
    "telemetry/evidence/scores-20261024/h5-author.json",
    "telemetry/evidence/scores-20261024/agreement.json",
    "telemetry/evidence/scores-20261024/scores-host.json",
    "telemetry/coverage-posthoc/COVERAGE-POSTHOC.json",
]

sys.path.insert(0, str(RQ1))
import estimate as es  # noqa: E402  the frozen RQ1 estimator, unmodified


def load(rel):
    return json.loads((ROOT / rel).read_text(encoding="utf-8"))


def rows(rel):
    with open(ROOT / rel, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def frac(s):
    return float(Fraction(s))


# ---------------------------------------------------------------------------------------------------------------- RQ1
def rq1():
    out = {}
    man = load("preregistration/rq1/rq1-sample-manifest.json")
    sizes = man["stratum_sizes"]
    frame = [r for r in rows("preregistration/rq1/rq1-frame.csv")]
    included = [r for r in frame if r["decision"] == "include"]
    screening = rows("preregistration/rq1/screening-20261025.csv")
    out["frame"] = {
        "candidate_records": len(load("preregistration/rq1/candidates-20261025.json")),
        "uncertain_second_reading": sum(r["second_reading"] == "yes" for r in screening),
        "cases_before_window": sum(r["reason"] == "E6" for r in frame),
        "cases": len(included),
        "agent_client": sizes["agent client"],
        "mcp_server_or_connector": sizes["MCP server or connector"],
        "sdk": sizes["SDK"],
        "from_timeline": sum(r["source"] == "timeline" for r in included),
    }
    out["sample"] = {"n": man["n"], **{k.replace(" ", "_"): v for k, v in man["allocation"].items()}}
    sample = {r["case_id"]: r["product_type"] for r in rows("preregistration/rq1/rq1-sample.csv")
              if r["sampled"].strip() == "yes"}

    # Summaries, flags, R0 sheet
    checks = rows("preregistration/rq1/summary-checks.csv")
    flags = load("preregistration/rq1/rq1-flags.json")
    flagged = set(flags["flagged"])
    corrected = [r for r in checks if r["verdict"] == "corrected"]
    out["summaries"] = {
        "corrected": len(corrected),
        "flagged_corrected": sum(r["case_id"] in flagged for r in corrected),
        "flagged_unchanged": sum(r["case_id"] in flagged for r in checks if r["verdict"] != "corrected"),
        "flagged": len(flagged),
        "not_flagged": len(sample) - len(flagged),
    }
    r0doc = load("preregistration/rq1/rq1-r0.json")
    r0 = {k: int(v) for k, v in r0doc["classes"].items()}
    direct = r0doc["class_set_directly"]
    out["r0_sheet"] = {"class_set_directly": sum(bool(v) for v in direct.values()),
                       "class_from_questions": sum(not v for v in direct.values()),
                       "contradicting_answers": sum(bool(v) for v in r0doc["direct_class_contradicts_answers"].values())}

    # Model runs
    manifest = load(f"preregistration/runs/rq1-confirmatory-20261027T142818Z/manifest.json")
    out["run"] = {"runs_per_model": manifest["runs"], "temperature": manifest["temperature"],
                  "context_tokens": manifest["num_ctx"], "n_cases": manifest["n_cases"]}
    runs = {k: load(f"preregistration/runs/rq1-confirmatory-20261027T142818Z/{v}.json")["cases"]
            for k, v in MODELS.items()}
    modal = {k: {c: v["modal"] for c, v in cs.items()} for k, cs in runs.items()}

    def majority(c):
        votes = [modal[k][c] for k in MODELS]
        for cl in (1, 2, 3, 4):
            if sum(v == cl for v in votes) * 2 > len(votes):
                return cl
        return None
    maj = {c: majority(c) for c in sample}

    def counts(lab):
        c = Counter(lab.get(x) for x in sample)
        return {"class1": c[1], "class2": c[2], "class3": c[3], "class4": c[4],
                "classes_1_2": c[1] + c[2], "classes_1_3": c[1] + c[2] + c[3], "no_majority": c[None]}
    out["classes"] = {"R0": counts(r0), "majority": counts(maj), **{k: counts(modal[k]) for k in MODELS}}
    g = runs["gemma"]
    out["models"] = {
        k: {"cases_runs_differ": sum(not v["stable"] and v["n_invalid"] == 0 for v in cs.values()),
            "cases_with_invalid": sum(v["n_invalid"] > 0 for v in cs.values()),
            "invalid_answers": sum(v["n_invalid"] for v in cs.values()),
            "answers": sum(len(v["answers"]) for v in cs.values())}
        for k, cs in runs.items()}
    out["models"]["gemma"]["cases_single_valid_answer"] = sum(
        sum(a["valid"] for a in v["answers"]) == 1 for v in g.values())
    qn = [c for c in sample if modal["qwen"][c] != modal["nemotron"][c]]
    out["models"]["qwen_vs_nemotron_differ"] = len(qn)
    out["models"]["qwen_vs_nemotron_differ_within_1_3"] = sum(
        modal["qwen"][c] in (1, 2, 3) and modal["nemotron"][c] in (1, 2, 3) for c in qn)

    # Primary analysis, variants, H1a (RESULTS-RQ1.json, as committed)
    res = load("preregistration/runs/rq1-confirmatory-20261027T142818Z-rq1-analysis/RESULTS-RQ1.json")

    def est(r):
        return {"share": r["share"], "low": r["interval"][0], "high": r["interval"][1], "unweighted": r["unweighted"]}
    out["primary"] = {"R0": est(res["primary"]["R0"]), "majority": est(res["primary"]["model majority"])}
    names = {"D45/D41 p1: mixed bundles as class 4": "mixed_bundles_class4",
             "D41 p6: contested cases against H1": "contested_against",
             "D41 p6: contested cases in favour of H1": "contested_in_favour",
             "D43: model majority without R2": "without_R2",
             "D44 p1: without the flagged (I?) cases": "without_kept_in_doubt",
             "D44 p5: without late-ineligible cases": "without_late_ineligible",
             "D44 p6: labelled cases only": "labelled_only",
             "D44 p6: equal weights for the three product types": "equal_weights"}
    out["variants"] = {names[k]: {"R0": v["R0"]["share"], "majority": v["model majority"]["share"]}
                       for k, v in res["variants"].items()}
    out["variants"]["not_applicable"] = len(res["not_applicable"])
    out["contested"] = {"cases": len(res["contested"]),
                        "flagged": sum(c in flagged for c in res["contested"])}
    h1a = res["H1a"]
    out["H1a"] = {"fleiss_all": h1a["fleiss_all_raters"], "fleiss_without_R2": h1a["fleiss_without_R2"],
                  "n_complete": h1a["n_complete"],
                  **{f"cohen_{k}": h1a["cohen_vs_R0"][v.replace("_", ":", 1)]["kappa"] for k, v in MODELS.items()}}
    out["per_model"] = {k: {"share": res["per_model"][v.replace("_", ":", 1)]["share"],
                            "low": res["per_model"][v.replace("_", ":", 1)]["interval"][0],
                            "high": res["per_model"][v.replace("_", ":", 1)]["interval"][1],
                            "unweighted": res["per_model"][v.replace("_", ":", 1)]["unweighted"],
                            "invalid_rate": res["per_model"][v.replace("_", ":", 1)]["invalid_answer_rate"]}
                        for k, v in MODELS.items()}
    bt = res["by_product_type"]
    out["by_type"] = {
        "agent_client": {"R0": est(bt["agent client"]["stratum"]["R0"]),
                         "majority": est(bt["agent client"]["stratum"]["model majority"]),
                         "frame_without_R0": bt["agent client"]["frame without it"]["R0"]["share"],
                         "frame_without_majority": bt["agent client"]["frame without it"]["model majority"]["share"]},
        "mcp": {"R0": est(bt["MCP server or connector"]["stratum"]["R0"]),
                "majority": est(bt["MCP server or connector"]["stratum"]["model majority"]),
                "frame_without_R0": bt["MCP server or connector"]["frame without it"]["R0"]["share"],
                "frame_without_majority": bt["MCP server or connector"]["frame without it"]["model majority"]["share"]},
        "sdk_sampled": bt["SDK"]["sampled"],
    }

    # Bound when every flagged summary is counted as class 4 (paper: "cannot exceed 38.4%"): every unflagged case in
    # classes 1-3, every flagged case in class 4, frozen estimator.
    st = {t: (sizes[t], sum(p == t for p in sample.values()),
              sum(p == t and c not in flagged for c, p in sample.items())) for t in sizes}
    out["flagged_as_class4_max_share"] = float(es.stratified_share(st)["share"])

    # Exploratory disagreement (D51) and post hoc agreement (D56)
    ex = load("preregistration/runs/rq1-confirmatory-20261027T142818Z-rq1-analysis/EXPLORATORY-DISAGREEMENT.json")
    pairs = ex["disagreement_pairs"]["R0 vs model majority"]
    out["disagreement"] = {
        "R0_vs_majority_cases": sum(pairs.values()),
        "between_1_3": pairs.get("1-3", 0), "between_2_3": pairs.get("2-3", 0),
        "binary": sum(v for k, v in pairs.items() if k.endswith("4")),
        "binary_R0_class4_majority_1_3": sum(1 for c in sample if r0[c] == 4 and maj[c] in (1, 2, 3)),
        "fleiss_binary": ex["binary"]["Fleiss, R0 + three models"]["kappa"],
        "fleiss_binary_low": ex["binary"]["Fleiss, R0 + three models"]["kappa_95"]["low"],
        "fleiss_binary_high": ex["binary"]["Fleiss, R0 + three models"]["kappa_95"]["high"],
        "fleiss_four_low": ex["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["low"],
        "fleiss_four_high": ex["four_class"]["Fleiss, R0 + three models"]["kappa_95"]["high"],
        "nemotron_binary_kappa": ex["binary"]["R0 vs nemotron-3.5-lightning:30b-a3b-q4_K_M"]["cohen_kappa"],
        "flagged_cases": ex["by_flag"]["flagged (D41)"]["cases"],
        "flagged_disagree": ex["by_flag"]["flagged (D41)"]["R0 vs majority disagree (4 classes)"],
        "flagged_disagree_binary": ex["by_flag"]["flagged (D41)"]["R0 vs majority disagree (binary)"],
        "flagged_no_majority": ex["by_flag"]["flagged (D41)"]["no model majority"],
        "unflagged_cases": ex["by_flag"]["not flagged"]["cases"],
        "unflagged_disagree": ex["by_flag"]["not flagged"]["R0 vs majority disagree (4 classes)"],
        "unflagged_disagree_binary": ex["by_flag"]["not flagged"]["R0 vs majority disagree (binary)"],
    }
    fi = load("preregistration/rq1/fisher-flags.json")
    out["disagreement"]["fisher_flagged_with_majority"] = sum(fi["table"][0])
    out["disagreement"]["fisher_unflagged_with_majority"] = sum(fi["table"][1])
    out["disagreement"]["fisher_p"] = float(fi["p_two_sided"])
    ag = load("preregistration/rq1/agreement-posthoc/AGREEMENT-POSTHOC.json")
    rm = ag["R0_vs_model_majority"]
    out["agreement_posthoc"] = {
        "ac1_four": ag["gwet_ac1_multirater"]["four_class"]["ac1"],
        "ac1_four_low": ag["gwet_ac1_multirater"]["four_class"]["ac1_95"]["low"],
        "ac1_four_high": ag["gwet_ac1_multirater"]["four_class"]["ac1_95"]["high"],
        "ac1_binary": ag["gwet_ac1_multirater"]["binary"]["ac1"],
        "ac1_binary_low": ag["gwet_ac1_multirater"]["binary"]["ac1_95"]["low"],
        "ac1_binary_high": ag["gwet_ac1_multirater"]["binary"]["ac1_95"]["high"],
        "R0_vs_majority_n": rm["n"],
        "R0_vs_majority_agree_four": rm["four_class"]["agreements"],
        "R0_vs_majority_agree_binary": rm["binary"]["agreements"],
        "R0_vs_majority_ac1_four": rm["four_class"]["ac1"],
        "R0_vs_majority_ac1_binary": rm["binary"]["ac1"],
        "R0_vs_majority_pabak_four": rm["four_class"]["pabak"],
        "R0_vs_majority_pabak_binary": rm["binary"]["pabak"],
        "confusion": {f"R0_{a}": {f"maj_{b.replace(' ', '_')}": n for b, n in row.items()}
                      for a, row in ag["confusion_R0_x_majority"].items()},
    }

    # Post hoc audit of the R0 labels (AUDIT.md), from its per-case files
    audit = rows("preregistration/rq1/audit-posthoc/rq1-audit-cases.csv")
    clause = Counter(r["a_class3_clause"] for r in audit if r["r0"] == "3")
    resmap = rows("preregistration/rq1/audit-posthoc/rq1-class3-residual-map.csv")
    mech = Counter(r["mechanism"] for r in resmap)
    top = {"path": "path traversal / file confinement", "ssrf": "SSRF / unrestricted destination",
           "command": "attacker text reaches a command / process spawn"}
    second = rows("preregistration/rq1/audit-posthoc/rq1-class3-second-check.csv")
    boundary = [r for r in audit if r["b_in_scope"] == "yes"]
    not_est = [r for r in audit if r["b_status"] == "not established by the sources"]
    out["audit"] = {
        "r0_class3": sum(r["r0"] == "3" for r in audit),
        "class3_authorisation": clause["authorization"], "class3_authentication": clause["authentication"],
        "class3_origin": clause["origin"],
        "class3_literal": clause["authorization"] + clause["authentication"] + clause["origin"],
        "class3_rule_only": len(resmap),
        "rule_only_paths": mech[top["path"]], "rule_only_ssrf": mech[top["ssrf"]],
        "rule_only_command": mech[top["command"]],
        "rule_only_other": len(resmap) - sum(mech[v] for v in top.values()),
        "second_check_agree_all_fields": sum(r["agree_all_fields"] == "yes" for r in second),
        "boundary_cases": len(boundary),
        "not_established": len(not_est),
        "not_established_r0_1_3": sum(r["r0"] in ("1", "2", "3") for r in not_est),
        "not_established_r0_4": sum(r["r0"] == "4" for r in not_est),
    }
    cat = Counter(r["c_category"] for r in audit if r["c_category"])
    out["audit"]["flags_cannot_change_class"] = cat["resolved correction / non-class doubt"]
    out["audit"]["flags_can_change_class"] = cat["residual class-relevant uncertainty"]
    out["audit"]["flags_class_3_4_boundary"] = sum("(3/4" in r["c_note"] for r in audit
                                                   if r["c_category"] == "residual class-relevant uncertainty")
    out["audit"]["flags_bibliographic"] = cat["bibliographic-only"]
    # Exploratory variant: the 28 "not established" cases as class 4 (AUDIT.md part b), frozen estimator
    ids = {r["case_id"] for r in not_est}

    def share(labels, as4=frozenset()):
        st = {}
        for t in sizes:
            cs = [c for c, p in sample.items() if p == t]
            x = sum(labels.get(c) in (1, 2, 3) and c not in as4 for c in cs)
            u = sum(labels.get(c) is None and c not in as4 for c in cs)
            st[t] = (sizes[t], len(cs), x, u)
        r = es.stratified_share(st)
        return {"share": float(r["share"]), "low": float(r["interval"][0]), "high": float(r["interval"][1])}
    out["audit"]["not_established_as_class4"] = {"R0": share(r0, ids), "majority": share(maj, ids)}

    # Source audit (D56) and frame check
    cr = load("preregistration/rq1/source-audit-posthoc/COMPARE-RATERS.json")
    xt = cr["cross_tab_claude_x_codex"]
    first = Counter()
    for k, n in xt.items():
        first[k.split("|")[0]] += n
    jr = cr["joint_x_R0"]
    out["source_audit"] = {
        "first_A": first["A"], "first_B": first["B"], "first_C": first["C"],
        "exact_agreement": cr["exact_agreement"],
        "A_vs_B": xt.get("A|B", 0) + xt.get("B|A", 0),
        "other_disagreements": len(sample) - cr["exact_agreement"] - xt.get("A|B", 0) - xt.get("B|A", 0),
        "codex_A_claude_C": xt.get("C|A", 0),
        "joint_A": cr["joint"]["A"], "joint_B": cr["joint"]["B"], "joint_U": cr["joint"]["U"],
        "decided": cr["joint"]["A"] + cr["joint"]["B"],
        "A_in_R0_1_3": jr["A|R0 1-3"], "B_in_R0_4": jr["B|R0 4"], "B_in_R0_1_3": jr["B|R0 1-3"],
        "U_in_R0_1_3": jr["U|R0 1-3"], "U_in_R0_4": jr["U|R0 4"],
        "share_A_decided": frac(cr["share_A_decided"]["share"]),
        "share_A_decided_low": frac(cr["share_A_decided"]["interval"][0]),
        "share_A_decided_high": frac(cr["share_A_decided"]["interval"][1]),
        "share_A_against": frac(cr["share_A_against"]["share"]),
        "share_A_against_low": frac(cr["share_A_against"]["interval"][0]),
        "share_A_against_high": frac(cr["share_A_against"]["interval"][1]),
    }
    fc = (ROOT / "preregistration/rq1/source-audit-posthoc/frame-check.md").read_text(encoding="utf-8")
    sec2 = fc.split("## 2. Possible ineligibility", 1)[1]
    suspicions = [ln.split("|")[3].strip() for ln in sec2.splitlines() if ln.startswith("| RQ1-")]
    out["frame_check"] = {
        "possibly_ineligible": sum(not s.startswith(("Eligible", "borderline")) for s in suspicions),
        "counting_unit_doubts": len(re.findall(r"this is a grouping\s+error", fc)),
    }

    # Pilot (exploratory) and the H1a threshold context
    pilot = load("preregistration/pilot/human.json")["classes"]
    in13 = [c for c, v in pilot.items() if v in (1, 2, 3)]
    out["pilot"] = {"cases": len(pilot), "r0_classes_1_3": len(in13),
                    "r0_classes_1_3_C01_class4": len([c for c in in13 if c != "C01"]),
                    "cases_C01_dated_by_advisory": len(pilot) - 1}
    md = (ROOT / "preregistration/pilot/results/agreement.md").read_text(encoding="utf-8")
    out["pilot"]["fleiss"] = float(re.search(r"Fleiss' kappa across all raters on \d+ cases: \*\*([0-9.]+)\*\*", md)[1])
    return out


# ---------------------------------------------------------------------------------------------------------------- RQ2
def rq2():
    sets = {"first": ["trusting-a-repo/evidence/q5-run/20261009-194314/matrix.csv",
                      "trusting-a-repo/evidence/q5-run/20261009-200610/matrix.csv"],
            "second": ["trusting-a-repo/evidence/q5-run/recheck-20261009/matrix-current-versions/matrix.csv",
                       "trusting-a-repo/evidence/q5-run/recheck-20261009/gemini-x3/matrix.csv"]}
    full = "trusting-a-repo/evidence/q5-run/20261009-194314/matrix.csv"
    valid = {}
    for k, files in sets.items():
        rs = []
        for f in files:
            # Codex rows of the full first matrix are invalid (background-server screen; NOTES.md) and excluded
            rs += [r for r in rows(f) if not (f == full and r["client"] == "codex")]
        valid[k] = rs
    out = {"runs_first_set": len(valid["first"]), "runs_second_set": len(valid["second"]),
           "runs_valid": len(valid["first"]) + len(valid["second"]),
           "terminal_clients": len({r["client"] for r in valid["first"]})}

    def cell(rs, client, name, col, version=None):
        sel = [r for r in rs if r["client"] == client and r["cell"] == name and (version is None or r["version"] == version)
               and r[col] != ""]
        return {"starts": sum(int(r[col]) > 0 for r in sel), "reps": len(sel)}
    a = valid["first"]
    out["cells"] = {}
    for client in sorted({r["client"] for r in a}):
        out["cells"][client] = {}
        for name in sorted({r["cell"] for r in a if r["client"] == client}):
            c = {"before": cell(a, client, name, "starts_before"), "after": cell(a, client, name, "starts_after")}
            out["cells"][client][name.replace("-", "_")] = c
    b = valid["second"]
    out["gemini_0_63"] = {name.replace("-", "_"): {"before": cell(b, "gemini", name, "starts_before"),
                                                   "after": cell(b, "gemini", name, "starts_after")}
                          for name in ("untrusted", "after-decision", "trusted-reopen")}
    log = (ROOT / "trusting-a-repo/evidence/q5-run/recheck-20261009/non-interactive/ptest.log").read_text()
    ni = {}
    for m in re.finditer(r"^(\S+) r\d+ starts=(\d+)", log, re.M):
        d = ni.setdefault(m[1].replace("-", "_"), {"starts": 0, "runs": 0})
        d["starts"] += int(m[2]) > 0
        d["runs"] += 1
    out["non_interactive_2_1_295"] = ni
    clean = sorted((ROOT / "trusting-a-repo/evidence/q5-run/recheck-20261009/claude-p-clean").glob("*.out"))
    out["claude_p_clean_runs"] = len(clean)
    gui = sorted(p.name for p in (ROOT / "trusting-a-repo/evidence/gui-20261009").iterdir() if p.is_dir())
    out["graphical_clients"] = len(gui)
    out["clients"] = out["terminal_clients"] + len(gui)
    return out


# ---------------------------------------------------------------------------------------------------------------- RQ3
def rq3():
    an = load("tool-change/evidence/primary-20261015/analysis/analysis.json")
    cells = an["cells_phase2"]
    clients = sorted({k.split("|")[0] for k in cells})
    out = {"repetitions": an["n_repetitions"], "valid": an["n_valid"], "cells": len(cells), "clients": len(clients),
           "repetitions_per_cell": an["n_repetitions"] // len(cells),
           "no_signal_stale": sum(v.get("stale", 0) for k, v in cells.items() if k.endswith("|none")),
           "no_signal_reps": sum(sum(v.values()) for k, v in cells.items() if k.endswith("|none")),
           "clients_reapproval": an["H3_clause1"]["clients_reapproval"],
           "notification_delivered_clients": sum(v["delivered"] > 0 for v in an["H3_clause2"]["per_client"].values()),
           "gemini_acting": an["H3_clause2"]["per_client"]["gemini"]["acting_repetitions"],
           "cells_phase2": {k.replace("|", "__").replace("-", "_"): v for k, v in cells.items()},
           "reopen": {k.replace("-", "_"): v for k, v in an["reopen_phase3_exploratory"].items()}}
    states = load("tool-change/states-posthoc/STATES.json")
    agg = states["aggregate_primary"]
    out["states"] = {
        "B_received_in_session": sum(r["p2_B_received"] for r in agg),
        "questions_after_change": states["checks"]["p2_questions_after_change"],
        "claude_ms_min": min(ms for r in agg if r["client"] == "claude-code" for ms in r["ms_signal_to_list"]),
        "claude_ms_max": max(ms for r in agg if r["client"] == "claude-code" for ms in r["ms_signal_to_list"]),
        "cursor_primary_reps": sum(r["n"] for r in agg if r["client"] == "cursor-agent"),
        "attempts_with_discarded": states["checks"]["primary_repetitions"] + 1,
    }
    ag = load("tool-change/evidence/primary-20261015/coding/agreement.json")
    pre = ag["author_vs_llm (preregistered kappa)"]
    dis = rows("tool-change/evidence/primary-20261015/coding/disagreements-resolved.csv")
    three = load("tool-change/evidence/primary-20261015/coding/codex/agreement-three.json")
    out["coding"] = {"kappa_author_local": pre["kappa"], "n": pre["n"],
                     "identical": round(pre["agreement"] * pre["n"]),
                     "disagreements": len(pre["disagreements"]),
                     "disagreements_packet_line": sum("packet line" in r["evidence"] for r in dis),
                     "resolved_as_author": sum(r["resolved"] == r["author"] for r in dis),
                     "codex_vs_author_kappa": three["2a_codex_vs_author"]["kappa"],
                     "codex_vs_author_agree": round(three["2a_codex_vs_author"]["raw_agreement"]
                                                    * three["2a_codex_vs_author"]["n"]),
                     "fleiss_three": three["3_fleiss_three_coders"]["kappa"]}
    pc = rows("tool-change/evidence/positive-control-20261028/coded.csv")
    out["positive_control"] = {"cells": len(pc),
                               "clients_question_captured": sum(int(r["p2_approvals"]) + int(r["p3_approvals"]) > 0
                                                                and r["p2_outcome"] != "silent-accept"
                                                                for r in pc if int(r["p1_approvals"]) > 0)}
    ow = load("tool-change/evidence/open-weight-20261024/RESULTS.json")
    out["open_weight"] = {"clients": len({c["client"] for c in ow["cells"]}),
                          "reps_per_cell": max(Counter((c["client"], c["signal"]) for c in ow["cells"]).values())}
    return out


# ---------------------------------------------------------------------------------------------------------------- RQ4
def rq4():
    cov = load("defence-coverage/results-20261024/coverage.json")
    ag = cov["agreement_before_adjudication"]["listed_servers"]
    names = {"azure-devops-mcp": "azure_devops", "github-mcp-server": "github", "sentry-mcp": "sentry",
             "aws-iac-mcp-server": "aws_iac", "mssql-mcp-server": "aws_sql_server", "oracle-mcp-server": "aws_oracle"}
    out = {"servers": cov["all_A"]["summary"]["servers"], "registered_tools": ag["n_joined"],
           "agreement": {k: {"raw": ag[k]["raw_agreement"], "kappa": ag[k]["kappa"]}
                         for k in ("class", "protection", "vendor_only")},
           "adjudicated": cov["adjudicated"]}
    for part in ("all_A", "without_vendor_only"):
        s = cov[part]["summary"]
        out[part] = {"per_server": {names[k]: v for k, v in cov[part]["per_server"].items()},
                     "mean_full": s["mean_full"], "median_full": s["median_full"],
                     "mean_any": s["mean_any"], "median_any": s["median_any"],
                     "pooled_full": s["pooled_full"][0], "pooled_any": s["pooled_any"][0], "tools": s["pooled_full"][1],
                     "pooled_none": s["pooled_full"][1] - s["pooled_any"][0],
                     "not_fully_covered": s["pooled_full"][1] - s["pooled_full"][0]}
    out["vendor_only_tools"] = out["all_A"]["tools"] - out["without_vendor_only"]["tools"]
    adj = rows("defence-coverage/results-20261024/adjudication.csv")
    out["adjudication"] = {
        "disputed": len(adj),
        "third_reading_accepted": sum(r["note"].startswith("[proposta accettata]") for r in adj),
        "protection_only_second": sum(r["decision_protection"] == r["second_protection"] != r["first_protection"]
                                      for r in adj),
        "protection_only_first": sum(r["decision_protection"] == r["first_protection"] != r["second_protection"]
                                     for r in adj)}
    pd = rows("defence-coverage/partial-posthoc/PARTIAL-DETAIL.csv")
    gh_label = sum(r["server"] == "github-mcp-server" and r["census_protection"] == "partial"
                   and r["partial_type"].startswith("T2 provenance label only") for r in pd)
    gh = cov["all_A"]["per_server"]["github-mcp-server"]
    out["github_label_only"] = {"partial_tools": gh["partial"], "label_only": gh_label,
                                "pooled_any_if_none": cov["all_A"]["summary"]["pooled_any"][0] - gh_label,
                                "github_any_if_none": gh["full"] + gh["partial"] - gh_label}
    md = (ROOT / "defence-coverage/partial-posthoc/RECLASSIFICATION-SUGGESTIONS-v1.md").read_text(encoding="utf-8")
    pooled_any = [int(m[1]) for m in re.finditer(r"\| \d+/138, (\d+)/138 \(", md)]
    med = [m[1] for m in re.finditer(r"Medians over servers stay at\s+([0-9.]+)%", md)]
    out["reclassification"] = {"pooled_any_max_after": max(pooled_any[1:]), "pooled_any_min_after": min(pooled_any[1:]),
                               "median_any_percent": float(med[0])}
    return out


# ---------------------------------------------------------------------------------------------------------------- RQ5
def rq5():
    h5 = load("telemetry/evidence/scores-20261024/h5-author.json")
    pairs = h5["pairs"]
    measurable = [p for p in pairs.values() if p["measurable"]]
    out = {"pairs": len(pairs), "clients": len({p["client"] for p in pairs.values()}),
           "event_types": len(h5["event_types"]),
           "measurable_pairs": len(measurable), "no_event_pairs": len(h5["not_measurable"]),
           "told_apart": sum(p["tells_apart"] is True for p in measurable),
           "not_told_apart": sum(p["tells_apart"] is False for p in measurable),
           "measurable_per_event": {k.replace("-", "_"): v["measurable_pairs"] for k, v in h5["event_types"].items()},
           "undistinguished_per_event": {k.replace("-", "_"): sum(p["event"] == k and p["tells_apart"] is False
                                                                for p in measurable) for k in h5["event_types"]},
           "detected": {k.replace("/", "__").replace("-", "_"): dict(zip(("runs", "of"), map(int, p["detected"].split("/"))))
                        for k, p in pairs.items()},
           "announced_detected_runs": sum(int(p["detected"].split("/")[0]) for p in pairs.values()
                                          if p["event"] == "q3-announced")}
    out["alert_windows"] = sum(int(p["fp_windows"].split("/")[0]) for p in pairs.values())
    out["holdout_windows_per_client"] = int(next(iter(pairs.values()))["fp_windows"].split("/")[1])
    agr = load("telemetry/evidence/scores-20261024/agreement.json")
    a, n = agr["agreement"].split("/")
    out["second_author_agree"], out["second_author_pairs"] = int(a), int(n)
    cp = load("telemetry/coverage-posthoc/COVERAGE-POSTHOC.json")
    told = [p for p in cp["pairs"].values() if p["posthoc_label"] == "told apart, false positives assessed"]
    out["coverage"] = {
        "min_covered_windows": cp["min_covered_windows"],
        "told_apart_fp_assessed": cp["summary"]["told_apart_fp_assessed"],
        "covered_min": min(p["fp_covered_windows"]["n"] for p in told),
        "covered_max": max(p["fp_covered_windows"]["n"] for p in told),
        "goose_covered": max(p["windows_covered_rule_source"] or 0 for k, p in cp["pairs"].items() if k.startswith("goose/")),
        "wilson_upper_60": cp["pairs"]["claude-code/q3-silent"]["fp_all_windows"]["wilson95_upper"],
        "wilson_upper_46": cp["pairs"]["claude-code/q3-announced"]["fp_covered_windows"]["wilson95_upper"],
        "covered_46": cp["pairs"]["claude-code/q3-announced"]["fp_covered_windows"]["n"],
        "event_runs": sum(p["event_runs_planned"] for p in cp["pairs"].values()),
    }
    host = load("telemetry/evidence/scores-20261024/scores-host.json")
    out["host"] = {k.split("/")[1].replace("-", "_"): {"detected": host[k]["events"]["detected"],
                                                       "scored": host[k]["events"]["scored"]}
                   for k in ("host/q5-start", "host/q3-announced", "host/q3-silent")}
    hs = host["host/q5-start"]["holdout"]
    out["host"]["holdout_windows"] = hs["windows"]
    out["host"]["holdout_fp_windows"] = hs["fp_windows"]
    out["host"]["covered_windows"] = hs["covered_windows"]
    out["host"]["holdout_hours"] = hs["hours"]
    return out


# ------------------------------------------------------------------------------------------------------------ design
def design():
    chron = rows("preregistration/chronology.csv")
    t = Counter(r["timing"] for r in chron)
    return {"chronology": {"decisions": len(chron), "prospective": t["prospective"],
                           "during_collection": t["during collection"], "after_results": t["after results"]}}


def main():
    if sys.argv[1:] == ["--inputs"]:
        print("\n".join(INPUTS))
        return
    for p in INPUTS:
        if not (ROOT / p).exists():
            sys.exit(f"missing input: {p}")
    print(json.dumps({"rq1": rq1(), "rq2": rq2(), "rq3": rq3(), "rq4": rq4(), "rq5": rq5(), "design": design()},
                     indent=1, sort_keys=True))


if __name__ == "__main__":
    main()
