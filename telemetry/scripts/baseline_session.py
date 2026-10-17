#!/usr/bin/env python3
"""Runs INSIDE the disposable VM: one baseline session of scripted normal use for one terminal client (D13, D24 point 4).

Cycles of the fixed tasks in ../baseline/tasks.json until --minutes are over: open the client in the trusted test folder
~/q3-repo, explain a file, run the tests, edit a file, call the known q3-lab tool (definition A, never changed), close the client.
Permission questions for commands and edits are answered "allow once" (../baseline/clients.json); the MCP tool approval and the
client's ready pattern are the frozen Q3 ones (tool-change/scripts/q3-clients.json). Every action is written with its time to
timeline.jsonl, which the analysis uses to place the one-minute windows; every screen at the end of a task is kept.

  python3 baseline_session.py --client codex --part dev --minutes 60 --out ~/q4-out
  python3 baseline_session.py --client codex --part setup --minutes 6 --out ~/q4-out    # exploratory set-up session

The q3-lab server is set to definition A with no signal before the first cycle, and checked again at the end: a session in which
the server log shows any definition other than A is invalid for the baseline. A session is also invalid unless the normal use
actually happened (tasks.json "workload_success": share of tasks completed, known-server calls per cycle). session.json records
both checks; the host keeps an invalid session as an attempt and does not count it. The local-engine repetition (D13 point 1)
is not implemented here: there is no part for it, and it is reported as not done unless a later, reviewed change adds it.
"""
import argparse, importlib.util, json, re, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEL = HERE.parent
_spec = importlib.util.spec_from_file_location("run_q3_cell", TEL.parent / "tool-change/scripts/run_q3_cell.py")
q3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q3)
_qspec = importlib.util.spec_from_file_location("quota", HERE / "quota.py")
quota = importlib.util.module_from_spec(_qspec)
_qspec.loader.exec_module(quota)
# The lab's known tool. Only a question that names it gets the frozen Q3 MCP approval; every other question (commands, edits)
# gets "allow once". For Claude Code both questions read "Do you want to proceed?", and the Q3 keys give "don't ask again".
LAB_TOOL = re.compile(r"q3_noop|q3-lab")
QUESTION_LINES = 25  # the bottom of the screen, where the clients draw their questions
DIALOG_LINES = 10    # the active dialog: the lines just above the question line
# Headings of command and edit dialogs: when one is in the active dialog, the question is never an MCP approval, even if the lab
# tool's name appears (recent tool output, or a command that mentions it).
# A persistent approval needs a positive sign that the active dialog is an MCP tool dialog; anything ambiguous gets "allow once".
MCP_DIALOG = re.compile(r"\(MCP\)|MCP server|MCP tool|mcp__", re.I)
COMMAND_DIALOG = re.compile(r"Bash command|Edit file|Create file|Write file|Run this command|Would you like to run the following command|"
                            r"Would you like to make the following edits|Apply this change|shell command", re.I)


class Session:
    def __init__(self, client, part, outdir, tasks, perms, cell=None):
        self.client, self.part, self.out = client, part, outdir
        self.cell = cell or f"baseline-{client}-{part}"
        self.spec = q3.CLIENTS[client]
        self.tasks, self.perm = tasks, perms.get(client, {})
        self.generic = perms.get("_generic")
        self.timeline = open(outdir / "timeline.jsonl", "a")
        self.n_caps = 0
        self.quota_message = None

    def log(self, **kw):
        self.timeline.write(json.dumps({"ts": q3.now(), "epoch": round(time.time(), 3), **kw}) + "\n")
        self.timeline.flush()

    def capture(self, label):
        self.n_caps += 1
        name = f"{self.client}__{self.part}__{self.n_caps:04d}-{label}.txt"
        (self.out / "screens" / name).write_text(q3.screen())
        return name

    def answer_questions(self, s, cycle, task):
        """Answer a permission question on screen, if any. Returns the kind answered, or None.
        The frozen Q3 MCP approval is used only for a question that names the lab tool; command and edit questions are always
        answered "allow once", so that nothing is allowed permanently (D24 point 4)."""
        # tmux captures the whole pane: drop the blank lines below the last drawn line first (a 50-line pane can end with
        # 20+ empty lines, which would push the question out of the window)
        drawn = s.rstrip().splitlines()
        lines = drawn[-QUESTION_LINES:]
        bottom = "\n".join(lines)
        if self.spec.get("approve"):
            hits = [i for i, l in enumerate(lines) if re.search(self.spec["approve"], l)]
            header = self.perm.get("mcp_header")
            if hits and header:  # the active dialog = the lines just above the last question line, the question included
                window = lines[max(0, hits[-1] - DIALOG_LINES):hits[-1] + 1]
                # persistent approval only on positive identification: the client's exact MCP dialog line for the lab tool
                # (baseline/clients.json "mcp_header") inside the active dialog, and no command or edit heading at the bottom
                if any(re.search(header, l) for l in window) and not COMMAND_DIALOG.search(bottom):
                    q3.keys(*(self.spec.get("approve_keys") or ("Enter",)))
                    return "mcp-approval"
        if self.perm.get("allow") and re.search(self.perm["allow"], bottom):
            q3.keys(*self.perm["allow_keys"])
            return "allow-once"
        if self.generic and re.search(self.generic, "\n".join(drawn[-12:])):  # bottom of the drawn screen only
            q3.keys("Enter")
            return "unexpected-question"
        return None

    def quota_hit(self, s, cycle, task_id):
        """True (and the session ends) when the screen shows a quota or rate-limit message."""
        msg = quota.find(self.client, s)
        if msg and not self.quota_message:
            self.quota_message = msg
            self.log(action="quota", cycle=cycle, task=task_id, message=msg, screen=self.capture("quota"))
        return bool(msg)

    def server_calls(self):
        return sum(1 for e in q3.events() if e.get("event") == "tools/call" and e.get("cell") == self.cell)

    def evidence(self, task, cycle, t_prompt, calls_before):
        """Whether the action the task asked for really happened (tasks.json "evidence"); the ready screen alone is not enough."""
        kind = task.get("evidence", "answered")
        if kind == "answered":
            return True
        if kind == "test-run":
            f = q3.REPO / ".q4-test-runs"
            return f.exists() and any(float(x) >= t_prompt - 1 for x in f.read_text().split() if x.replace(".", "", 1).isdigit())
        if kind == "file-contains":
            f = q3.REPO / task["file"]
            return f.exists() and task["contains"].replace("{k}", str(cycle)) in f.read_text()
        if kind == "server-call":
            return self.server_calls() > calls_before
        raise ValueError(f"unknown evidence {kind}")

    def do_task(self, cycle, task, timeout, idle_s):
        """True when the client is back at its ready screen with a stable screen before the timeout AND the task's evidence is
        there (a refused edit or a failed command returns to the ready screen too)."""
        prompt = task["prompt"].replace("{k}", str(cycle))
        t_prompt, calls_before = time.time(), self.server_calls()
        q3.type_text(prompt)
        self.log(action="prompt", cycle=cycle, task=task["id"])
        t0, last, stable_since = time.time(), None, time.time()
        while time.time() - t0 < timeout:
            time.sleep(1.5)
            s = q3.screen()
            if self.quota_hit(s, cycle, task["id"]):
                return False
            if q3.answer_noise(s):
                continue
            kind = self.answer_questions(s, cycle, task)
            if kind:
                self.log(action=kind, cycle=cycle, task=task["id"], screen=self.capture(kind))
                time.sleep(2)
                continue
            if s != last:
                last, stable_since = s, time.time()
            elif time.time() - stable_since >= idle_s and re.search(self.spec["ready"], s):
                ok = self.evidence(task, cycle, t_prompt, calls_before)
                self.log(action="done" if ok else "no-evidence", cycle=cycle, task=task["id"], seconds=round(time.time() - t0, 1),
                         screen=self.capture(f"c{cycle}-{task['id']}"))
                return ok
        self.log(action="timeout", cycle=cycle, task=task["id"], screen=self.capture(f"c{cycle}-{task['id']}-timeout"))
        return False

    def run(self, minutes, cfg):
        """Returns (cycles, tasks prompted, tasks done). A cycle whose client never gets ready counts all its tasks as failed."""
        deadline = time.time() + minutes * 60
        cycle = prompted = done = 0
        while time.time() < deadline:
            cycle += 1
            q3.launch(self.spec["cmd"])
            self.log(action="open", cycle=cycle)
            ready = q3.wait_ready(self.spec, 90, [], f"c{cycle}", self.out / "screens", {"client": self.client, "signal": "baseline", "rep": cycle})
            if not ready:
                self.log(action="not-ready", cycle=cycle)
            self.quota_hit(q3.screen(), cycle, None)  # a quota message can sit next to the ready marker
            for task in self.tasks:
                if time.time() >= deadline or self.quota_message:
                    break
                prompted += 1
                if ready and self.do_task(cycle, task, cfg["task_timeout_s"], cfg["idle_s"]):
                    done += 1
                elif not ready:
                    self.log(action="skipped-not-ready", cycle=cycle, task=task["id"])
            self.quota_hit(q3.screen(), cycle, None)  # last look before the screen is destroyed, deadline exits included
            q3.kill()
            self.log(action="close", cycle=cycle)
            if self.quota_message:
                break  # stop spending: the session is not valid anyway
            time.sleep(cfg["pause_between_cycles_s"])
        return cycle, prompted, done


def workload(cycles, prompted, done, calls, crit):
    """Whether the normal use happened: share of tasks done and known-server calls per cycle, against fixed thresholds."""
    share = done / prompted if prompted else 0.0
    per_cycle = calls / cycles if cycles else 0.0
    return {"cycles": cycles, "tasks_prompted": prompted, "tasks_done": done, "done_share": share, "known_server_calls": calls,
            "known_server_calls_per_cycle": per_cycle,
            "ok": share >= crit["min_done_share"] and per_cycle >= crit["min_known_server_calls_per_cycle"]}


def validity(events):
    """Definitions served by tools/list in the session, and whether the server logged any change (the server's log records
    every message out with the definition state at that moment)."""
    served = sorted({e.get("state") for e in events if e.get("event") == "out" and e.get("why") == "tools/list"})
    return served, any(e.get("event") == "definition-changed" for e in events)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, choices=list(q3.CLIENTS))
    ap.add_argument("--part", required=True, choices=["setup", "dev", "holdout"])
    ap.add_argument("--minutes", type=float, required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    q3.load_overrides(TEL.parent / "tool-change/scripts/q3-clients.json")
    cfg = json.loads((TEL / "baseline/tasks.json").read_text())
    perms = json.loads((TEL / "baseline/clients.json").read_text())
    outdir = Path(a.out).expanduser() / f"baseline__{a.client}__{a.part}"
    (outdir / "screens").mkdir(parents=True, exist_ok=True)
    for name, text in cfg["setup_files"].items():
        (q3.REPO / name).write_text(text)
    q3.flip_init("none", "description", f"baseline-{a.client}-{a.part}")  # definition A, no signal, for the whole session
    s = Session(a.client, a.part, outdir, cfg["tasks"], perms, cell=f"baseline-{a.client}-{a.part}")
    t_start = time.time()
    s.log(action="session-start", client=a.client, part=a.part, minutes=a.minutes,
          version=q3.sh(q3.CLIENTS[a.client]["version"] + " 2>&1 | head -1").stdout.strip())
    cycles, prompted, done = s.run(a.minutes, cfg)
    events = q3.events()
    served, changed = validity(events)
    calls = sum(1 for e in events if e.get("event") == "tools/call" and e.get("cell") == f"baseline-{a.client}-{a.part}")
    w = workload(cycles, prompted, done, calls, cfg["workload_success"])
    s.log(action="session-end", cycles=cycles, definitions_served=served, definition_changed=changed, workload=w)
    (outdir / "session.json").write_text(json.dumps({"client": a.client, "part": a.part, "minutes": a.minutes, "t_start": t_start,
                                                     "t_end": time.time(), "definitions_served": served,
                                                     "definition_changed": changed, "workload": w,
                                                     "quota_exhausted": bool(s.quota_message), "quota_message": s.quota_message,
                                                     "valid": served in ([], ["A"]) and not changed and w["ok"]
                                                     and not s.quota_message}, indent=1))


if __name__ == "__main__":
    main()
