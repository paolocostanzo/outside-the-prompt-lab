#!/usr/bin/env python3
"""RQ1 frame, step 1: the dated query of D1 (GitHub Advisory Database and NVD, 26 Jun – 24 Sep 2026), raw results saved.

    python3 preregistration/rq1/query_frame.py OUTDIR

GitHub's global advisory API has no free-text search: every reviewed and unreviewed advisory published in the window is saved
(malware advisories are not vulnerabilities and are not requested), then filtered by the D1 keywords. NVD is queried once per D1
keyword with its own keyword search. Everything fetched is written as returned; `query.json` records when and how. Needs `gh`
(authenticated) for the GitHub API. Standard library otherwise.
"""
import datetime, json, pathlib, re, subprocess, sys, time, urllib.parse, urllib.request

WINDOW = ("2026-06-26", "2026-09-24")
KEYWORDS = ["MCP", "Model Context Protocol", "AI agent", "coding agent", "Copilot", "Claude Code", "Cursor", "Gemini CLI", "Codex"]
NVD = "https://services.nvd.nist.gov/rest/json/cves/2.0"


def ghsa(kind):
    r = subprocess.run(["gh", "api", "-X", "GET", "/advisories", "-f", f"published={WINDOW[0]}..{WINDOW[1]}", "-f", f"type={kind}",
                        "-f", "per_page=100", "--paginate", "--jq", ".[]"], capture_output=True, text=True, check=True)
    return [json.loads(line) for line in r.stdout.splitlines() if line.strip()]  # one advisory per line


def nvd(keyword):
    out, start = [], 0
    while True:
        q = urllib.parse.urlencode({"keywordSearch": keyword, "pubStartDate": WINDOW[0] + "T00:00:00.000",
                                    "pubEndDate": WINDOW[1] + "T23:59:59.999", "resultsPerPage": 2000, "startIndex": start})
        with urllib.request.urlopen(NVD + "?" + q, timeout=120) as r:
            d = json.load(r)
        out += d.get("vulnerabilities", [])
        start += d.get("resultsPerPage", 0)
        time.sleep(7)  # NVD without an API key: 5 requests per 30 s
        if start >= d.get("totalResults", 0) or not d.get("resultsPerPage"):
            return d.get("totalResults", 0), out


def text_of_ghsa(a):
    pk = " ".join((v.get("package") or {}).get("name") or "" for v in a.get("vulnerabilities") or [])
    return " ".join([a.get("summary") or "", a.get("description") or "", pk, a.get("source_code_location") or ""])


def matches(text):
    """D1 keywords, whole words and case-insensitive; "MCP" also matches as part of package names (e.g. foo-mcp)."""
    found = []
    for k in KEYWORDS:
        if k == "MCP":
            if re.search(r"(?<![A-Za-z])mcp(?![A-Za-z])", text, re.I): found.append(k)
        elif re.search(r"\b" + re.escape(k) + r"\b", text, re.I):
            found.append(k)
    return found


def main(outdir):
    out = pathlib.Path(outdir); out.mkdir(parents=True, exist_ok=False)
    started = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    meta = {"started": started, "window": WINDOW, "keywords": KEYWORDS, "sources": {}}
    for kind in ("reviewed", "unreviewed"):
        adv = ghsa(kind)
        (out / f"ghsa-{kind}.json").write_text(json.dumps(adv, indent=1, ensure_ascii=False))
        hits = [{"ghsa_id": a["ghsa_id"], "cve_id": a.get("cve_id"), "published": a.get("published_at"), "summary": a.get("summary"),
                 "keywords": m, "url": a.get("html_url")} for a in adv if (m := matches(text_of_ghsa(a)))]
        (out / f"ghsa-{kind}-keyword-hits.json").write_text(json.dumps(hits, indent=1, ensure_ascii=False))
        meta["sources"][f"ghsa-{kind}"] = {"fetched": len(adv), "keyword_hits": len(hits)}
    nvd_all = {}
    for k in KEYWORDS:
        total, vulns = nvd(k)
        (out / f"nvd-{re.sub(r'[^a-z0-9]+', '-', k.lower())}.json").write_text(json.dumps(vulns, indent=1, ensure_ascii=False))
        meta["sources"][f"nvd:{k}"] = {"total": total, "fetched": len(vulns)}
        for v in vulns:
            nvd_all[v["cve"]["id"]] = v
    meta["nvd_unique_cves"] = len(nvd_all)
    meta["finished"] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds")
    (out / "query.json").write_text(json.dumps(meta, indent=1))
    print(json.dumps(meta, indent=1))


if __name__ == "__main__":
    main(sys.argv[1])
