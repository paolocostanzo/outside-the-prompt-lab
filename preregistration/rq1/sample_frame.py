#!/usr/bin/env python3
"""RQ1 sample (D44): stratified random sample of the frozen frame, seeded by a public drand round drawn after the frame is public.

    python3 preregistration/rq1/sample_frame.py draw COMMIT
    python3 preregistration/rq1/sample_frame.py verify     # offline: recompute seed and sample from frame, manifest and B

`draw` checks that COMMIT is an ancestor of the remote master and the head of a GitHub PushEvent, that no commit other than
COMMIT touches the frame in the history of COMMIT or of any head pushed up to the round time, and that this script equals its copy in COMMIT; it derives the one drand round of D44
point 4 from the push (the first 20:00:00 UTC at least one hour after it), records the Internet Archive capture of the commit page
(evidence of the push time; never a reason to redraw), reads the round from two relays, and writes rq1-sample.csv and
rq1-sample-manifest.json next to the frame (refusing to overwrite). There is no fallback beacon. Once a valid frame push exists and the round time
has passed, the draw is binding: tooling failures are fixed and the same round is used. Standard library, git and gh only.
"""
import calendar, csv, datetime, hashlib, io, json, pathlib, subprocess, sys, urllib.parse, urllib.request

HERE = pathlib.Path(__file__).resolve().parent
FRAME = HERE / "rq1-frame.csv"
FRAME_IN_REPO = "preregistration/rq1/rq1-frame.csv"
SCRIPT_IN_REPO = "preregistration/rq1/sample_frame.py"
SAMPLE_COLUMNS = ["case_id", "product_type", "source", "rank", "sampled"]
N = 120
TYPES = ("agent client", "MCP server or connector", "SDK")
SOURCES = ("timeline", "query only")
COLUMNS = ["case_id", "records", "date", "product", "product_type", "source", "primary_source", "decision", "reason", "note"]
DRAND_CHAIN = "8990e7a9aaed2ffed73dbd7092123d6f289930540d7651336225dc172e51b2ce"
DRAND_GENESIS, DRAND_PERIOD = 1595431050, 30
DRAND_RELAYS = ("https://api.drand.sh", "https://drand.cloudflare.com")
REPO = "paolocostanzo/outside-the-prompt-lab"
# Pilot components and their aliases (D3, D41 point 1): never in the frame.
PILOT_RECORDS = {"CVE-2026-55607", "GHSA-7835-87q9-rgvv", "CVE-2026-72718", "GHSA-r5pp-p5r8-466r", "CVE-2026-19590",
                 "GHSA-433v-pqvh-w4gj", "CVE-2026-19592", "GHSA-26wp-42v3-96xp", "CVE-2026-19593", "GHSA-hcf6-9q9g-xx3c",
                 "CVE-2026-59726", "GHSA-c4hm-4h84-2cf3", "CVE-2026-59950", "GHSA-vj7q-gjh5-988w", "CVE-2026-15015",
                 "GHSA-8g44-6rrm-mf2w"}


def round_time(r):
    return DRAND_GENESIS + (r - 1) * DRAND_PERIOD


def first_round_after(push_ts):
    """The drand round of D44 point 4: the first 20:00:00 UTC at least one hour after the given time (the capture)."""
    t = push_ts + 3600
    d = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
    at = d.replace(hour=20, minute=0, second=0, microsecond=0)
    if at.timestamp() < t:
        at += datetime.timedelta(days=1)
    return (int(at.timestamp()) - DRAND_GENESIS) // DRAND_PERIOD + 1


def read_frame(raw):
    """Validated rows of the frame; every row must be decided, typed and outside the pilot."""
    if raw.startswith(b"\xef\xbb\xbf"):
        sys.exit("frame has a byte-order mark")
    rd = csv.DictReader(io.StringIO(raw.decode("utf-8")))
    if rd.fieldnames != COLUMNS:
        sys.exit(f"frame columns must be exactly {COLUMNS}")
    rows = list(rd)
    ids = [r["case_id"] for r in rows]
    if not rows or any(not i.strip() for i in ids) or len(set(ids)) != len(ids):
        sys.exit("empty frame, empty or duplicate case ids")
    for r in rows:
        if r["decision"] not in ("include", "exclude"):
            sys.exit(f"{r['case_id']}: decision {r['decision']!r} is not include/exclude (resolve every uncertain case first)")
        if not r["reason"].strip():
            sys.exit(f"{r['case_id']}: no reason")
        if r["decision"] == "include":
            if r["product_type"] not in TYPES: sys.exit(f"{r['case_id']}: product type {r['product_type']!r}")
            if r["source"] not in SOURCES: sys.exit(f"{r['case_id']}: source {r['source']!r}")
            if pil := {x.strip().upper() for x in r["records"].split(";")} & {x.upper() for x in PILOT_RECORDS}: sys.exit(f"{r['case_id']}: pilot records {sorted(pil)}")
    return [r for r in rows if r["decision"] == "include"]


def allocate(sizes, n):
    """Largest-remainder allocation of n places over sizes, at least one per non-empty stratum, never more than its size."""
    total = sum(sizes.values())
    if n >= total:
        return dict(sizes)
    if n < sum(1 for v in sizes.values() if v):
        sys.exit("fewer places than non-empty strata")
    quota = {k: n * v / total for k, v in sizes.items()}
    alloc = {k: min(sizes[k], max(1 if sizes[k] else 0, int(q))) for k, q in quota.items()}
    while sum(alloc.values()) < n:
        k = max((k for k in sizes if alloc[k] < sizes[k]), key=lambda k: (quota[k] - alloc[k], k))
        alloc[k] += 1
    while sum(alloc.values()) > n:  # only when the minimum of one pushed the total over
        k = max((k for k in sizes if alloc[k] > 1), key=lambda k: (alloc[k] - quota[k], k))
        alloc[k] -= 1
    return alloc


def seed_of(frame_sha256, beacon):
    return hashlib.sha256(f"{frame_sha256}:{beacon}".encode()).hexdigest()


def sample(rows, seed, n=N):
    """Strata = product types (timeline cases sit in theirs). Returns the sizes, the allocation and every case in its stratum's order."""
    key = lambda r: hashlib.sha256(f"{seed}:{r['case_id']}".encode()).hexdigest()
    sizes = {t: sum(r["product_type"] == t for r in rows) for t in TYPES}
    alloc = allocate(sizes, n)
    out = []
    for t in TYPES:
        for i, r in enumerate(sorted((r for r in rows if r["product_type"] == t), key=key)):
            out.append({"case_id": r["case_id"], "product_type": t, "source": r["source"], "rank": i + 1,
                        "sampled": "yes" if i < alloc[t] else "no"})
    return sizes, alloc, out


def git(*a):
    return subprocess.run(["git", "-C", str(HERE), *a], capture_output=True, check=True).stdout


def fetch_round(r, chain=DRAND_CHAIN):
    vals = set()
    for relay in DRAND_RELAYS:
        with urllib.request.urlopen(f"{relay}/{chain}/public/{r}", timeout=30) as resp:
            d = json.load(resp)
        if d.get("round") != r:
            sys.exit(f"{relay}: returned round {d.get('round')}, not {r}")
        vals.add(d["randomness"])
    if len(vals) != 1:
        sys.exit(f"drand relays disagree on round {r}")
    return vals.pop()


def frame_blob(commit):
    """The frame's blob id at commit, or None when the commit has no frame."""
    if not git_ok("cat-file", "-e", f"{commit}:{FRAME_IN_REPO}"):
        return None
    return git("rev-parse", f"{commit}:{FRAME_IN_REPO}").decode().strip()


def frame_commits(head):
    """Every commit in the history of head that adds or changes the frame, with no history simplification: non-merge commits
    touching it, and merges whose frame differs from the frame of every parent (a change made while resolving the merge)."""
    plain = git("log", "--full-history", "--no-merges", "--format=%H", head, "--", FRAME_IN_REPO).decode().split()
    merges = []
    for line in git("log", "--full-history", "--merges", "--format=%H %P", head, "--", FRAME_IN_REPO).decode().splitlines():
        m, *parents = line.split()
        if all(frame_blob(m) != frame_blob(p) for p in parents):
            merges.append(m)
    return plain + merges


def git_ok(*a):
    return subprocess.run(["git", "-C", str(HERE), *a], capture_output=True).returncode == 0


def push_events():
    r = subprocess.run(["gh", "api", "--paginate", f"repos/{REPO}/events", "--jq", '.[] | select(.type == "PushEvent")'],
                       capture_output=True, text=True, check=True)
    return [json.loads(line) for line in r.stdout.splitlines() if line.strip()]


def first_capture(url):
    """Unix time of the first Internet Archive capture of url, or None."""
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode({"url": url, "output": "json", "limit": 1})
    with urllib.request.urlopen(q, timeout=60) as resp:
        rows = json.load(resp)
    if len(rows) < 2:
        return None
    return calendar.timegm(datetime.datetime.strptime(rows[1][1], "%Y%m%d%H%M%S").timetuple())


def archived_event(sha, push_ts):
    """Unix time of an Internet Archive capture of the repository events page, made within 30 minutes after the push, that
    holds the PushEvent of sha; None if there is none."""
    url = f"https://api.github.com/repos/{REPO}/events"
    fmt = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).strftime("%Y%m%d%H%M%S")
    q = "https://web.archive.org/cdx/search/cdx?" + urllib.parse.urlencode(
        {"url": url, "output": "json", "from": fmt(push_ts), "to": fmt(push_ts + 1800)})
    with urllib.request.urlopen(q, timeout=60) as resp:
        rows = json.load(resp)[1:]
    for row in rows:
        with urllib.request.urlopen(f"https://web.archive.org/web/{row[1]}id_/{url}", timeout=60) as resp:
            body = json.load(resp)
        if any(e.get("type") == "PushEvent" and e.get("payload", {}).get("head") == sha for e in body):
            return calendar.timegm(datetime.datetime.strptime(row[1], "%Y%m%d%H%M%S").timetuple())
    return None


def independently_verifiable(capture):
    return capture["within_30_min_after_push"] or bool(capture.get("events_page_utc"))


def ts(iso):
    return calendar.timegm(datetime.datetime.strptime(iso, "%Y-%m-%dT%H:%M:%SZ").timetuple())


def main(commit):
    git("fetch", "--quiet", "--all")
    sha = git("rev-parse", commit).decode().strip()
    raw = git("show", f"{sha}:{FRAME_IN_REPO}")
    if git("show", f"{sha}:{SCRIPT_IN_REPO}") != pathlib.Path(__file__).read_bytes():
        sys.exit("this script differs from its copy in the frame commit")
    master = git("ls-remote", "origin", "refs/heads/master").decode().split()[0]
    if not git_ok("merge-base", "--is-ancestor", sha, master):
        sys.exit("the frame commit is not an ancestor of the remote master")
    events = push_events()
    mine = [e for e in events if e["payload"].get("head") == sha]
    if not mine:
        sys.exit(f"no PushEvent with head {sha}: the frame commit must be pushed alone as head (or GitHub events lag; retry)")
    push = min(mine, key=lambda e: e["created_at"]); push_ts = ts(push["created_at"])
    if int(git("show", "-s", "--format=%ct", sha)) > push_ts:
        sys.exit("commit date later than the push: refused")
    rnd = first_round_after(push_ts)
    t = round_time(rnd); when = datetime.datetime.fromtimestamp(t, datetime.timezone.utc)
    now = datetime.datetime.now(datetime.timezone.utc).timestamp()
    if t > now:
        sys.exit(f"round {rnd} ({when.isoformat()}) is not drawn yet")
    # Only versions pushed up to the round time count; later pushes cannot void the draw. In the history of the frame commit
    # and of every head pushed up to then, intermediate commits included, the frame commit is the only one touching the frame.
    for h in [sha] + [e["payload"].get("head") for e in events if ts(e["created_at"]) <= t and e["payload"].get("head") != sha]:
        if not git_ok("cat-file", "-e", h):
            sys.exit(f"pushed head {h} cannot be checked locally: fetch it (the draw waits, it is not redone)")
        if other := [c for c in frame_commits(h) if c != sha]:
            sys.exit(f"commit {other[0]} in the history of {h} also adds or changes the frame: the draw is void (D44 point 4)")
        if git_ok("cat-file", "-e", f"{h}:{FRAME_IN_REPO}") and git("show", f"{h}:{FRAME_IN_REPO}") != raw:
            sys.exit(f"pushed head {h} carries a different frame (e.g. through a merge): the draw is void (D44 point 4)")
    cap = first_capture(f"https://github.com/{REPO}/commit/{sha}")
    ev_cap = archived_event(sha, push_ts)
    iso = lambda t: datetime.datetime.fromtimestamp(t, datetime.timezone.utc).isoformat() if t else None
    capture = {"utc": iso(cap), "within_30_min_after_push": bool(cap and push_ts <= cap <= push_ts + 1800),
               "events_page_utc": iso(ev_cap)}
    chain_hash, beacon_round = DRAND_CHAIN, rnd
    beacon = fetch_round(beacon_round, chain_hash)
    rows = read_frame(raw)
    f_sha = hashlib.sha256(raw).hexdigest(); seed = seed_of(f_sha, beacon)
    sizes, alloc, out = sample(rows, seed)
    dest, man = HERE / "rq1-sample.csv", HERE / "rq1-sample-manifest.json"
    if dest.exists() or man.exists():
        sys.exit("the sample exists: it is drawn once (D44 point 4)")
    with open(dest, "x", newline="") as f:
        w = csv.DictWriter(f, fieldnames=SAMPLE_COLUMNS); w.writeheader(); w.writerows(out)
    with open(man, "x") as f:
        json.dump({"frame_commit": sha, "frame_sha256": f_sha, "push_event": push, "capture": capture,
                   "script_sha256": hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest(),
                   "drand_chain": chain_hash, "drand_round": beacon_round, "mainnet_round": rnd, "drand_round_time": when.isoformat(),
                   "drand_randomness": beacon, "seed": seed, "n": N, "stratum_sizes": sizes, "allocation": alloc,
                   "sampled": sum(r["sampled"] == "yes" for r in out)}, f, indent=2)
    print(f"seed {seed}; sizes {sizes}; allocation {alloc}")


def verify(sample_csv=None, manifest=None, online=False):
    """Recompute the seed and the sample from the frame in the frame commit, the manifest's beacon value and this script.
    Offline it trusts the manifest's beacon value; with online=True it reads the round from the drand relays again."""
    m = json.loads(pathlib.Path(manifest or HERE / "rq1-sample-manifest.json").read_text())
    raw = git("show", f"{m['frame_commit']}:{FRAME_IN_REPO}")
    if hashlib.sha256(raw).hexdigest() != m["frame_sha256"]:
        sys.exit("frame hash differs from the manifest")
    if seed_of(m["frame_sha256"], m["drand_randomness"]) != m["seed"]:
        sys.exit("seed does not follow from the frame and the beacon")
    t = round_time(first_round_after(ts(m["push_event"]["created_at"])))
    expected = (DRAND_CHAIN, (t - DRAND_GENESIS) // DRAND_PERIOD + 1)
    if (m["drand_chain"], m["drand_round"]) != expected:
        sys.exit("the round does not follow from the push time")
    if not independently_verifiable(m["capture"]):
        print("round not independently verifiable: no timely Internet Archive capture of the commit page or of the push event; "
              "it rests on the stored event only (reported in the paper, D44 point 4)")
    if online and fetch_round(m["drand_round"], m["drand_chain"]) != m["drand_randomness"]:
        sys.exit("the beacon value differs from drand")
    _, _, out = sample(read_frame(raw), m["seed"])
    with open(sample_csv or HERE / "rq1-sample.csv", newline="") as f:
        got = [dict(r) for r in csv.DictReader(f)]
    if got != [{k: str(v) for k, v in r.items()} for r in out]:
        sys.exit("the published sample differs from the recomputed one")
    print("sample verified")


if __name__ == "__main__":
    if sys.argv[1:2] == ["draw"] and len(sys.argv) == 3:
        main(sys.argv[2])
    elif sys.argv[1:] in (["verify"], ["verify", "online"]):
        verify(online=len(sys.argv) == 3)
    else:
        sys.exit(__doc__)
