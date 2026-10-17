#!/usr/bin/env python3
"""Secret gate (D26). The author's rule of 17 Oct 2026: no secret may ever be published. A secret here is any token, API key or
login file of the lab's clients, and anything inside them. This script never prints, logs or writes a secret's value.

  python3 secret_gate.py fingerprints                          # INSIDE the VM: JSON fingerprints of every lab secret on stdout
  python3 secret_gate.py scan [--fingerprints FP.json] PATH... # files, folders and archives; exit 1 on a finding
  python3 secret_gate.py scan-git [--fingerprints FP.json] [--repo DIR] BASE HEAD
                                                               # every blob added or changed by every commit in BASE..HEAD,
                                                               # and the commit messages; BASE may be the empty tree

Two kinds of matching:
- *exact*: a fingerprint is {kind, source, length, prefix (first 4 characters), sha256}. Every occurrence of a prefix is checked by
  hashing the bytes of the recorded length that start there. Exact matching needs fingerprints taken inside the VM and finds a
  secret whatever its format;
- *format*: known token formats (Anthropic, Google API keys, JWTs, OpenAI keys, GitHub tokens, private keys, token fields in JSON,
  secret environment variables with a literal value). It needs no fingerprint, and also finds a secret that was renewed after the
  fingerprints were taken.

Archives (.tar, .tgz, .tar.gz, .gz, .zip, .xz, .bz2) are scanned member by member, nested up to three levels. A file that cannot
be read or decompressed, or an archive format the script cannot open, is a failure (exit 2): the gate fails closed. Findings are
reported with the file, the archive member, the line (format matches) and the kind, never with the value.
Exit codes: 0 clean, 1 at least one finding, 2 something could not be scanned (and no finding).
"""
import argparse, bz2, gzip, hashlib, io, json, lzma, os, re, socket, subprocess, sys, tarfile, time, zipfile
from pathlib import Path

MIN_LEN = 16          # shorter values are not fingerprinted (too many accidental matches, and not secrets)
PREFIX = 4
MAX_DEPTH = 3
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"

FORMATS = [
    ("anthropic-token", rb"sk-ant-[a-z]{2,8}[0-9]{0,3}-[A-Za-z0-9_\-]{20,}"),
    ("google-api-key", rb"AIza[0-9A-Za-z_\-]{35}"),
    ("jwt", rb"eyJ[A-Za-z0-9_\-]{8,}\.eyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}"),
    ("openai-key", rb"(?<![A-Za-z0-9_\-])sk-(?!ant-)(?:proj-|svcacct-|admin-)?[A-Za-z0-9_\-]{32,}"),
    ("github-token", rb"(?<![A-Za-z0-9_])(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{36}|github_pat_[A-Za-z0-9_]{60,}"),
    ("private-key", rb"-----BEGIN (?:[A-Z]+ )*PRIVATE KEY-----"),
    ("token-field", rb"[\"'](?:access_token|refresh_token|id_token|accessToken|refreshToken|idToken|api_key|apiKey|"
                    rb"client_secret|clientSecret)[\"']\s*:\s*[\"'][^\"'\s]{16,}[\"']"),
    ("secret-env", rb"(?<![A-Za-z0-9_])(?:CLAUDE_CODE_OAUTH_TOKEN|ANTHROPIC_API_KEY|ANTHROPIC_AUTH_TOKEN|GEMINI_API_KEY|"
                   rb"GOOGLE_API_KEY|OPENAI_API_KEY|CODEX_ACCESS_TOKEN|DASHSCOPE_API_KEY|OPENROUTER_API_KEY)\s*[=:]\s*"
                   rb"[\"']?(?![\"']?\$)[A-Za-z0-9_\-./+=]{16,}"),
]
FORMATS = [(k, re.compile(p)) for k, p in FORMATS]

# --------------------------------------------------------------------------- fingerprints (inside the VM)
HOME = Path(os.path.expanduser("~"))
# (kind, path relative to HOME, how to read it)
SOURCES = [
    ("claude-oauth-token", ".agentlab_claude_token", "raw"),
    ("claude-login", ".claude/.credentials.json", "json"),
    ("claude-login", ".agentlab_claude_interactive.json", "json"),
    ("codex-login", ".codex/auth.json", "json"),
    ("cursor-login", ".config/cursor/auth.json", "json"),
    ("lab-secret", ".agentlab_secrets", "env"),
    ("goose-secret", ".config/goose/secrets.yaml", "yaml"),
    ("gemini-settings", ".gemini/settings.json", "json-keys"),
    ("qwen-settings", ".qwen/settings.json", "json-keys"),
    ("gemini-env", ".gemini/.env", "env"),
    ("qwen-env", ".qwen/.env", "env"),
]
SECRET_KEY = re.compile(r"(token|secret|key|password|credential|auth)", re.I)


def _strings(obj, keyed=False, key=""):
    """String values of a JSON document: all of them, or (keyed) only those under a key that names a secret."""
    if isinstance(obj, dict):
        for k, v in obj.items():
            yield from _strings(v, keyed, str(k))
    elif isinstance(obj, list):
        for v in obj:
            yield from _strings(v, keyed, key)
    elif isinstance(obj, str) and (not keyed or SECRET_KEY.search(key)):
        yield obj


def values_of(path, how):
    text = path.read_text(encoding="utf-8", errors="replace")
    if how == "raw":
        return [text.strip()]
    if how in ("json", "json-keys"):
        return list(_strings(json.loads(text), keyed=(how == "json-keys")))
    if how == "env":
        out = []
        for line in text.splitlines():
            m = re.match(r"\s*(?:export\s+)?[A-Za-z_][A-Za-z0-9_]*\s*=\s*(.*)$", line)
            if m:
                out.append(m.group(1).strip().strip("'\""))
        return out
    if how == "yaml":  # flat key: value files only
        return [m.group(1).strip().strip("'\"") for m in (re.match(r"\s*[^:#]+:\s*(.+)$", l) for l in text.splitlines()) if m]
    raise ValueError(how)


def fingerprint(value, kind, source):
    b = value.encode()
    return {"kind": kind, "source": source, "length": len(b), "prefix": value[:PREFIX],
            "sha256": hashlib.sha256(b).hexdigest()}


def fingerprints(home=HOME, sources=SOURCES):
    """Fingerprints of every secret value found in the lab's known stores. A store that exists but cannot be read or parsed is
    listed under "unreadable": the caller must treat that as a failure, since its secrets would go unchecked."""
    fps, seen, unreadable, absent = [], set(), [], []
    for kind, rel, how in sources:
        p = home / rel
        if not p.exists():
            absent.append(rel)
            continue
        try:
            vals = values_of(p, how)
        except (OSError, ValueError) as exc:
            unreadable.append({"source": rel, "error": type(exc).__name__})
            continue
        for v in vals:
            if len(v.encode()) >= MIN_LEN and v not in seen:
                seen.add(v)
                fps.append(fingerprint(v, kind, rel))
    return {"created": int(time.time()), "host": socket.gethostname(), "fingerprints": fps, "unreadable": unreadable,
            "absent": absent}


def merge_fingerprints(old, new):
    """Union of two fingerprint files (a secret renewed during the campaign keeps the old fingerprint as well)."""
    out, seen = dict(new), set()
    out["fingerprints"] = []
    for f in (old or {}).get("fingerprints", []) + new.get("fingerprints", []):
        if f["sha256"] not in seen:
            seen.add(f["sha256"])
            out["fingerprints"].append(f)
    return out


# --------------------------------------------------------------------------- scanning
class Unscannable(Exception):
    pass


def _exact(data, fps):
    hits = []
    for f in fps:
        pre, n, want = f["prefix"].encode(), f["length"], f["sha256"]
        i = data.find(pre)
        while i != -1:
            if hashlib.sha256(data[i:i + n]).hexdigest() == want:
                hits.append(f["kind"])
                break
            i = data.find(pre, i + 1)
    return hits


def scan_bytes(data, fps=()):
    """[(kind, line or None)] for one blob of bytes; never the matched text."""
    found = [(k, None) for k in _exact(data, fps)]
    for kind, rx in FORMATS:
        for m in rx.finditer(data):
            found.append((kind, data.count(b"\n", 0, m.start()) + 1))
    return found


def _open_archive(name, data):
    """Members of an archive as (member name, bytes), or None if data is not an archive."""
    low = name.lower()
    try:
        if low.endswith((".tar", ".tgz", ".tar.gz", ".tar.xz", ".tar.bz2", ".txz", ".tbz2")) or (
                len(data) > 262 and data[257:262] == b"ustar"):
            with tarfile.open(fileobj=io.BytesIO(data), mode="r:*") as t:
                return [(m.name, t.extractfile(m).read()) for m in t.getmembers() if m.isfile()]
        if low.endswith(".zip") or data[:4] == b"PK\x03\x04":
            with zipfile.ZipFile(io.BytesIO(data)) as z:
                return [(i.filename, z.read(i)) for i in z.infolist() if not i.is_dir()]
        if low.endswith(".gz") or data[:2] == b"\x1f\x8b":
            return [(name[:-3] if low.endswith(".gz") else name + "!gunzip", gzip.decompress(data))]
        if low.endswith(".xz") or data[:6] == b"\xfd7zXZ\x00":
            return [(name[:-3] if low.endswith(".xz") else name + "!unxz", lzma.decompress(data))]
        if low.endswith(".bz2") or data[:3] == b"BZh":
            return [(name[:-4] if low.endswith(".bz2") else name + "!bunzip2", bz2.decompress(data))]
    except (tarfile.TarError, zipfile.BadZipFile, OSError, EOFError, lzma.LZMAError, ValueError) as exc:
        raise Unscannable(f"{type(exc).__name__}") from exc
    if low.endswith((".7z", ".zst", ".rar", ".lz4")):
        raise Unscannable("archive format not supported")
    return None


def scan_blob(label, data, fps=(), depth=0):
    """Findings [{path, member, kind, line}] and failures [{path, error}] for one blob, archives opened recursively."""
    findings, failures = [], []
    path, _, member = label.partition("::")
    for kind, line in scan_bytes(data, fps):
        findings.append({"path": path, "member": member or None, "kind": kind, "line": line})
    try:
        members = _open_archive(member or path, data)
    except Unscannable as exc:
        return findings, failures + [{"path": path, "member": member or None, "error": str(exc)}]
    if members is not None:
        if depth >= MAX_DEPTH:
            return findings, failures + [{"path": path, "member": member or None, "error": "archives nested too deep"}]
        for mname, mdata in members:
            f2, e2 = scan_blob(path + "::" + (member + "/" if member else "") + mname, mdata, fps, depth + 1)
            findings += f2
            failures += e2
    return findings, failures


def scan_paths(paths, fps=(), skip=()):
    findings, failures = [], []
    for root in paths:
        root = Path(root)
        if not root.exists():
            failures.append({"path": str(root), "member": None, "error": "does not exist"})
            continue
        if root.is_file():
            files = [root]
        else:  # a symlink is read through: what it points to is what would be published
            files = sorted(p for p in root.rglob("*")
                           if (p.is_file() or p.is_symlink()) and not set(p.relative_to(root).parts[:-1]) & set(skip))
        for p in files:
            try:
                data = p.read_bytes()
            except OSError as exc:
                failures.append({"path": str(p), "member": None, "error": type(exc).__name__})
                continue
            f, e = scan_blob(str(p), data, fps)
            findings += f
            failures += e
    return findings, failures


def _git(repo, *args, binary=False):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if r.returncode != 0:
        raise Unscannable(f"git {args[0]} failed: {r.stderr.decode(errors='replace').strip()[:200]}")
    return r.stdout if binary else r.stdout.decode()


def scan_git(repo, base, head, fps=()):
    """Every blob added or modified by every commit in base..head (so a secret added and later removed is still found: it would
    stay in the published history), and every commit message in the range."""
    findings, failures = [], []
    try:
        rng = head if base == EMPTY_TREE else f"{base}..{head}"
        commits = _git(repo, "rev-list", "--reverse", rng).split()
        for c in commits:
            msg = _git(repo, "log", "-1", "--format=%B", c, binary=True)
            f, _ = scan_blob(f"commit {c[:12]} message", msg, fps)
            findings += f
            names = _git(repo, "diff-tree", "-r", "--root", "--no-commit-id", "--name-only", "--diff-filter=ACMRT", "-z", c,
                         binary=True).split(b"\0")
            for n in filter(None, names):
                path = n.decode(errors="replace")
                try:
                    data = _git(repo, "cat-file", "blob", f"{c}:{path}", binary=True)
                except Unscannable as exc:
                    failures.append({"path": f"{c[:12]}:{path}", "member": None, "error": str(exc)})
                    continue
                f, e = scan_blob(f"{c[:12]}:{path}", data, fps)
                findings += f
                failures += e
    except Unscannable as exc:
        failures.append({"path": str(repo), "member": None, "error": str(exc)})
    return findings, failures


def load_fps(path):
    if not path:
        return []
    d = json.loads(Path(path).read_text())
    if d.get("unreadable"):
        raise SystemExit(f"fingerprint file lists unreadable stores {[u['source'] for u in d['unreadable']]}: refusing to scan "
                         "with an incomplete set")
    return d.get("fingerprints", [])


def report(findings, failures, out=sys.stdout):
    json.dump({"findings": findings, "failures": failures}, out, indent=1)
    out.write("\n")
    return 1 if findings else (2 if failures else 0)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    sub = ap.add_subparsers(dest="mode", required=True)
    sub.add_parser("fingerprints")
    s = sub.add_parser("scan")
    s.add_argument("--fingerprints")
    s.add_argument("--skip", action="append", default=[], help="folder name to skip (repeatable)")
    s.add_argument("paths", nargs="+")
    g = sub.add_parser("scan-git")
    g.add_argument("--fingerprints")
    g.add_argument("--repo", default=".")
    g.add_argument("base")
    g.add_argument("head")
    a = ap.parse_args(argv)
    if a.mode == "fingerprints":
        d = fingerprints()
        json.dump(d, sys.stdout, indent=1)
        sys.stdout.write("\n")
        return 2 if d["unreadable"] else 0
    fps = load_fps(a.fingerprints)
    if a.mode == "scan":
        return report(*scan_paths(a.paths, fps, set(a.skip)))
    return report(*scan_git(a.repo, a.base, a.head, fps))


if __name__ == "__main__":
    sys.exit(main())
