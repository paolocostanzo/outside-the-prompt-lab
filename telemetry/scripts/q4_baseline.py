#!/usr/bin/env python3
"""Host-side orchestration of the Q4 baseline (D13 points 1-3, D24 point 4): scripted normal use per terminal client.

Plan: one development session per client, in a random order fixed by --seed, then one holdout session per client in the same
order. plan.json is written before the first session and is what every later invocation executes; a restart with other
arguments or inputs (snapshot, seed, minutes, gap, clients, parts, inventory, candidates, harness commit) is refused.
A holdout session starts only when at least --gap-hours (default 6) have passed since the end of that client's VALID
development session; the runner waits otherwise. Every session starts from the clean snapshot and gets the same export as the
event runs (q4_events.py). A session counts only if its session.json says valid (definition A only, no change, the normal use
happened: baseline/tasks.json "workload_success"), its client logs were exported (collection check ok), and the outputs and the
lab server's log were copied; otherwise the attempt
is kept under <session>/attempts/<n>/ and the campaign stops, so that a person looks at it before more quota is spent.
The local-engine repetition (D13 point 1) is not implemented and is reported as not done.

  python3 q4_baseline.py --snapshot q3-base-20261015 --seed SEED --inventory INVENTORY.json --out OUT [--minutes 60] [--dry-run]
  python3 q4_baseline.py ... --parts setup --minutes 6      # exploratory set-up sessions (not part of the baseline)
"""
import argparse, importlib.util, io, json, random, sys, tarfile, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("q4_events", HERE / "q4_events.py")
ev = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ev)
PARTS = ("setup", "dev", "holdout")


def plan(seed, clients=ev.CLIENTS, parts=("dev", "holdout")):
    bad = [p for p in parts if p not in PARTS]
    if bad:
        raise SystemExit(f"unknown part(s) {bad}: only {PARTS} exist (the local-engine repetition is not implemented)")
    order = list(clients)
    random.Random(seed).shuffle(order)
    return [{"client": c, "part": p, "name": f"baseline__{c}__{p}"} for p in parts for c in order]


def session_command(s, minutes):
    return (f"python3 ~/lab/telemetry/scripts/baseline_session.py --client {s['client']} --part {s['part']} "
            f"--minutes {minutes} --out ~/q4-out")


def outputs_command():
    return "cd ~ && tar -czf - q4-out q3-server.log"  # required files only: tar fails if one is missing


def check_outputs(s, tgz_bytes):
    """(session.json or None, problems)."""
    try:
        tar = tarfile.open(fileobj=io.BytesIO(tgz_bytes), mode="r:gz")
        names = set(tar.getnames())
    except (tarfile.TarError, OSError, EOFError) as exc:
        return None, [f"outputs archive unreadable: {exc}"]
    base = f"q4-out/{s['name']}"
    problems = [f"{base}/{f} missing" for f in ("session.json", "timeline.jsonl") if f"{base}/{f}" not in names]
    if "q3-server.log" not in names:
        problems.append("q3-server.log missing")
    if problems:
        return None, problems
    try:
        sess = json.load(tar.extractfile(f"{base}/session.json"))
    except ValueError as exc:
        return None, [f"session.json unreadable: {exc}"]
    if sess.get("quota_exhausted"):
        problems.append(f"quota or rate limit reached: {sess.get('quota_message')!r} (stop: Paolo's rule)")
    if not sess.get("valid"):
        problems.append(f"session not valid: definitions {sess.get('definitions_served')}, changed {sess.get('definition_changed')}, "
                        f"workload {sess.get('workload')}")
    return sess, problems


def wait_for_gap(out, s, gap_hours, note, sleep=time.sleep):
    """Holdout sessions start at least gap_hours after the end of the same client's valid development session."""
    if s["part"] != "holdout":
        return 0
    f = out / f"baseline__{s['client']}__dev" / "run.json"
    if not f.exists():
        raise SystemExit(f"{s['name']}: no valid development session for {s['client']} yet")
    dev = json.loads(f.read_text())
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
    frozen = {"snapshot": a.snapshot, "seed": a.seed, "minutes": a.minutes, "gap_hours": a.gap_hours,
              "clients": a.clients.split(","), "parts": a.parts.split(","), "inventory_sha256": ev.sha_file(a.inventory),
              "candidates_sha256": ev.sha_file(ev.CANDIDATES), "harness": ev.harness_identity()}
    sessions = ev.load_or_create_plan(out, frozen, sessions)
    q3 = ev.load(ev.LAB / "tool-change/scripts/q3_host.py", "q3_host")
    cc = ev.load(HERE / "collection_check.py", "collection_check")
    inv = json.load(open(a.inventory))
    h = q3.Host(out)
    rn = ev.Runner(h, q3)
    for i, s in enumerate(sessions, 1):
        d = out / s["name"]
        if (d / "run.json").exists():
            continue
        waited = wait_for_gap(out, s, a.gap_hours, h.note)
        kept = ev.preserve_interrupted(d)
        if kept:
            h.note(event="interrupted-attempt-kept", session=s["name"], kept=str(kept))
        d.mkdir(exist_ok=True)
        ip, boot_s = ev.fresh_vm_checked(h, q3, a.snapshot, h.note)
        rc_push, hashes = rn.push(ip)
        (d / "harness-sha256.txt").write_text(hashes)
        ev.safe(h.ssh, ip, "rm -rf ~/q4-out && mkdir -p ~/q4-out")
        t0 = int(time.time())
        h.note(event="session-start", n=i, of=len(sessions), session=s["name"], ip=ip, boot_s=boot_s)
        res = ev.safe(h.ssh, ip, session_command(s, a.minutes), timeout=int(a.minutes * 60) + 900)
        t1 = int(time.time())
        (d / "session.stdout.txt").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
        stop = ev.safe(h.ssh, ip, ev.STOP_CLIENTS)
        if stop.returncode != 0:
            dest = ev.keep_attempt(d, "clients-not-stopped", {"stdout": stop.stdout[-2000:], "t0": t0, "t1": t1})
            h.note(event="abort-not-quiescent", session=s["name"], kept=str(dest), hint="a writer survived; VM left as it is")
            sys.exit(5)
        check = rn.client_logs(ip, d, s["client"], t0, t1, cc, inv, frozen["candidates_sha256"])
        rc_out, err_out = rn.ssh_bin(ip, outputs_command(), d / "vm-out.tgz")
        sess, problems = check_outputs(s, (d / "vm-out.tgz").read_bytes())
        if rc_out != 0:
            problems.insert(0, f"outputs copy exited {rc_out}: {err_out}")
        if res.returncode != 0:
            problems.insert(0, f"session exited {res.returncode}")
        if check["export"] != "ok":  # a development or holdout session without its logs is of no use (D24 point 4)
            problems.insert(0, f"client-log export failed: {check.get('reason', '').split(':')[0]}")
        problems += rn.telemetry(ip, d, t0 - 5)
        if problems:
            dest = ev.keep_attempt(d, "session-not-counted", {"problems": problems, "t0": t0, "t1": t1, "session": sess})
            h.note(event="abort-session", session=s["name"], problems=problems, kept=str(dest),
                   hint="VM left as it is; look at the attempt, fix the cause, then rerun the same command (the plan is kept)")
            sys.exit(5)
        (d / "run.json").write_text(json.dumps({**s, "t0": t0, "t1": t1, "waited_s": waited, "session_rc": res.returncode,
                                                "push_rc": rc_push, "export": check["export"], "export_reason": check.get("reason"),
                                                "client_logs": check.get("client_logs"), "workload": sess["workload"]}, indent=1))
        h.note(event="session-end", session=s["name"], seconds=t1 - t0, export=check["export"], workload_ok=sess["workload"]["ok"])
    h.note(event="baseline-done", sessions=len(sessions), local_engine_repetition="not implemented, not done")
    q3.run(q3.VIRSH + ["shutdown", q3.DOMAIN])


if __name__ == "__main__":
    main()
