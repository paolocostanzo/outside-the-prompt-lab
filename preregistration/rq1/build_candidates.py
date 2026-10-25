#!/usr/bin/env python3
"""RQ1 frame, step 2: one row per candidate (CVE id, or GHSA id when there is no CVE), merged across GHSA and NVD hits of the
dated query, with the text a screener needs. Mechanical only: no inclusion decision is made here.

    python3 preregistration/rq1/build_candidates.py RAWDIR OUT.json
"""
import glob, gzip, json, pathlib, sys

sys.path.insert(0, str(pathlib.Path(__file__).parent))
from query_frame import text_of_ghsa  # noqa: E402


def load(path):
    """A raw file as saved by query_frame.py, or its gzip copy (the two full GHSA dumps are committed compressed)."""
    path = pathlib.Path(path)
    if not path.exists() and path.with_name(path.name + ".gz").exists():
        return json.loads(gzip.decompress(path.with_name(path.name + ".gz").read_bytes()))
    return json.loads(path.read_text())


def main(raw, out):
    raw = pathlib.Path(raw); c = {}
    def row(k):
        return c.setdefault(k, {"id": k, "ghsa": [], "sources": [], "keywords": [], "published": None, "title": "",
                                "text": "", "packages": [], "refs": []})
    for kind in ("reviewed", "unreviewed"):
        adv = {a["ghsa_id"]: a for a in load(raw / f"ghsa-{kind}.json")}
        for h in load(raw / f"ghsa-{kind}-keyword-hits.json"):
            a = adv[h["ghsa_id"]]; r = row(a.get("cve_id") or a["ghsa_id"])
            r["ghsa"].append(a["ghsa_id"]); r["sources"].append("ghsa-" + kind); r["keywords"] += h["keywords"]
            r["published"] = min(filter(None, [r["published"], a.get("published_at")]))
            r["title"] = r["title"] or a.get("summary") or ""
            r["text"] = r["text"] or (a.get("description") or "")
            r["packages"] += [f"{(v.get('package') or {}).get('ecosystem')}:{(v.get('package') or {}).get('name')}"
                              for v in a.get("vulnerabilities") or [] if v.get("package")]
            r["refs"] += [a.get("html_url")] + [u for u in a.get("references") or [] if isinstance(u, str)][:8]
            if a.get("source_code_location"): r["refs"].append(a["source_code_location"])
    for f in sorted(glob.glob(str(raw / "nvd-*.json"))):
        kw = pathlib.Path(f).stem[4:]
        for v in load(f):
            cve = v["cve"]; r = row(cve["id"])
            if "nvd" not in r["sources"]: r["sources"].append("nvd")
            r["keywords"].append(kw)
            r["published"] = min(filter(None, [r["published"], cve.get("published")]))
            en = next((d["value"] for d in cve.get("descriptions", []) if d.get("lang") == "en"), "")
            if not r["text"]: r["text"] = en
            r["refs"] += [x["url"] for x in cve.get("references", [])][:8]
    for r in c.values():
        for k in ("ghsa", "sources", "keywords", "packages", "refs"):
            r[k] = sorted(dict.fromkeys(filter(None, r[k])))
        r["text"] = r["text"][:1500]
    rows = sorted(c.values(), key=lambda r: (r["published"] or "", r["id"]))
    pathlib.Path(out).write_text(json.dumps(rows, indent=1, ensure_ascii=False))
    print(len(rows), "candidates")


if __name__ == "__main__":
    main(*sys.argv[1:3])
