#!/usr/bin/env python3
"""Runs INSIDE the VM next to a run or session (D25 point 5): reads the client's tmux pane every second, read-only, and records
every quota or rate-limit message it sees, with the screen, even if the client recovers and the message is gone by the next saved
capture. The historical Q3 and Q5 runners are left as they ran; this observer is the Q4 addition.

  python3 quota_watch.py --client codex --session q3run --out ~/q4-out/quota-watch.jsonl &

It writes a "started" record first, so that the host can tell a watcher that saw nothing from one that never ran.
"""
import argparse, importlib.util, json, subprocess, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("quota", HERE / "quota.py")
quota = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quota)


def screen(session):
    r = subprocess.run(["tmux", "capture-pane", "-p", "-J", "-t", session], capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def watch(client, session, out, interval=1.0, rounds=None, read=screen):
    out = Path(out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    with open(out, "a") as fh:
        fh.write(json.dumps({"ts": time.time(), "event": "started", "client": client, "session": session}) + "\n")
        fh.flush()
        last = None
        n = 0
        while rounds is None or n < rounds:
            n += 1
            s = read(session)
            msg = quota.find(client, s)
            if msg and s != last:
                fh.write(json.dumps({"ts": time.time(), "event": "quota", "message": msg, "screen": s}) + "\n")
                fh.flush()
                last = s
            time.sleep(interval)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--session", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    watch(a.client, a.session, a.out)


if __name__ == "__main__":
    main()
