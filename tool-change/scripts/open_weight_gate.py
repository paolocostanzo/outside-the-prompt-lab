#!/usr/bin/env python3
"""Secret gate for the open-weight cells (D39), the same gate as q4_events.py (D26): take fresh fingerprints of the VM's secrets
(never their values) into the host's fingerprint state, then scan every file copied out for the campaign, archives included, by
exact value and by format. Fails closed: a finding, a file that cannot be scanned or fingerprints that cannot be trusted make the
campaign not publishable. Writes secret-gate.json (files and kinds only, never values) in the campaign folder.

    python3 open_weight_gate.py --out ../../results/q3/open-weight-20261024 --vm-ip 192.168.122.70
The VM must be running (any restore of the campaign's snapshot: its secret stores are the ones the cells used).
"""
import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "telemetry" / "scripts"))
import secret_gate as sg  # noqa: E402
import q3_host as qh  # noqa: E402

STATE = Path.home() / ".agentlab-q4"  # shared with q4_events.py, outside every results folder: never published


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True)
    ap.add_argument("--vm-ip", required=True)
    a = ap.parse_args()
    out = Path(a.out).resolve()
    gate = Path(__file__).resolve().parents[2] / "telemetry" / "scripts" / "secret_gate.py"
    r = subprocess.run(["ssh", "-i", str(qh.KEY), "-o", f"UserKnownHostsFile={qh.KNOWN}", "-o", "BatchMode=yes", f"lab@{a.vm_ip}",
                        "python3 - fingerprints"], input=gate.read_text(), capture_output=True, text=True, timeout=120)
    problems = []
    try:
        new = json.loads(r.stdout)
        problems += sg.fingerprint_problems(new)
    except ValueError:
        new, problems = None, [f"no fingerprints from the VM (exit {r.returncode})"]
    fp = STATE / "secret-fingerprints.json"
    old = json.loads(fp.read_text()) if fp.exists() else None
    if old is not None and sg.fingerprint_problems(old, require_kinds=()):
        problems.append("host fingerprint state malformed")
    findings, failures = [], []
    if not problems:
        merged = sg.merge_fingerprints(old, new)
        STATE.mkdir(exist_ok=True)
        fp.write_text(json.dumps(merged))
        os.chmod(fp, 0o600)
        findings, failures = sg.scan_paths([out], merged["fingerprints"])
    result = {"made": qh.now(), "folder": out.name, "fingerprint_problems": problems,
              "findings": [{"path": os.path.relpath(f["path"], out), "member": f.get("member"), "kind": f["kind"]} for f in findings],
              "unscannable": [{"path": os.path.relpath(x["path"], out), "member": x.get("member"), "error": x.get("error")}
                              for x in failures],
              "publishable": not problems and not findings and not failures}
    (out / "secret-gate.json").write_text(json.dumps(result, indent=1))
    print(json.dumps({k: result[k] if k != "findings" else len(result[k]) for k in result}))
    sys.exit(0 if result["publishable"] else 9)


if __name__ == "__main__":
    main()
