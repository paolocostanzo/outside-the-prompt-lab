#!/usr/bin/env python3
"""Collection check for one session (D24 point 2), independent of detection.

Inputs: the archive written by `vm_logs.py collect` (host copy), the client that ran, the session window and the ground truth
(the lab server's or the canary's log, which alone establishes that the event happened). Output: one JSON record with
  export: ok | failed (archive unreadable, no manifest, or a file in the manifest missing from the archive / hash mismatch)
  client_logs: wrote | wrote-nothing-in-session | no-default-logs   (from the inventory: no candidate location exists)
  coverage: whether the files written in the session span the event's time (first/last mtime against the ground-truth event)
A session is excluded only when export is "failed"; a client that logs nothing for the event is a valid negative observation.

  python3 collection_check.py ARCHIVE.tgz CLIENT START END --event-time T [--inventory INVENTORY.json]
"""
import argparse, hashlib, io, json, sys, tarfile


def check(archive_path, client, start, end, event_time=None, inventory=None):
    rec = {"client": client, "start": start, "end": end, "event_time": event_time}
    try:
        tar = tarfile.open(archive_path, "r:gz")
        manifest = json.load(tar.extractfile("manifest.json"))
    except (OSError, tarfile.TarError, KeyError, ValueError) as exc:
        return rec | {"export": "failed", "reason": f"archive or manifest unreadable: {exc}"}
    files = manifest.get("clients", {}).get(client, [])
    members = {m.name: m for m in tar.getmembers()}
    for f in files:
        m = members.get("home/" + f["path"])
        if m is None:
            return rec | {"export": "failed", "reason": f"missing from archive: {f['path']}"}
        if hashlib.sha256(tar.extractfile(m).read()).hexdigest() != f["sha256"]:
            return rec | {"export": "failed", "reason": f"hash mismatch: {f['path']}"}
    inv_files = (inventory or {}).get("clients", {}).get(client, {}).get("files")
    written = [f for f in files if start <= f["mtime"] <= end + 5]  # this session's window, not the one used at collection
    if inventory is not None and not inv_files and not files:
        status = "no-default-logs"
    elif written:
        status = "wrote"
    else:
        status = "wrote-nothing-in-session"
    rec |= {"export": "ok", "client_logs": status, "files": len(files), "files_written_in_session": len(written)}
    if written and event_time is not None:
        rec["coverage"] = {"first_mtime": min(f["mtime"] for f in written), "last_mtime": max(f["mtime"] for f in written),
                           "after_event": max(f["mtime"] for f in written) >= event_time}
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("archive"); ap.add_argument("client"); ap.add_argument("start", type=int); ap.add_argument("end", type=int)
    ap.add_argument("--event-time", type=int)
    ap.add_argument("--inventory")
    a = ap.parse_args()
    inv = json.load(open(a.inventory)) if a.inventory else None
    json.dump(check(a.archive, a.client, a.start, a.end, a.event_time, inv), sys.stdout, indent=1)


if __name__ == "__main__":
    main()
