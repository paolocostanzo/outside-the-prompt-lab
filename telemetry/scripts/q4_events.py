#!/usr/bin/env python3
"""Host-side orchestration of the Q4 event runs (D24 point 3), with the client-log export of D24 points 1-2.

Three event types on the six terminal clients, two runs per type and client (36 runs), in a random order fixed by --seed:
  q5-start      a server declared by the repository starts after the folder is trusted (trusting-a-repo, run_q5_matrix.py)
  q3-announced  an approved tool's definition changes and the server sends notifications/tools/list_changed (run_q3_cell.py)
  q3-silent     the same change without the notification
plan.json is written before the first run and is what every later invocation executes: a restart with a different seed,
snapshot, client list, inventory, candidates file or harness (git commit of the lab, clean tree) is refused.
For every run: restore the clean snapshot, start the VM, copy tool-change/, trusting-a-repo/ and telemetry/ in, run the cell,
stop every client (tmux), then BEFORE the next restore:
  - archive the client's default log locations (vm_logs.py collect, window = the run's start and end) and check the archive
    (collection_check.py); a failed client-log export is recorded and the run is excluded with its reason (D24 point 2);
  - copy the run's outputs and the ground-truth log (the lab server's log for Q3 events, the canary's log for Q5) and verify
    that they are present and readable. If they are not, the attempt is kept under <run>/attempts/<n>/, nothing is marked
    complete, and the campaign stops with the VM left as it is: without ground truth, "no event" cannot be told from a lost one.
Whether the event happened is decided later from the ground-truth logs only, never from the client's logs.

  python3 q4_events.py --snapshot q3-base-20261015 --seed SEED --inventory INVENTORY.json --candidates CANDIDATES.json --out OUT
  python3 q4_events.py ... --dry-run          # prints the plan and the commands, touches nothing
"""
import argparse, csv, datetime as dt, hashlib, importlib.util, io, json, random, shutil, subprocess, sys, tarfile, time
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
STOP_CLIENTS = "tmux kill-server 2>/dev/null; pkill -f q3-server.mjs; pkill -f marker-server.mjs; sleep 3; true"


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


def ground_truth_command(run):
    """Required files only, so that tar fails if one is missing (no --ignore-failed-read)."""
    gt = "canary-start.log" if run["event"] == "q5-start" else "q3-server.log"
    return f"cd ~ && tar -czf - q4-out {gt}"


def validate_ground_truth(run, tgz_bytes):
    """Problems with the copied outputs and ground truth of one run (empty list = usable). Does not decide the event."""
    try:
        tar = tarfile.open(fileobj=io.BytesIO(tgz_bytes), mode="r:gz")
        names = set(tar.getnames())
    except (tarfile.TarError, OSError, EOFError) as exc:
        return [f"outputs archive unreadable: {exc}"]
    problems = []
    if run["event"] == "q5-start":
        if "canary-start.log" not in names:
            problems.append("canary-start.log missing")
        mats = [n for n in names if n.startswith("q4-out/") and n.endswith("/matrix.csv")]
        if len(mats) != 1:
            problems.append(f"expected one matrix.csv, found {len(mats)}")
        else:
            rows = list(csv.DictReader(io.TextIOWrapper(tar.extractfile(mats[0]), encoding="utf-8")))
            if [(r["client"], r["cell"]) for r in rows] != [(run["client"], Q5_CELL[run["client"]])]:
                problems.append(f"matrix.csv does not hold exactly this cell: {[(r['client'], r['cell']) for r in rows]}")
    else:
        cell = f"q4-out/{run['client']}__{Q3_SIGNAL[run['event']]}__description__r{run['rep']}/row.json"
        if cell not in names:
            problems.append(f"{cell} missing")
        else:
            try:
                json.load(tar.extractfile(cell))
            except ValueError as exc:
                problems.append(f"row.json unreadable: {exc}")
        if "q3-server.log" not in names:
            problems.append("q3-server.log missing")
        else:
            lines = tar.extractfile("q3-server.log").read().decode("utf-8", "replace").splitlines()
            if not lines:
                problems.append("q3-server.log empty")
            elif not any('"definition-changed"' in l for l in lines):
                problems.append("q3-server.log has no definition-changed record: the change itself is not documented")
    return problems


def sha_file(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def harness_identity():
    """The lab's git commit and the tree of every folder pushed into the VM; refuses a dirty tree."""
    dirty = subprocess.run(["git", "-C", str(LAB), "status", "--porcelain", "--", *FOLDERS], capture_output=True, text=True).stdout
    if dirty.strip():
        raise SystemExit("the harness folders have uncommitted changes: commit them first, the plan records the commit\n" + dirty)
    head = subprocess.run(["git", "-C", str(LAB), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    trees = {f: subprocess.run(["git", "-C", str(LAB), "rev-parse", f"HEAD:{f}"], capture_output=True, text=True,
                               check=True).stdout.strip() for f in FOLDERS}
    return {"commit": head, "trees": trees}


def load_or_create_plan(out, frozen, runs):
    """frozen: the identity of this campaign (arguments and input hashes). Returns the runs to execute."""
    pf = out / "plan.json"
    if pf.exists():
        old = json.loads(pf.read_text())
        diff = {k: (old.get("frozen", {}).get(k), v) for k, v in frozen.items() if old.get("frozen", {}).get(k) != v}
        if diff:
            raise SystemExit(f"plan.json was made with other inputs; refusing to continue: {json.dumps(diff)[:800]}")
        return old["runs"]
    pf.write_text(json.dumps({"created": now(), "frozen": frozen, "runs": runs}, indent=2))
    return runs


def keep_attempt(d, status, extra):
    """Move whatever a failed attempt left into d/attempts/<n>/ with a status file; the run stays not complete."""
    att = d / "attempts"
    att.mkdir(exist_ok=True)
    n = len([p for p in att.iterdir() if p.is_dir()]) + 1
    dest = att / str(n)
    dest.mkdir()
    for p in list(d.iterdir()):
        if p.name != "attempts":
            shutil.move(str(p), str(dest / p.name))
    (dest / "attempt.json").write_text(json.dumps({"status": status, "at": now(), **extra}, indent=1))
    return dest


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

    def client_logs(self, ip, d, client, t0, t1, cc, inv, cand_sha):
        rc, err = self.ssh_bin(ip, collect_command(t0, t1), d / "client-logs.tgz")
        check = cc.check(str(d / "client-logs.tgz"), client, t0, t1, inv, cand_sha)
        check["collect_rc"], check["collect_stderr"] = rc, err
        if rc != 0 and check["export"] == "ok":
            check["export"], check["reason"] = "failed", f"collect exited {rc}"
        (d / "collection.json").write_text(json.dumps(check, indent=1))
        return check


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--inventory", required=True, help="inventory.json taken on the clean snapshot (D24 point 1)")
    ap.add_argument("--candidates", default=str(LAB / "telemetry/inventory/candidates.json"))
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
    frozen = {"snapshot": a.snapshot, "seed": a.seed, "clients": a.clients.split(","), "q5_cell": Q5_CELL,
              "inventory_sha256": sha_file(a.inventory), "candidates_sha256": sha_file(a.candidates), "harness": harness_identity()}
    runs = load_or_create_plan(out, frozen, runs)
    q3 = load(LAB / "tool-change/scripts/q3_host.py", "q3_host")
    cc = load(HERE / "collection_check.py", "collection_check")
    inv = json.load(open(a.inventory))
    h = q3.Host(out)
    rn = Runner(h, q3)
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
        h.ssh(ip, STOP_CLIENTS)  # databases and logs are closed before they are copied
        check = rn.client_logs(ip, d, r["client"], t0, t1, cc, inv, frozen["candidates_sha256"])
        rc_gt, err_gt = rn.ssh_bin(ip, ground_truth_command(r), d / "vm-out.tgz")
        problems = ([f"ground-truth copy exited {rc_gt}: {err_gt}"] if rc_gt != 0 else []) + \
            validate_ground_truth(r, (d / "vm-out.tgz").read_bytes())
        rn.telemetry(ip, d, t0 - 5)
        if problems:
            dest = keep_attempt(d, "ground-truth-unavailable", {"problems": problems, "t0": t0, "t1": t1, "cell_rc": res.returncode})
            h.note(event="abort-ground-truth", run=r["name"], problems=problems, kept=str(dest),
                   hint="VM left as it is for inspection; fix the cause, then rerun the same command (the plan is kept)")
            sys.exit(5)
        (d / "run.json").write_text(json.dumps({**r, "t0": t0, "t1": t1, "cell_rc": res.returncode, "push_rc": rc_push,
                                                "export": check["export"], "export_reason": check.get("reason"),
                                                "client_logs": check.get("client_logs"), "ground_truth": "copied and checked"},
                                               indent=1))
        h.note(event="run-end", run=r["name"], rc=res.returncode, seconds=t1 - t0, export=check["export"],
               client_logs=check.get("client_logs"))
    h.note(event="events-done", runs=len(runs))
    q3.run(q3.VIRSH + ["shutdown", q3.DOMAIN])


if __name__ == "__main__":
    main()
