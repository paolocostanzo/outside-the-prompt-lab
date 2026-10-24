#!/usr/bin/env python3
"""Host-side orchestration of the open-weight cells (D39), on top of q3_host.py.

For every cell: restore the clean snapshot, start the VM, copy the harness in, start the recording proxy inside the VM
(record_proxy.py, 127.0.0.1:11435 -> the model endpoint reachable from the VM), run one cell with the open-weight client file,
stop the proxy's output by fetching it with the cell, copy everything out, stop the VM at the end.

The model endpoint must already be reachable from the VM at --upstream (an SSH tunnel to our GPU instance bound to the libvirt
bridge address, opened by hand for the duration of the runs). Nothing here touches processes on the host.

  python3 q3_open_weight_host.py --snapshot q4-base-20261023b --clients qwen,goose --signals none,list_changed \
      --upstream http://192.168.122.1:11434 --out ../../results/q3/open-weight-20261025 --seed 20261025
"""
import argparse
import json
import random
import time
from pathlib import Path

import q3_host as qh

CLIENTS_JSON = "~/lab/tool-change/scripts/q3-clients-open-weight.json"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--snapshot", required=True)
    ap.add_argument("--clients", required=True)
    ap.add_argument("--signals", default="none,list_changed")
    ap.add_argument("--rep", type=int, default=1)
    ap.add_argument("--seed", type=int, required=True)
    ap.add_argument("--upstream", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--probe", action="store_true", help="trial run: proxy + client start only, no cell (validity check)")
    a = ap.parse_args()
    out = Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    h = qh.Host(out)
    cells = [{"client": c, "signal": s} for c in a.clients.split(",") for s in a.signals.split(",")]
    random.Random(a.seed).shuffle(cells)
    (out / "plan.json").write_text(json.dumps({"made": qh.now(), "seed": a.seed, "snapshot": a.snapshot, "upstream": a.upstream,
                                               "probe": a.probe, "cells": cells}, indent=2))
    for i, c in enumerate(cells, 1):
        name = f"{c['client']}__{c['signal']}__description__r{a.rep}" + ("__probe" if a.probe else "")
        if (out / name / ("probe.json" if a.probe else "row.json")).exists():
            continue
        h.mem_ok()
        t0 = time.time()
        ip, boot_s = h.fresh_vm(a.snapshot)
        rc, hashes = h.push_harness(ip)
        h.note(event="cell-start", n=i, of=len(cells), cell=name, ip=ip, boot_s=boot_s, push_rc=rc)
        h.ssh(ip, f"mkdir -p ~/q3-out/{name} && (nohup python3 ~/lab/tool-change/scripts/record_proxy.py --listen 127.0.0.1:11435 "
                  f"--upstream {a.upstream} --out ~/q3-out/{name}/proxy.jsonl --client {c['client']} "
                  f"> ~/q3-out/{name}/proxy.stderr.txt 2>&1 &) ; sleep 1; curl -s -m 20 http://127.0.0.1:11435/api/version",
              timeout=60)
        if a.probe:
            r = h.ssh(ip, f"cd ~/lab/tool-change/scripts && python3 -c \"import json,run_q3_cell as m; m.load_overrides('{CLIENTS_JSON}'); "
                          f"print(m.CLIENTS['{c['client']}']['cmd'])\"", timeout=60)
            (out / f"{name}.stdout.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr)
            h.ssh(ip, f"echo '{{\"cmd_checked\": true}}' > ~/q3-out/{name}/probe.json")
        else:
            r = h.ssh(ip, f"python3 ~/lab/tool-change/scripts/run_q3_cell.py --client {c['client']} --signal {c['signal']} "
                          f"--change description --rep {a.rep} --out ~/q3-out --clients-json {CLIENTS_JSON}", timeout=2400)
            (out / f"{name}.stdout.txt").write_text(r.stdout + "\n--- stderr ---\n" + r.stderr)
            # the cell writes into ~/q3-out/<client>__<signal>__description__r<rep>, the same folder as the proxy log
        h.fetch(ip, name, out / name, int(t0) - 5)
        (out / name / "harness-sha256.txt").write_text(hashes)
        h.note(event="cell-end", cell=name, rc=r.returncode, seconds=round(time.time() - t0),
               row=(out / name / "row.json").exists())
    h.note(event="matrix-done", cells=len(cells))
    qh.run(qh.VIRSH + ["shutdown", qh.DOMAIN])


if __name__ == "__main__":
    main()
