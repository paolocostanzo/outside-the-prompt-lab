#!/usr/bin/env python3
"""Host-side orchestration of the RQ3 positive control (D52, exploratory; D12 point 5 run after the fact), on top of q3_host.py.

One cell per client: the tool is renamed (change "name": q3_noop -> q3_noop_renamed, a tool the user never approved) with the
list_changed signal, phases 1-3 as in the primary matrix (phase 3 reopens the client, the path by which a client that keeps its
catalog until reconnection sees the new name). The clients file is q3-clients-positive.json (the frozen q3-clients.json with
Gemini's approval pattern widened to the renamed tool). Gemini CLI runs first, alone, as the cost pilot; the other clients follow
in an order drawn from the seed. All of this is frozen in plan.json before the first cell, and a resume must match it.

Guards, as in q3_open_weight_host.py and the Q4 orchestrators: the shared VM lock and no Q4 evidence pending, checked before the
VM is touched; the VM is shut down and its state checked whatever happens; a cell whose phase 1 did not produce a valid call
with definition A (login, quota or set-up failure) stops the campaign before the next cell. --only CLIENT runs just that cell
(the cost pilot), then stops. After each cell, while the VM still holds that cell's secret stores, the secret gate
(open_weight_gate.py, D26) fingerprints them and scans the whole folder; a result that is not clean stops the campaign.

  python3 q3_positive_host.py --snapshot q4-base-20261023b --seed 20261028 --out ../../../lab/results/q3/positive-control-20261028 \
      [--only gemini]
"""
import argparse
import fcntl
import hashlib
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

import q3_host as qh
import code_q3

STATE = Path.home() / ".agentlab-q4"  # shared with the Q4 orchestrators: one campaign at a time drives the VM
CLIENTS = ["claude-code", "codex", "gemini", "qwen", "goose"]  # Cursor CLI excluded (no plan, D52)
PILOT = "gemini"
CLIENTS_JSON = "q3-clients-positive.json"


def campaign(seed, snapshot):
    rest = [c for c in CLIENTS if c != PILOT]
    random.Random(seed).shuffle(rest)
    here = Path(__file__).resolve().parent
    return {"seed": seed, "snapshot": snapshot, "change": "name", "signal": "list_changed", "rep": 1, "reopen": True,
            "order": [PILOT] + rest, "pilot": PILOT, "clients_json": CLIENTS_JSON,
            "inputs_sha256": {f: hashlib.sha256((here / f).read_bytes()).hexdigest()
                              for f in (CLIENTS_JSON, "run_q3_cell.py", "flip.mjs", "q3_host.py", "q3_positive_host.py",
                                        "code_q3.py", "open_weight_gate.py", "../server/q3-server.mjs")}}


def phase1_valid(cell_dir):
    """True if phase 1 produced a successful call with definition A (else: login, quota or set-up failure)."""
    try:
        coded = code_q3.code(cell_dir)
    except Exception:  # noqa: BLE001 (missing or unreadable files are a failed set-up too)
        return False
    return bool(coded.get("p1_ok"))


PENDING = STATE / "pending.json"  # the Q4 orchestrators' VM-wide marker: while it exists, no campaign restores the VM


def write_json_atomic(path, obj):
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(obj, indent=1))
    os.replace(tmp, path)


def mark_pending(out, cell, ip):
    """The Q4 protocol (q4_events.mark_pending): the same record in the campaign folder and VM-wide, so that Q4's guard_vm sees
    a live attempt of another folder and stops instead of restoring."""
    rec = {"at": qh.now(), "folder": str(out.resolve()), "campaign": "q3-positive-control", "cell": cell, "ip": ip,
           "why": "evidence or secret stores of this cell are still only in the VM"}
    write_json_atomic(out / "pending.json", rec)
    write_json_atomic(PENDING, rec)


def clear_pending(out):
    """As q4_events.clear_pending: the folder's record, and the VM-wide one only if it is this folder's."""
    (out / "pending.json").unlink(missing_ok=True)
    if PENDING.exists() and json.loads(PENDING.read_text()).get("folder") == str(out.resolve()):
        PENDING.unlink()


def gated(out, cell):
    """True if the host log records a clean secret gate for this cell after its export (the only state that lets a cell be
    read, skipped on resume or followed by a restore)."""
    log = out / "host-log.jsonl"
    if not log.exists():
        return False
    for line in log.read_text().splitlines():
        e = json.loads(line)
        if e.get("event") == "secret-gate" and e.get("cell") == cell and e.get("rc") == 0:
            return True
    return False


def fetch_checked(h, ip, name, local, since):
    """q3_host's export with every exit status checked: the archive is copied (ssh rc), tested (gzip -t) and extracted (tar rc),
    each telemetry command must succeed, and the files must be there (row, server log, control, every capture listed, non-empty
    audit log and journal). Returns what failed or is missing (empty: complete)."""
    local.mkdir(parents=True, exist_ok=True)
    problems = []
    tgz = local.parent / f"{name}.tgz"
    ssh = ["ssh", "-i", str(qh.KEY), "-o", f"UserKnownHostsFile={qh.KNOWN}", "-o", "BatchMode=yes", f"lab@{ip}"]
    with open(tgz, "wb") as f:
        r = subprocess.run(ssh + [f"tar -C ~/q3-out -czf - {name}"], stdout=f, stderr=subprocess.PIPE, timeout=120)
    if r.returncode != 0:
        problems.append(f"archive copy rc {r.returncode}")
    if qh.run(["gzip", "-t", str(tgz)]).returncode != 0:
        problems.append("archive integrity")
    elif qh.run(["tar", "-C", str(local.parent), "-xzf", str(tgz)]).returncode != 0:
        problems.append("archive extraction")
    tel = local / "telemetry"
    tel.mkdir(exist_ok=True)
    for fname, rcmd in [("audit.log", "sync; sleep 1; sudo cat /var/log/audit/audit.log"),
                        ("journal.txt", f"sudo journalctl -o short-iso-precise --since @{since} --no-pager"),
                        ("nft-ruleset.txt", "sudo nft list ruleset"),
                        ("auditctl-rules.txt", "sudo auditctl -l")]:
        r = h.ssh(ip, rcmd, timeout=120)
        (tel / fname).write_text(r.stdout)
        if r.returncode != 0:
            problems.append(f"telemetry {fname} rc {r.returncode}")
    for f in ("row.json", "q3-server.log", "q3-control.json"):
        if not (local / f).exists():
            problems.append(f)
    if (local / "row.json").exists():
        for c in json.loads((local / "row.json").read_text()).get("captures", []):
            if not (local / c).exists():
                problems.append(c)
    for f in ("audit.log", "journal.txt"):
        if (tel / f).stat().st_size == 0:
            problems.append("telemetry/" + f + " empty")
    return problems


def vm_off():
    st = qh.run(qh.VIRSH + ["domstate", qh.DOMAIN]).stdout.strip()
    return st in ("shut off", "spento", "terminato")


def shutdown_verified(h):
    qh.run(qh.VIRSH + ["shutdown", qh.DOMAIN])
    for _ in range(40):
        if vm_off():
            h.note(event="vm-off")
            return True
        time.sleep(3)
    qh.run(qh.VIRSH + ["destroy", qh.DOMAIN])  # power off: the snapshot is the clean state, nothing in the VM is kept
    ok = vm_off()
    h.note(event="vm-destroyed", off=ok)
    return ok


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--only", choices=CLIENTS)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    STATE.mkdir(exist_ok=True)
    lock = open(STATE / "vm.lock", "w")
    try:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        sys.exit("another campaign is driving the VM (vm.lock): not starting")
    if PENDING.exists() or (out / "pending.json").exists():
        sys.exit("a campaign has evidence pending in the VM (pending.json): recover it first; nothing restored")
    plan = campaign(a.seed, a.snapshot)
    pf = out / "plan.json"
    if pf.exists():
        old = json.loads(pf.read_text())
        if {k: old.get(k) for k in plan} != plan:
            sys.exit(f"{pf} was made with other arguments or inputs; refusing to resume into this folder")
    else:
        out.mkdir(parents=True, exist_ok=True)
        pf.write_text(json.dumps({"made": qh.now(), **plan}, indent=2))
    h = qh.Host(out)
    try:
        run_cells(a, h, out, plan)
    finally:
        if not shutdown_verified(h):
            print("WARNING: the VM did not reach the shut-off state", file=sys.stderr)


def run_cells(a, h, out, plan):
    for i, client in enumerate(plan["order"], 1):
        if a.only and client != a.only:
            continue
        name = f"{client}__list_changed__name__r1"
        if (out / name / "row.json").exists():
            if not gated(out, name):  # exported but never cleared by the gate: recover by hand, nothing is read
                h.note(event="stop", reason="cell exported without a clean secret gate: recover it before anything else", cell=name)
                return
            if not phase1_valid(out / name):
                h.note(event="stop", reason="an earlier cell has an invalid phase 1", cell=name)
                return
            continue
        h.mem_ok()
        t0 = time.time()
        h.note(event="pre-revert", cell=name, order6plus=h.order6_blocks())
        ip, boot_s = h.fresh_vm(a.snapshot)
        rc, hashes = h.push_harness(ip)
        h.note(event="cell-start", n=i, of=len(plan["order"]), cell=name, ip=ip, boot_s=boot_s, push_rc=rc)
        mark_pending(out, name, ip)
        result = None
        try:
            result = h.ssh(ip, f"python3 ~/lab/tool-change/scripts/run_q3_cell.py --client {client} --signal list_changed "
                               f"--change name --rep 1 --out ~/q3-out --clients-json "
                               f"/home/lab/lab/tool-change/scripts/{CLIENTS_JSON}", timeout=1500)
            (out / f"{name}.stdout.txt").write_text(result.stdout + "\n--- stderr ---\n" + result.stderr)
        except Exception as e:  # noqa: BLE001
            h.note(event="cell-failed", cell=name, error=type(e).__name__ + ": " + str(e)[:300])
        finally:
            try:
                missing = fetch_checked(h, ip, name, out / name, int(t0) - 5)
            except Exception as e:  # noqa: BLE001
                missing = ["export failed: " + type(e).__name__]
            (out / name).mkdir(parents=True, exist_ok=True)
            (out / name / "harness-sha256.txt").write_text(hashes)
        if missing:  # pending.json stays: the VM is shut down, not restored, so the cell's files survive for recovery
            h.note(event="stop", reason="export incomplete; VM kept (pending.json) for recovery", cell=name, missing=missing[:20])
            return
        # secret gate (D26) while the VM still holds this cell's stores (a renewed token exists only here): fingerprints are
        # merged into the host's private state and the whole folder is scanned; anything but a clean result stops the campaign
        g = qh.run([sys.executable, "-B", str(Path(__file__).resolve().parent / "open_weight_gate.py"), "--out", str(out),
                    "--vm-ip", ip], timeout=600)  # not -I: the gate imports q3_host from its own directory
        h.note(event="secret-gate", cell=name, rc=g.returncode)
        if g.returncode != 0:  # pending.json stays: the cell's stores are not fingerprinted, the VM must not be restored
            h.note(event="stop", reason="secret gate not clean: nothing is read or published; VM kept (pending.json)", cell=name)
            return
        clear_pending(out)  # exported, checked and gated: the VM may be restored again
        valid = (out / name / "row.json").exists() and phase1_valid(out / name)
        h.note(event="cell-end", cell=name, rc=None if result is None else result.returncode,
               seconds=round(time.time() - t0), phase1_valid=valid)
        if not valid:
            h.note(event="stop", reason="phase 1 invalid (login, quota or set-up): fix and resume", cell=name)
            return
        if a.only:
            h.note(event="only-done", cell=name)
            return
    h.note(event="campaign-done", cells=len(plan["order"]))


if __name__ == "__main__":
    main()
