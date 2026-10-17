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
the server log shows any definition other than A is invalid for the baseline.
"""
import argparse, importlib.util, json, re, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
TEL = HERE.parent
_spec = importlib.util.spec_from_file_location("run_q3_cell", TEL.parent / "tool-change/scripts/run_q3_cell.py")
q3 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(q3)


class Session:
    def __init__(self, client, part, outdir, tasks, perms):
        self.client, self.part, self.out = client, part, outdir
        self.spec = q3.CLIENTS[client]
        self.tasks, self.perm = tasks, perms.get(client, {})
        self.generic = perms.get("_generic")
        self.timeline = open(outdir / "timeline.jsonl", "a")
        self.n_caps = 0

    def log(self, **kw):
        self.timeline.write(json.dumps({"ts": q3.now(), "epoch": round(time.time(), 3), **kw}) + "\n")
        self.timeline.flush()

    def capture(self, label):
        self.n_caps += 1
        name = f"{self.client}__{self.part}__{self.n_caps:04d}-{label}.txt"
        (self.out / "screens" / name).write_text(q3.screen())
        return name

    def answer_questions(self, s, cycle, task):
        """Answer a permission question on screen, if any. Returns the kind answered, or None."""
        if self.spec.get("approve") and re.search(self.spec["approve"], s):
            q3.keys(*(self.spec.get("approve_keys") or ("Enter",)))
            return "mcp-approval"
        if self.perm.get("allow") and re.search(self.perm["allow"], s):
            q3.keys(*self.perm["allow_keys"])
            return "allow-once"
        if self.generic and re.search(self.generic, "\n".join(s.splitlines()[-12:])):  # bottom of the screen only
            q3.keys("Enter")
            return "unexpected-question"
        return None

    def do_task(self, cycle, task, timeout, idle_s):
        prompt = task["prompt"].replace("{k}", str(cycle))
        q3.type_text(prompt)
        self.log(action="prompt", cycle=cycle, task=task["id"])
        t0, last, stable_since = time.time(), None, time.time()
        while time.time() - t0 < timeout:
            time.sleep(1.5)
            s = q3.screen()
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
                self.log(action="done", cycle=cycle, task=task["id"], seconds=round(time.time() - t0, 1),
                         screen=self.capture(f"c{cycle}-{task['id']}"))
                return True
        self.log(action="timeout", cycle=cycle, task=task["id"], screen=self.capture(f"c{cycle}-{task['id']}-timeout"))
        return False

    def run(self, minutes, cfg):
        deadline = time.time() + minutes * 60
        cycle = 0
        while time.time() < deadline:
            cycle += 1
            q3.launch(self.spec["cmd"])
            self.log(action="open", cycle=cycle)
            if not q3.wait_ready(self.spec, 90, [], f"c{cycle}", self.out / "screens", {"client": self.client, "signal": "baseline", "rep": cycle}):
                self.log(action="not-ready", cycle=cycle)
            for task in self.tasks:
                if time.time() >= deadline:
                    break
                self.do_task(cycle, task, cfg["task_timeout_s"], cfg["idle_s"])
            q3.kill()
            self.log(action="close", cycle=cycle)
            time.sleep(cfg["pause_between_cycles_s"])
        return cycle


def validity(events):
    """Definitions served by tools/list in the session, and whether the server logged any change (the server's log records
    every message out with the definition state at that moment)."""
    served = sorted({e.get("state") for e in events if e.get("event") == "out" and e.get("why") == "tools/list"})
    return served, any(e.get("event") == "definition-changed" for e in events)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True, choices=list(q3.CLIENTS))
    ap.add_argument("--part", required=True, choices=["setup", "dev", "holdout", "local-dev", "local-holdout"])
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
    s = Session(a.client, a.part, outdir, cfg["tasks"], perms)
    t_start = time.time()
    s.log(action="session-start", client=a.client, part=a.part, minutes=a.minutes,
          version=q3.sh(q3.CLIENTS[a.client]["version"] + " 2>&1 | head -1").stdout.strip())
    cycles = s.run(a.minutes, cfg)
    served, changed = validity(q3.events())
    s.log(action="session-end", cycles=cycles, definitions_served=served, definition_changed=changed)
    (outdir / "session.json").write_text(json.dumps({"client": a.client, "part": a.part, "minutes": a.minutes, "t_start": t_start,
                                                     "t_end": time.time(), "cycles": cycles, "definitions_served": served,
                                                     "definition_changed": changed,
                                                     "valid": served in ([], ["A"]) and not changed}, indent=1))


if __name__ == "__main__":
    main()
