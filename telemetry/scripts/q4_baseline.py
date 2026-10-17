#!/usr/bin/env python3
"""Host-side orchestration of the Q4 baseline (D13 points 1-3, D24 point 4): scripted normal use per terminal client.

Plan (written to plan.json before the first session): one development session per client, in a random order fixed by --seed,
then one holdout session per client in the same order. A holdout session starts only when at least --gap-hours (default 6) have
passed since the end of that client's development session; the runner waits otherwise. Every session starts from the clean
snapshot and gets the same export as the event runs (q4_events.py): client-log archive for the session window, outputs and the
lab server's log, host telemetry, collection check. Sessions with a run.json are skipped when the runner is restarted.

  python3 q4_baseline.py --snapshot q3-base-20261015 --seed SEED --inventory INVENTORY.json --out OUT [--minutes 60] [--dry-run]
  python3 q4_baseline.py ... --parts setup --minutes 6      # exploratory set-up sessions (not part of the baseline)
"""
import argparse, importlib.util, json, random, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("q4_events", HERE / "q4_events.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)


def plan(seed, clients=ev.CLIENTS, parts=("dev", "holdout")):
    order = list(clients)
    random.Random(seed).shuffle(order)
    return [{"client": c, "part": p, "name": f"baseline__{c}__{p}"} for p in parts for c in order]


def session_command(s, minutes):
    return (f"python3 ~/lab/telemetry/scripts/baseline_session.py --client {s['client']} --part {s['part']} "
            f"--minutes {minutes} --out ~/q4-out")


def wait_for_gap(out, s, gap_hours, note, sleep=time.sleep):
    """Holdout sessions start at least gap_hours after the end of the same client's development session."""
    if s["part"] != "holdout":
        return 0
    dev = json.loads((out / f"baseline__{s['client']}__dev" / "run.json").read_text())
    wait = dev["t1"] + gap_hours * 3600 - time.time()
    if wait > 0:
        note(event="holdout-wait", session=s["name"], wait_s=round(wait))
        sleep(wait)
    return max(0, round(wait))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--inventory", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--minutes", type=float, default=60)
    ap.add_argument("--gap-hours", type=float, default=6)
    ap.add_argument("--clients", default=",".join(ev.CLIENTS))
    ap.add_argument("--parts", default="dev,holdout")
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    sessions = plan(a.seed, a.clients.split(","), a.parts.split(","))
    if a.dry_run:
        for i, s in enumerate(sessions, 1):
            print(f"{i:2} {s['name']:34} {session_command(s, a.minutes)}")
        return
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    q3 = ev.load(ev.LAB / "tool-change/scripts/q3_host.py", "q3_host")
    cc = ev.load(HERE / "collection_check.py", "collection_check")
    inv = json.load(open(a.inventory))
    h = q3.Host(out)
    rn = ev.Runner(h, q3)
    pf = out / "plan.json"
    if not pf.exists():
        pf.write_text(json.dumps({"created": ev.now(), "snapshot": a.snapshot, "seed": a.seed, "minutes": a.minutes,
                                  "gap_hours": a.gap_hours, "sessions": sessions}, indent=2))
    for i, s in enumerate(sessions, 1):
        d = out / s["name"]
        if (d / "run.json").exists():
            continue
        waited = wait_for_gap(out, s, a.gap_hours, h.note)
        d.mkdir(exist_ok=True)
        avail = h.mem_ok()
        ip, boot_s = h.fresh_vm(a.snapshot)
        rc_push, hashes = rn.push(ip)
        (d / "harness-sha256.txt").write_text(hashes)
        h.ssh(ip, "rm -rf ~/q4-out && mkdir -p ~/q4-out")
        t0 = int(time.time())
        h.note(event="session-start", n=i, of=len(sessions), session=s["name"], ip=ip, boot_s=boot_s, host_avail_mb=avail)
        res = h.ssh(ip, session_command(s, a.minutes), timeout=int(a.minutes * 60) + 900)
        t1 = int(time.time())
        (d / "session.stdout.txt").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
        rc_logs, err_logs = rn.ssh_bin(ip, ev.collect_command(t0, t1), d / "client-logs.tgz")
        rc_out, err_out = rn.ssh_bin(ip, "cd ~ && tar -czf - --ignore-failed-read q4-out q3-server.log", d / "vm-out.tgz")
        rn.telemetry(ip, d, t0 - 5)
        check = cc.check(str(d / "client-logs.tgz"), s["client"], t0, t1, inventory=inv)
        check["collect_rc"], check["collect_stderr"] = rc_logs, err_logs
        if rc_logs != 0:
            check["export"], check["reason"] = "failed", f"collect exited {rc_logs}"
        (d / "collection.json").write_text(json.dumps(check, indent=1))
        (d / "run.json").write_text(json.dumps({**s, "t0": t0, "t1": t1, "waited_s": waited, "session_rc": res.returncode,
                                                "push_rc": rc_push, "vm_out_rc": rc_out, "vm_out_stderr": err_out,
                                                "export": check["export"], "client_logs": check.get("client_logs")}, indent=1))
        h.note(event="session-end", session=s["name"], rc=res.returncode, seconds=t1 - t0, export=check["export"])
    h.note(event="baseline-done", sessions=len(sessions))
    q3.run(q3.VIRSH + ["shutdown", q3.DOMAIN])


if __name__ == "__main__":
    main()
