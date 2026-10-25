#!/usr/bin/env python3
"""RQ1 frame: first public disclosure date of every case (D14 point 2, D44 point 1): the earliest of the global GitHub advisory,
the repository security advisory it links, the CVE record (NVD) and the dated pages listed in disclosure-manual.csv (researcher
write-ups, vendor bulletins). Public issues and pull requests do not count. Writes disclosure-dates.csv, one row per record.

    python3 preregistration/rq1/disclosure_dates.py
Needs gh (authenticated). Standard library otherwise.
"""
import csv, glob, json, pathlib, re, subprocess

HERE = pathlib.Path(__file__).resolve().parent
REPO_ADV = re.compile(r"https://github\.com/([^/]+)/([^/]+)/security/advisories/(GHSA-[\w-]+)")


def gh(path):
    r = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


def main():
    cand = {c["id"]: c for c in json.loads((HERE / "candidates-20261025.json").read_text())}
    nvd = {}
    for f in glob.glob(str(HERE / "raw-20261025" / "nvd-*.json")):
        for v in json.loads(pathlib.Path(f).read_text()):
            nvd[v["cve"]["id"]] = v["cve"].get("published")
    scr = {r["id"]: r for r in csv.DictReader(open(HERE / "screening-20261025.csv", newline=""))}
    for o in csv.DictReader(open(HERE / "screening-overrides.csv", newline="")):
        scr[o["id"]]["decision"] = o["decision"]
    wanted = sorted(r for r, x in scr.items() if x["decision"] == "include" and not x["pilot"])
    manual = {}
    for m in csv.DictReader(open(HERE / "disclosure-manual.csv", newline="")):
        manual.setdefault(m["record"], []).append((m["date"], m["url"], m["kind"]))
    out = []
    for rid in wanted:
        c = cand[rid]; dates = []  # (date, url, kind)
        ghsas = list(c["ghsa"])
        if rid.startswith("GHSA") and rid not in ghsas:
            ghsas.append(rid)
        repo_links = {m.groups() for u in c["refs"] for m in [REPO_ADV.match(u)] if m}
        for g in ghsas:
            a = gh(f"/advisories/{g}")
            if a and a.get("published_at"):
                dates.append((a["published_at"][:10], a["html_url"], "global GHSA"))
                repo_links |= {m.groups() for u in (a.get("references") or []) for m in [REPO_ADV.match(u if isinstance(u, str) else "")] if m}
                if a.get("source_code_location"):
                    sm = re.match(r"https://github\.com/([^/]+)/([^/]+)", a["source_code_location"])
                    if sm:
                        repo_links.add((sm.group(1), sm.group(2).removesuffix(".git"), g))
        for owner, repo, g in sorted(repo_links):
            r = gh(f"/repos/{owner}/{repo}/security-advisories/{g}")
            if r and r.get("published_at"):
                dates.append((r["published_at"][:10], r["html_url"], "repository advisory"))
        if nvd.get(rid):
            dates.append((nvd[rid][:10], f"https://nvd.nist.gov/vuln/detail/{rid}", "CVE record (NVD)"))
        dates += manual.get(rid, [])
        if not dates and c["published"]:
            dates.append((c["published"][:10], f"https://nvd.nist.gov/vuln/detail/{rid}", "query record"))
        first = min(dates)
        out.append({"record": rid, "first_disclosure": first[0], "source_url": first[1], "kind": first[2],
                    "all_dates": "; ".join(f"{d} {k}" for d, u, k in sorted(set(dates)))})
    with open(HERE / "disclosure-dates.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["record", "first_disclosure", "source_url", "kind", "all_dates"], lineterminator="\n")
        w.writeheader(); w.writerows(out)
    print(len(out), "records dated")


if __name__ == "__main__":
    main()
