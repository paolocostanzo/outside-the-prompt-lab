#!/usr/bin/env python3
"""Host-side orchestration of the Q4 event runs (D24 point 3), with the client-log export of D24 points 1-2.

Three event types on the six terminal clients, two runs per type and client (36 runs), in a random order fixed by --seed and
written to plan.json before the first run:
  q5-start      a server declared by the repository starts after the folder is trusted (trusting-a-repo, run_q5_matrix.py)
  q3-announced  an approved tool's definition changes and the server sends notifications/tools/list_changed (run_q3_cell.py)
  q3-silent     the same change without the notification
For every run: restore the clean snapshot, start the VM, copy tool-change/, trusting-a-repo/ and telemetry/ in, run the cell,
then BEFORE the VM is stopped: archive the client's default log locations (vm_logs.py collect, window = the run's start and end),
copy the run's outputs and the ground-truth logs (canary and lab server), copy the host telemetry, and write the collection
check (collection_check.py). Whether the event happened is decided later from the ground-truth logs only, never from the
client's logs. A run is resumed if its run.json is missing; --dry-run prints the plan and the commands and touches nothing.

  python3 q4_events.py --snapshot q3-base-20261015 --seed SEED --inventory INVENTORY.json --out OUT [--dry-run]
"""
import argparse, datetime as dt, importlib.util, json, random, subprocess, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
LAB = HERE.parent.parent  # repository root: tool-change/, trusting-a-repo/, telemetry/
FOLDERS = ["tool-change", "trusting-a-repo", "telemetry"]
CLIENTS = ["claude-code", "codex", "gemini", "qwen", "cursor-agent", "goose"]
EVENTS = ["q5-start", "q3-announced", "q3-silent"]
# Q5 cell in which the client trusts the folder (and approves the server where it asks); Goose has no trust step and never
# starts a repository-declared server (part 2: 0/2), so its runs are expected to be "no event" (D24 point 2).
Q5_CELL = {"claude-code": "after-decision", "codex": "after-decision", "gemini": "after-decision", "qwen": "after-decision",
           "cursor-agent": "after-decision", "goose": "open-in-repo"}
Q3_SIGNAL = {"q3-announced": "list_changed", "q3-silent": "none"}


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plan(seed, clients=CLIENTS, events=EVENTS, reps=2):
    """Random order within each repetition block, as in the Q3 matrix: every (client, event) once per block."""
    rng = random.Random(seed)
    runs = []
    for rep in range(1, reps + 1):
        block = [(c, e) for c in clients for e in events]
        rng.shuffle(block)
        runs += [{"rep": rep, "client": c, "event": e, "name": f"{c}__{e}__r{rep}"} for c, e in block]
    return runs


def cell_command(run):
    """The command run inside the VM for one run (outputs under ~/q4-out)."""
    c, e, rep = run["client"], run["event"], run["rep"]
    if e == "q5-start":
        return (f"python3 ~/lab/trusting-a-repo/scripts/run_q5_matrix.py --lab ~/lab/trusting-a-repo --out ~/q4-out "
                f"--reps 1 --clients {c} --only {c}:{Q5_CELL[c]}")
    return (f"python3 ~/lab/tool-change/scripts/run_q3_cell.py --client {c} --signal {Q3_SIGNAL[e]} --change description "
            f"--rep {rep} --out ~/q4-out")


def collect_command(t0, t1):
    return f"python3 -I ~/lab/telemetry/scripts/vm_logs.py collect ~/lab/telemetry/inventory/candidates.json {t0} {t1}"


def now():
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")


class Runner:
    def __init__(self, host, q3):
        self.h, self.q3 = host, q3  # q3_host.Host instance and the q3_host module (VM constants, ssh key)

    def ssh_bin(self, ip, command, dest, timeout=300):
        """Run a command in the VM and write its stdout, as bytes, to dest."""
        q3 = self.q3
        with open(dest, "wb") as f:
            r = subprocess.run(["ssh", "-i", str(q3.KEY), "-o", f"UserKnownHostsFile={q3.KNOWN}", "-o", "BatchMode=yes",
                                f"lab@{ip}", command], stdout=f, stderr=subprocess.PIPE, timeout=timeout)
        return r.returncode, r.stderr.decode(errors="replace")[-500:]

    def push(self, ip):
        q3 = self.q3
        p1 = subprocess.Popen(["tar", "-C", str(LAB), "-czf", "-", "--exclude=node_modules", "--exclude=__pycache__", *FOLDERS],
                              stdout=subprocess.PIPE)
        p2 = subprocess.run(["ssh", "-i", str(q3.KEY), "-o", f"UserKnownHostsFile={q3.KNOWN}", "-o", "BatchMode=yes", f"lab@{ip}",
                             "mkdir -p ~/lab && cd ~/lab && rm -rf " + " ".join(FOLDERS) + " && tar -xzf -"],
                            stdin=p1.stdout, capture_output=True, timeout=180)
        p1.wait()
        h = self.h.ssh(ip, "cd ~/lab && find " + " ".join(FOLDERS) + " -type f -not -path '*/test/*' | sort | xargs sha256sum",
                       timeout=120)
        return p2.returncode, h.stdout

    def telemetry(self, ip, d, since):
        tel = d / "telemetry"
        tel.mkdir(exist_ok=True)
        for name, rcmd in [("audit.log", "sync; sleep 1; sudo cat /var/log/audit/audit.log"),
                           ("journal.txt", f"sudo journalctl -o short-iso-precise --since @{since} --no-pager"),
                           ("nft-ruleset.txt", "sudo nft list ruleset"),
                           ("auditctl-rules.txt", "sudo auditctl -l")]:
            (tel / name).write_text(self.h.ssh(ip, rcmd, timeout=120).stdout)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--inventory", required=True, help="inventory.json taken on the clean snapshot (D24 point 1)")
    ap.add_argument("--out", required=True)
    ap.add_argument("--clients", default=",".join(CLIENTS))
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    runs = plan(a.seed, a.clients.split(","))
    if a.dry_run:
        for i, r in enumerate(runs, 1):
            print(f"{i:2} {r['name']:32} {cell_command(r)}")
        print("then:", collect_command("<t0>", "<t1>"))
        return
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    q3 = load(LAB / "tool-change/scripts/q3_host.py", "q3_host")
    cc = load(HERE / "collection_check.py", "collection_check")
    inv = json.load(open(a.inventory))
    h = q3.Host(out)
    rn = Runner(h, q3)
    pf = out / "plan.json"
    if not pf.exists():
        pf.write_text(json.dumps({"created": now(), "snapshot": a.snapshot, "seed": a.seed, "q5_cell": Q5_CELL,
                                  "inventory": str(Path(a.inventory).resolve()), "runs": runs}, indent=2))
    for i, r in enumerate(runs, 1):
        d = out / r["name"]
        if (d / "run.json").exists():
            continue
        d.mkdir(exist_ok=True)
        avail = h.mem_ok()
        h.note(event="pre-revert", run=r["name"], order6plus=h.order6_blocks())
        ip, boot_s = h.fresh_vm(a.snapshot)
        rc_push, hashes = rn.push(ip)
        (d / "harness-sha256.txt").write_text(hashes)
        h.ssh(ip, "rm -rf ~/q4-out && mkdir -p ~/q4-out")
        t0 = int(time.time())
        h.note(event="run-start", n=i, of=len(runs), run=r["name"], ip=ip, boot_s=boot_s, host_avail_mb=avail, push_rc=rc_push)
        res = h.ssh(ip, cell_command(r), timeout=1500)
        t1 = int(time.time())
        (d / "cell.stdout.txt").write_text(res.stdout + "\n--- stderr ---\n" + res.stderr)
        rc_logs, err_logs = rn.ssh_bin(ip, collect_command(t0, t1), d / "client-logs.tgz")
        rc_out, err_out = rn.ssh_bin(ip, "cd ~ && tar -czf - --ignore-failed-read q4-out canary-start.log q3-server.log",
                                     d / "vm-out.tgz")
        rn.telemetry(ip, d, t0 - 5)
        check = cc.check(str(d / "client-logs.tgz"), r["client"], t0, t1, inventory=inv)
        check["collect_rc"], check["collect_stderr"] = rc_logs, err_logs
        if rc_logs != 0:
            check["export"], check["reason"] = "failed", f"collect exited {rc_logs}"
        (d / "collection.json").write_text(json.dumps(check, indent=1))
        (d / "run.json").write_text(json.dumps({**r, "t0": t0, "t1": t1, "cell_rc": res.returncode, "push_rc": rc_push,
                                                "vm_out_rc": rc_out, "vm_out_stderr": err_out, "export": check["export"],
                                                "client_logs": check.get("client_logs")}, indent=1))
        h.note(event="run-end", run=r["name"], rc=res.returncode, seconds=t1 - t0, export=check["export"],
               client_logs=check.get("client_logs"))
    h.note(event="events-done", runs=len(runs))
    q3.run(q3.VIRSH + ["shutdown", q3.DOMAIN])


if __name__ == "__main__":
    main()
