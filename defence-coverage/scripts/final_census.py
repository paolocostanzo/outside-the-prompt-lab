#!/usr/bin/env python3
"""Final RQ4 census and coverage tables (D17 points 3, 4 and 6; D22; D23), for an explicit list of servers only.

Inputs: the frozen first reading, Codex's second reading (valid sessions only), and the author's adjudication sheet (one row per
disagreement and per tool found by one reading only, with decision_class, decision_protection, decision_vendor_only filled in).
A tool's final label is the two readings' common label where they agree, and the author's decision otherwise; a tool that needs
a decision and has none stops the script. Only the servers named with --servers are read into the outputs, so that servers whose
figures cannot be published (vendors in coordination) never reach a public file. Servers named with --no-defence (D23) are kept
in the census table but leave the coverage figures.

  python3 final_census.py --first FIRST.csv --second SECOND.csv --adjudication ADJUDICATION.csv --servers a,b,c \
      [--no-defence NAME ...] --out DIR
Writes DIR/final-census.csv, DIR/coverage.json and DIR/COVERAGE.md.
"""
import argparse, csv, hashlib, importlib.util, json, statistics
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("compare_census", HERE / "compare_census.py")
cmpc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(cmpc)

PROTECTIONS = {"full", "partial", "none"}


def norm_decision(r):
    c, p, v = (r.get("decision_class") or "").strip(), (r.get("decision_protection") or "").strip(), \
        (r.get("decision_vendor_only") or "").strip().lower()
    if not (c and p and v):
        return None
    if c not in ("A", "not-A") or v not in ("true", "false") or (c == "A") != (p in PROTECTIONS) or (c == "not-A" and p != "n-a"):
        raise SystemExit(f"invalid decision for {r['server']} · {r['tool']}: {c}/{p}/{v}")
    return {"class": c, "protection": p, "vendor_only": v}


def first_label(r):
    return {"class": cmpc.cls(r), "protection": cmpc.prot_first(r), "vendor_only": cmpc.flag(r, "contested")}


def second_label(r):
    return {"class": cmpc.cls(r), "protection": cmpc.prot_second(r), "vendor_only": cmpc.flag(r, "vendor_only")}


def final_rows(first, second, decisions, servers):
    rows, missing = [], []
    keys = sorted(k for k in set(first) | set(second) if k[0] in servers)
    for k in keys:
        if k in decisions and decisions[k] is not None:
            rows.append({"server": k[0], "tool": k[1], **decisions[k], "source": "adjudicated"})
            continue
        if k in first and k in second:
            f, s = first_label(first[k][0]), second_label(second[k][0])
            if f == s or (f["class"] == s["class"] == "not-A"):  # non-A rows: the comparison does not adjudicate them
                rows.append({"server": k[0], "tool": k[1], **f, "source": "agreed"})
                continue
        missing.append(k)
    if missing:
        raise SystemExit(f"{len(missing)} tool(s) need a decision in the adjudication sheet, e.g. {missing[:3]}")
    return rows


def coverage(rows, servers, exclude_vendor_only=False):
    per = {}
    for r in rows:
        if r["server"] not in servers or r["class"] != "A" or (exclude_vendor_only and r["vendor_only"] == "true"):
            continue
        s = per.setdefault(r["server"], {"A": 0, "full": 0, "partial": 0, "none": 0})
        s["A"] += 1
        s[r["protection"]] += 1
    for s in per.values():
        s["cov_full"], s["cov_any"] = s["full"] / s["A"], (s["full"] + s["partial"]) / s["A"]
    sel = list(per.values())
    A = sum(s["A"] for s in sel)
    summ = {"servers": len(sel)}
    if sel:
        summ |= {"mean_full": statistics.mean(s["cov_full"] for s in sel), "median_full": statistics.median(s["cov_full"] for s in sel),
                 "mean_any": statistics.mean(s["cov_any"] for s in sel), "median_any": statistics.median(s["cov_any"] for s in sel),
                 "pooled_full": [sum(s["full"] for s in sel), A], "pooled_any": [sum(s["full"] + s["partial"] for s in sel), A]}
    return {"per_server": per, "summary": summ}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    ap = argparse.ArgumentParser()
    for k in ("first", "second", "adjudication", "servers", "out"):
        ap.add_argument("--" + k, required=True)
    ap.add_argument("--no-defence", action="append", default=[])
    a = ap.parse_args()
    servers = [s for s in a.servers.split(",") if s]
    first = {k: v for k, v in cmpc.read(a.first).items() if k[0] in servers}
    second = {k: v for k, v in cmpc.read(a.second, valid_only=True).items() if k[0] in servers}
    decisions = {(r["server"].strip(), r["tool"].strip()): norm_decision(r)
                 for r in csv.DictReader(open(a.adjudication, newline="")) if r["server"].strip() in servers}
    rows = final_rows(first, second, decisions, set(servers))
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "final-census.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["server", "tool", "class", "protection", "vendor_only", "source"])
        w.writeheader()
        w.writerows(rows)
    cov_set = [s for s in servers if s not in a.no_defence]
    res = {"inputs_sha256": {"first": sha(a.first), "second": sha(a.second), "adjudication": sha(a.adjudication)},
           "servers": servers, "no_defence_D23": a.no_defence,
           "agreement_before_adjudication": {k: v for k, v in cmpc.compare(first, second).items()
                                             if k in ("n_joined", "class", "protection", "vendor_only")},
           "adjudicated": sum(r["source"] == "adjudicated" for r in rows),
           "all_A": coverage(rows, cov_set), "without_vendor_only": coverage(rows, cov_set, exclude_vendor_only=True)}
    (out / "coverage.json").write_text(json.dumps(res, indent=1))
    pct = lambda x: f"{100 * x:.1f}%"
    md = ["# RQ4 coverage (generated by final_census.py)", "", f"Servers: {', '.join(cov_set)}. Unit: registered tool name.", ""]
    for label, key in [("All tools returning third-party prose", "all_A"), ("Without vendor-only prose (D17 point 4)", "without_vendor_only")]:
        c = res[key]
        md += [f"## {label}", "", "| Server | Tools | Full | Partial | None | Covered, full only | Covered, full + partial |", "|---|---|---|---|---|---|---|"]
        md += [f"| {s} | {v['A']} | {v['full']} | {v['partial']} | {v['none']} | {pct(v['cov_full'])} | {pct(v['cov_any'])} |"
               for s, v in c["per_server"].items()]
        m = c["summary"]
        if m["servers"]:
            md += ["", f"Mean over servers {pct(m['mean_full'])} / {pct(m['mean_any'])}; median {pct(m['median_full'])} / "
                   f"{pct(m['median_any'])}; pooled {m['pooled_full'][0]}/{m['pooled_full'][1]} / {m['pooled_any'][0]}/{m['pooled_any'][1]}.", ""]
    ag = res["agreement_before_adjudication"]
    md += [f"Agreement between the readings before adjudication, on these servers (n = {ag['n_joined']}): class κ = "
           f"{ag['class']['kappa']}, protection κ = {ag['protection']['kappa']}. Adjudicated tools: {res['adjudicated']}.", ""]
    (out / "COVERAGE.md").write_text("\n".join(md))
    print("\n".join(md))


if __name__ == "__main__":
    main()
