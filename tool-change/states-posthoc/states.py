#!/usr/bin/env python3
"""RQ3 observable states, per repetition (POST HOC, EXPLORATORY; written 31 October 2026, after all RQ3 results were known).

Reads only the published evidence (row.json, q3-server.log, capture file names and texts) and writes STATES.json and
STATES.md next to this script. It changes no data, no outcome and no preregistered analysis: the primary RQ3 result is the
coded matrix (evidence/primary-20261015/analysis, coding/). This script only re-expresses each repetition as a sequence of
observable states and says, for each state, whether the evidence observes it.

States (phase 2 = same session after the change; phase 3 = after reopening, exploratory in the protocol):
  initial approval      question shown at the first call (row.json p1_approvals) and the option chosen (persistent_approval)
  change A->B           server log: definition-changed event (from, to, sha256)
  notification          server log: signal-delivered / signal-not-deliverable (signal cells only)
  list re-requested     server log: a tools/list served after the change, in the phase window, and what was served (A/B)
  definition received   B served to the client by a tools/list in the window (protocol level)
  definition loaded     only where a client action shows it: a call to a name that exists only in B (rename), or a client
                        notice about updated tools; otherwise "not observed" (or "no": B was never served in that session)
  sent to model         not observed: no recording proxy in these cells (the open-weight cells, D39, are separate)
  tool called           server log tools/call in the window: name called, known or unknown, the server's state at the call,
                        and the last definition the client had been served before the call (A unless B was served)
  question shown        runner observation (p*_approvals, p*_notice_seen) cross-checked with the capture files

Run:  python3 -I states.py            (no arguments; paths are relative to this file)
"""
import json, re
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
EV = HERE.parent / "evidence"
PRIMARY = EV / "primary-20261015"
CONTROL = EV / "positive-control-20261028"
FAILED = PRIMARY / "failed-attempts" / "qwen__none__description__r4__tentativo1"
ENDS = {"stdin-closed", "sigterm", "sigint"}
CLIENT_NAMES = {"claude-code": "Claude Code", "codex": "Codex CLI", "cursor-agent": "Cursor CLI", "gemini": "Gemini CLI",
                "goose": "Goose", "qwen": "Qwen Code"}


def ts(s):
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def load(d):
    row = json.loads((d / "row.json").read_text())
    ev = []
    for line in (d / "q3-server.log").read_text().splitlines():
        try:
            e = json.loads(line)
        except json.JSONDecodeError:
            continue
        if "ts" in e:
            e["_t"] = ts(e["ts"])
            ev.append(e)
    return row, ev


def group_of(row):
    """Approval group from the first call: no question / persistent / session (from row.json, not from the paper)."""
    if row.get("p1_approvals", 0) == 0:
        return "no-initial-question"
    return "session-approval" if "session" in row.get("persistent_approval", "").lower() else "persistent-approval"


def captures(d, row, phase):
    return [c for c in row.get("captures", []) if f"-{phase}-" in c]


def phase_states(d, row, ev, phase, start, end, change):
    w = [e for e in ev if start <= e["_t"] < end]
    lists = [e for e in w if e.get("event") == "served-list"]
    calls = [e for e in w if e.get("event") == "tools/call"]
    b_names = None
    for e in ev:
        if e.get("event") == "definition-changed":
            b_names = e.get("names")
    # last definition served to the client before each call (any server process of this repetition; before the phase, A)
    out_calls = []
    for c in calls:
        prior = [e for e in ev if e.get("event") == "served-list" and e["_t"] < c["_t"]]
        last = prior[-1]["served"] if prior else None
        out_calls.append({"name": c.get("called"), "known": bool(c.get("known")), "server_state": c.get("served_state"),
                          "last_served_to_client": last,
                          "name_only_in_B": bool(change == "name" and b_names and c.get("called") in b_names)})
    served = [e.get("served") for e in lists]
    received_b = "B" in served
    caps = captures(d, row, phase)
    approvals = row.get(f"{phase}_approvals", 0)
    notice = bool(row.get(f"{phase}_notice_seen", False))
    cap_text = ""
    for c in caps:
        p = d / c
        if p.exists():
            cap_text += p.read_text(errors="replace")
    notice_text = "Tools updated for server" in cap_text
    if any(c["name_only_in_B"] and c["known"] for c in out_calls):
        loaded = "observed (called a name that exists only in B)"
    elif received_b and notice_text:
        loaded = "indirect (client notice about updated tools after B was served)"
    elif received_b:
        loaded = "not observed (B received; client-side use not visible)"
    else:
        loaded = "no (B never served in this window)"
    acted_on = sorted({c["last_served_to_client"] or "?" for c in out_calls if c["known"]})
    return {
        "lists_served": "".join(x or "?" for x in served) or "-",
        "list_re_requested": bool(lists),
        "first_list_ms_after_window_start": round((lists[0]["_t"] - start).total_seconds() * 1000) if lists else None,
        "definition_received_B": received_b,
        "definition_loaded": loaded,
        "definition_sent_to_model": "not observed (no recording proxy in these cells)",
        "calls": out_calls,
        "ok_calls": sum(c["known"] for c in out_calls),
        "unknown_tool_calls": sum(not c["known"] for c in out_calls),
        "definition_acted_on_at_ok_calls": "+".join(acted_on) or "-",
        "question_shown": approvals > 0,
        "approvals_recorded": approvals,
        "notice_shown": notice,
        "approval_capture_present": any("approval" in c for c in caps),
        "notice_capture_present": any("notice" in c for c in caps),
        "notice_text_in_captures": notice_text,
        "servers_started": len({e["pid"] for e in w if e.get("event") == "start"}),
    }


def repetition(d):
    row, ev = load(d)
    change = row["change"]
    flip, p2_end = ts(row["flip_at"]), ts(row.get("p2_end_at") or row["reopen_at"])
    reopen, p3_end = ts(row["reopen_at"]), ts(row.get("p3_end_at") or row["t_end"])
    p1 = phase_states(d, row, ev, "p1", ts(row["t_start"]), flip, change)
    changed = [e for e in ev if e.get("event") == "definition-changed"]
    sig = [e for e in ev if e.get("event") in ("signal-delivered", "signal-not-deliverable") and flip <= e["_t"] < p2_end]
    if row["signal"] == "list_changed":
        if any(e["event"] == "signal-delivered" for e in sig):
            e = next(e for e in sig if e["event"] == "signal-delivered")
            notif = "delivered (" + "+".join(sorted({x.get("era", "?") for x in e.get("delivered", [])})) + ")"
        elif sig:
            notif = "not deliverable (no channel: no subscription)"
        else:
            notif = "not observed"
    else:
        notif = "n/a (no-signal cell)"
    p2 = phase_states(d, row, ev, "p2", flip, p2_end, change)
    if row["signal"] == "list_changed" and sig and p2["list_re_requested"]:
        first_list = next(e for e in ev if e.get("event") == "served-list" and flip <= e["_t"] < p2_end)
        p2["first_list_ms_after_signal"] = round((first_list["_t"] - sig[0]["_t"]).total_seconds() * 1000)
    p3 = phase_states(d, row, ev, "p3", reopen, p3_end, change)
    return {
        "id": d.name, "client": row["client"], "signal": row["signal"], "change": change, "rep": row["rep"],
        "version": row.get("version_before"), "version_unchanged": row.get("version_before") == row.get("version_after"),
        "group": group_of(row),
        "initial": {"question_shown": row.get("p1_approvals", 0) > 0, "option_recorded": row.get("persistent_approval"),
                    "first_call_ok_with_A": p1["ok_calls"] > 0 and p1["definition_acted_on_at_ok_calls"] == "A"},
        "change_A_to_B": {"observed": bool(changed), "from": changed[0].get("from") if changed else None,
                          "to": changed[0].get("to") if changed else None,
                          "names_after": changed[0].get("names") if changed else None},
        "notification": notif,
        "p2": p2, "p3": p3,
    }


def failed_attempt():
    """The discarded first attempt of qwen/none/r4 (D19). Only captures survive: no row.json, no server log."""
    out = {"id": FAILED.name, "client": "qwen", "signal": "none", "change": "description", "rep": 4,
           "evidence": sorted(p.name for p in FAILED.iterdir() if p.suffix == ".txt")}
    p1 = (FAILED / "qwen__none__r4__01-p1-end.txt").read_text(errors="replace")
    p2q = (FAILED / "qwen__none__r4__03-p2-approval.txt").read_text(errors="replace")
    out["initial"] = {"question_shown": "Allow execution" in p1 or "Waiting for user confirmation" in p1,
                      "first_call_shown_ok": bool(re.search(r"q3_noop .*\n\s+ok", p1))}
    out["change_A_to_B"] = "not observable (server log not kept for this attempt)"
    out["notification"] = "n/a (no-signal cell)"
    out["p2"] = {
        "list_re_requested": "not observable (no server log)",
        "definition_received_B": "not observable", "definition_loaded": "not observable",
        "definition_sent_to_model": "not observed",
        "tool_called": "no call reached completion in the captures; the runner stopped at the question",
        "question_shown": "Allow execution of MCP tool" in p2q,
        "question_cause_shown_by_client": ("classifier unavailable"
                                           if "Classifier stage 1 unavailable" in p2q else "not stated"),
        # words that would tie the question to the change; the banner's "(/model to change)" and the option
        # "No, suggest changes" are UI text present in every Qwen Code screen and are removed first
        "question_mentions_change": bool(re.search(r"chang|updat|modif|definition|description",
                                                   p2q.replace("/model to change", "").replace("suggest changes", ""),
                                                   re.I)),
    }
    out["p3"] = "not reached"
    return out


def tally(reps, key):
    t = {}
    for r in reps:
        k = key(r)
        t[k] = t.get(k, 0) + 1
    return t


def main():
    reps = [repetition(d) for d in sorted(PRIMARY.iterdir()) if (d / "row.json").exists()]
    ctl = [repetition(d) for d in sorted(CONTROL.iterdir()) if (d / "row.json").exists()]
    fa = failed_attempt()
    assert len(reps) == 60, len(reps)

    def cellkey(r):
        return (r["group"], r["client"], r["signal"])

    agg = {}
    for r in reps:
        k = "|".join(cellkey(r))
        a = agg.setdefault(k, {"group": r["group"], "client": r["client"], "signal": r["signal"], "n": 0,
                               "initial_question": 0, "change_observed": 0, "notification": {},
                               "p2_list_re_requested": 0, "p2_B_received": 0, "p2_loaded": {}, "p2_ok_call": 0,
                               "p2_acted_on": {}, "p2_question": 0, "p2_notice": 0,
                               "p3_B_received": 0, "p3_question": 0, "p3_acted_on": {}, "ms_signal_to_list": []})
        a["n"] += 1
        a["initial_question"] += r["initial"]["question_shown"]
        a["change_observed"] += r["change_A_to_B"]["observed"]
        a["notification"][r["notification"]] = a["notification"].get(r["notification"], 0) + 1
        p2, p3 = r["p2"], r["p3"]
        a["p2_list_re_requested"] += p2["list_re_requested"]
        a["p2_B_received"] += p2["definition_received_B"]
        a["p2_loaded"][p2["definition_loaded"]] = a["p2_loaded"].get(p2["definition_loaded"], 0) + 1
        a["p2_ok_call"] += p2["ok_calls"] > 0
        a["p2_acted_on"][p2["definition_acted_on_at_ok_calls"]] = a["p2_acted_on"].get(p2["definition_acted_on_at_ok_calls"], 0) + 1
        a["p2_question"] += p2["question_shown"]
        a["p2_notice"] += p2["notice_shown"]
        a["p3_B_received"] += p3["definition_received_B"]
        a["p3_question"] += p3["question_shown"]
        a["p3_acted_on"][p3["definition_acted_on_at_ok_calls"]] = a["p3_acted_on"].get(p3["definition_acted_on_at_ok_calls"], 0) + 1
        if "first_list_ms_after_signal" in p2:
            a["ms_signal_to_list"].append(p2["first_list_ms_after_signal"])

    checks = {
        "primary_repetitions": len(reps),
        "all_first_calls_ok_with_A": all(r["initial"]["first_call_ok_with_A"] for r in reps),
        "all_changes_observed_A_to_B": all(r["change_A_to_B"]["observed"] and r["change_A_to_B"]["from"] == "A"
                                           and r["change_A_to_B"]["to"] == "B" for r in reps),
        "p2_questions_after_change": sum(r["p2"]["question_shown"] for r in reps),
        "p2_runner_vs_capture_disagreements": [r["id"] for r in reps for ph in ("p2", "p3")
                                               if r[ph]["question_shown"] != r[ph]["approval_capture_present"]
                                               or r[ph]["notice_shown"] != r[ph]["notice_capture_present"]],
        "versions_unchanged": all(r["version_unchanged"] for r in reps),
    }
    primary_q = checks["p2_questions_after_change"]
    sensitivity = {
        "primary": {"attempts": 60, "question_after_change_same_session": primary_q,
                    "change_related_question": primary_q, "classifier_unavailable_message": 0},
        "including_discarded_attempt": {
            "attempts": 61,
            "question_after_change_same_session": primary_q + int(fa["p2"]["question_shown"]),
            "change_related_question": f"{primary_q} in the 60 retained; unknown for the discarded attempt (no server log)",
            "classifier_unavailable_message": int(fa["p2"]["question_shown"]
                                             and fa["p2"]["question_cause_shown_by_client"] == "classifier unavailable"),
            "clients_with_any_question_after_change": sorted({r["client"] for r in reps if r["p2"]["question_shown"]}
                                                             | ({"qwen"} if fa["p2"]["question_shown"] else set())),
            "note": ("Counting the discarded attempt as a question would give one client (Qwen Code) one question in 6 "
                     "no-signal attempts; H3's first clause (at most one client requires re-approval) would still hold. "
                     "The client's own message attributes the question to its classifier being unavailable and does "
                     "not mention a change; server-side states of that attempt are not observable."),
        },
    }
    data = {"note": "POST HOC, EXPLORATORY (31 Oct 2026). Re-expresses published RQ3 evidence as observable states; "
                    "the primary result is unchanged.",
            "checks": checks, "aggregate_primary": list(agg.values()), "sensitivity": sensitivity,
            "failed_attempt": fa, "positive_control_D52": ctl, "primary": reps}
    (HERE / "STATES.json").write_text(json.dumps(data, indent=1, sort_keys=False, default=str) + "\n")
    (HERE / "STATES.md").write_text(render(data))
    print(json.dumps(checks))


def fmt(d):
    return "; ".join(f"{k} {v}" for k, v in sorted(d.items()))


def render(data):
    L = ["# RQ3 observable states (post hoc, exploratory)", "",
         "Written 31 October 2026, after all RQ3 results were known; generated by `states.py` from the published evidence "
         "only. It changes no outcome: the primary RQ3 result is the coded matrix of `evidence/primary-20261015`. "
         "Phase 2 is the same session after the change; phase 3 is after reopening (exploratory in the protocol). "
         "\"Received B\" means the server served definition B in a `tools/list` response; whether the client then used "
         "it is observable only through a client action (a call to a name that exists only in B, or a client notice). "
         "What reached the model is not observed in these cells (no recording proxy; see the open-weight cells, D39). "
         "\"Acted on\" is the last definition the client had been served before a successful call: for a description "
         "change the call carries the same name, so this is inferred from the server log, not observed in the client.", "",
         "## Checks", ""]
    for k, v in data["checks"].items():
        L.append(f"- {k}: {v}")
    L += ["", "## Primary matrix (60 repetitions), per client and signal", "",
          "| Group | Client | Signal | n | First-call question | Change A→B | Notification | P2 list re-requested "
          "| P2 received B | P2 loaded | P2 acted on | P2 question | P2 notice | P3 received B | P3 question | P3 acted on "
          "| ms signal→list |",
          "|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    order = {"no-initial-question": 0, "persistent-approval": 1, "session-approval": 2}
    for a in sorted(data["aggregate_primary"], key=lambda a: (order[a["group"]], a["client"], a["signal"])):
        ms = a["ms_signal_to_list"]
        L.append(f"| {a['group']} | {CLIENT_NAMES[a['client']]} | {a['signal']} | {a['n']} | {a['initial_question']}/{a['n']} "
                 f"| {a['change_observed']}/{a['n']} | {fmt(a['notification'])} | {a['p2_list_re_requested']}/{a['n']} "
                 f"| {a['p2_B_received']}/{a['n']} | {fmt(a['p2_loaded'])} | {fmt(a['p2_acted_on'])} "
                 f"| {a['p2_question']}/{a['n']} | {a['p2_notice']}/{a['n']} | {a['p3_B_received']}/{a['n']} "
                 f"| {a['p3_question']}/{a['n']} | {fmt(a['p3_acted_on'])} | {(str(min(ms)) + '–' + str(max(ms))) if ms else '-'} |")
    L += ["", "Definition sent to the model: not observed in any of the 60 repetitions.", "",
          "## Per repetition (primary)", "",
          "| Repetition | Group | Notification | P2 lists | P2 calls (name, known, last served) | P2 question/notice "
          "| P3 lists | P3 question |", "|---|---|---|---|---|---|---|---|"]
    for r in data["primary"]:
        calls = ", ".join(f"{c['name']}/{'ok' if c['known'] else 'unknown'}/{c['last_served_to_client']}" for c in r["p2"]["calls"]) or "none"
        L.append(f"| {r['id']} | {r['group']} | {r['notification']} | {r['p2']['lists_served']} | {calls} "
                 f"| {int(r['p2']['question_shown'])}/{int(r['p2']['notice_shown'])} | {r['p3']['lists_served']} "
                 f"| {int(r['p3']['question_shown'])} |")
    L += ["", "## Positive control D52 (rename, exploratory; one cell per client, Cursor CLI not run)", "",
          "| Client | Group | Notification | P2 lists | P2 calls (name, known, last served) | P2 loaded | P2 question/notice "
          "| P3 lists | P3 calls | P3 question |", "|---|---|---|---|---|---|---|---|---|---|"]
    for r in data["positive_control_D52"]:
        c2 = ", ".join(f"{c['name']}/{'ok' if c['known'] else 'unknown'}/{c['last_served_to_client']}" for c in r["p2"]["calls"]) or "none"
        c3 = ", ".join(f"{c['name']}/{'ok' if c['known'] else 'unknown'}/{c['last_served_to_client']}" for c in r["p3"]["calls"]) or "none"
        L.append(f"| {CLIENT_NAMES[r['client']]} | {r['group']} | {r['notification']} | {r['p2']['lists_served']} | {c2} "
                 f"| {r['p2']['definition_loaded']} | {int(r['p2']['question_shown'])}/{int(r['p2']['notice_shown'])} "
                 f"| {r['p3']['lists_served']} | {c3} | {int(r['p3']['question_shown'])} |")
    s = data["sensitivity"]
    fa = data["failed_attempt"]
    L += ["", "In D52 a question after the change is the first approval of a new name, not a second approval of a changed "
          "definition.", "", "## Sensitivity: the discarded first attempt of Qwen Code, no signal, repetition 4 (D19)", "",
          f"Evidence kept: {', '.join(fa['evidence'])} (no row.json, no server log). First call shown as successful: "
          f"{fa['initial']['first_call_shown_ok']}; question at the first call: {fa['initial']['question_shown']}. "
          f"After the change: question shown {fa['p2']['question_shown']}; cause stated by the client: "
          f"{fa['p2']['question_cause_shown_by_client']}; message mentions a change: {fa['p2']['question_mentions_change']}. "
          "List re-requested, definition received or loaded, tool called: not observable.", "",
          "| Analysis | Attempts | Question after change (same session) | Caused by the change | Client message names classifier unavailability |",
          "|---|---|---|---|---|",
          f"| Primary (as preregistered + D19) | {s['primary']['attempts']} | {s['primary']['question_after_change_same_session']} "
          f"| {s['primary']['change_related_question']} | {s['primary']['classifier_unavailable_message']} |",
          f"| Including the discarded attempt | {s['including_discarded_attempt']['attempts']} "
          f"| {s['including_discarded_attempt']['question_after_change_same_session']} "
          f"| {s['including_discarded_attempt']['change_related_question']} "
          f"| {s['including_discarded_attempt']['classifier_unavailable_message']} |", "",
          s["including_discarded_attempt"]["note"], "The primary result is unchanged.", ""]
    return "\n".join(L)


if __name__ == "__main__":
    main()
