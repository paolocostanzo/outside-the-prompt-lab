#!/usr/bin/env python3
"""Runs INSIDE the disposable VM (Python 3, standard library only). Read-only on the client stores.

  python3 vm_logs.py inventory CANDIDATES.json            # which candidate log files exist now -> JSON on stdout
  python3 vm_logs.py collect CANDIDATES.json START END    # tar.gz of every matching file on stdout; manifest as the
                                                          # first member (manifest.json): path, size, mtime, sha256,
                                                          # and whether the file was modified inside [START, END]

START and END are Unix seconds of the session (D24 point 2). Paths in the manifest are relative to the home directory.
"""
import glob, hashlib, io, json, os, sys, tarfile, time

HOME = os.path.expanduser("~")


def expand(pattern):
    p = os.path.expanduser(pattern)
    return sorted(f for f in glob.glob(p, recursive=True) if os.path.isfile(f) and not os.path.islink(f))


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def describe(path, start=None, end=None):
    st = os.stat(path)
    d = {"path": os.path.relpath(path, HOME), "size": st.st_size, "mtime": int(st.st_mtime), "sha256": sha256(path)}
    if start is not None:
        d["modified_in_session"] = start <= st.st_mtime <= end + 5
    return d


def inventory(candidates):
    out = {}
    for client, patterns in candidates.items():
        if client.startswith("_"):
            continue
        files = []
        for pat in patterns:
            files += [describe(f) | {"pattern": pat} for f in expand(pat)]
        out[client] = {"patterns": patterns, "files": files}
    return {"taken_at": int(time.time()), "home": HOME, "clients": out}


def collect(candidates, start, end, stream):
    manifest = {"start": start, "end": end, "taken_at": int(time.time()), "clients": {}}
    paths = []
    for client, patterns in candidates.items():
        if client.startswith("_"):
            continue
        files = sorted({f for pat in patterns for f in expand(pat)})
        manifest["clients"][client] = [describe(f, start, end) for f in files]
        paths += files
    with tarfile.open(fileobj=stream, mode="w:gz") as tar:
        data = json.dumps(manifest, indent=1).encode()
        info = tarfile.TarInfo("manifest.json"); info.size = len(data); info.mtime = int(time.time())
        tar.addfile(info, io.BytesIO(data))
        for f in paths:
            tar.add(f, arcname="home/" + os.path.relpath(f, HOME), recursive=False)
    return manifest


def main():
    mode, cand = sys.argv[1], json.load(open(sys.argv[2]))
    if mode == "inventory":
        json.dump(inventory(cand), sys.stdout, indent=1)
    elif mode == "collect":
        collect(cand, int(sys.argv[3]), int(sys.argv[4]), sys.stdout.buffer)
    else:
        sys.exit("mode must be inventory or collect")


if __name__ == "__main__":
    main()
