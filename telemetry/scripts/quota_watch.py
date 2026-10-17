#!/usr/bin/env python3
"""Runs INSIDE the VM next to a run or session (D25 point 5): reads the client's tmux pane every second, read-only, and records
every quota or rate-limit message it sees, with the screen, even if the client recovers and the message is gone by the next saved
capture. The historical Q3 and Q5 runners are left as they ran; this observer is the Q4 addition.

  python3 quota_watch.py --client codex --session q3run --out ~/q4-out/quota-watch.jsonl &

Records (JSON Lines): "started"; "heartbeat" every HEARTBEAT_S seconds with the number of captures, whether the client's tmux
session existed (between a client's restarts it does not: an expected gap, not an error) and capture failures; "capture-error"
when the session existed but could not be read; "quota" with the screen; "stopped" on SIGTERM (the orderly end). The host
(observer_problems() in q4_events.py) rejects a run without "stopped", with a gap between records longer than MAX_GAP_S, or with
capture errors: an observer that died part-way must not look like an observer that saw nothing.
"""
import argparse, importlib.util, json, signal, subprocess, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("quota", HERE / "quota.py")
quota = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(quota)


HEARTBEAT_S = 10


def screen(session):
    """(present, text, error): present is False when the session does not exist (between client restarts)."""
    if subprocess.run(["tmux", "has-session", "-t", session], capture_output=True).returncode != 0:
        return False, "", None
    r = subprocess.run(["tmux", "capture-pane", "-p", "-J", "-t", session], capture_output=True, text=True)
    return True, r.stdout, (None if r.returncode == 0 else (r.stderr.strip() or f"exit {r.returncode}"))


class Stop(Exception):
    pass


def watch(client, session, out, interval=1.0, rounds=None, read=screen, clock=time.time, sleep=time.sleep):
    out = Path(out).expanduser()
    out.parent.mkdir(parents=True, exist_ok=True)
    stats = {"captures": 0, "absent": 0, "capture_errors": 0}

    def write(fh, **rec):
        fh.write(json.dumps({"ts": clock(), **rec}) + "\n")
        fh.flush()

    def on_term(signum, frame):
        raise Stop()

    with open(out, "a") as fh:
        write(fh, event="started", client=client, session=session)
        old = signal.signal(signal.SIGTERM, on_term) if rounds is None else None
        last, last_beat, n = None, clock(), 0
        try:
            while rounds is None or n < rounds:
                n += 1
                present, s, err = read(session)
                if not present:
                    stats["absent"] += 1
                elif err:
                    stats["capture_errors"] += 1
                    write(fh, event="capture-error", error=err)
                else:
                    stats["captures"] += 1
                    msg = quota.find(client, s)
                    if msg and s != last:
                        write(fh, event="quota", message=msg, screen=s)
                        last = s
                if clock() - last_beat >= HEARTBEAT_S:
                    write(fh, event="heartbeat", **stats)
                    last_beat = clock()
                sleep(interval)
        except Stop:
            pass
        finally:
            if old is not None:
                signal.signal(signal.SIGTERM, old)
            write(fh, event="stopped", **stats)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--client", required=True)
    ap.add_argument("--session", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    watch(a.client, a.session, a.out)


if __name__ == "__main__":
    main()
