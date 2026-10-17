#!/usr/bin/env python3
"""Agreement between the first reading of the RQ4 census (frozen canonical table, D22) and Codex's second reading.

Joins by server and registered tool name; reports tools missing or duplicated on either side; computes Cohen's kappa and raw
agreement on class (A/B), on protection (full/partial/none/n-a) and on the vendor-only flag, using the second reading's labels as
they are (no correction from the first reading is applied to them). Lists every disagreement on a tool that either reading puts
in class A, for the author's adjudication against the source. Only rows from valid sessions are used.

  python3 compare_census.py FIRST_CANONICAL.csv SECOND_READING.csv --out OUT.json
"""
import argparse, collections, csv, importlib.util, json
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("agreement_q3", HERE.parents[1] / "tool-change/scripts/agreement_q3.py")
agr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(agr)


def read(path, valid_only=False):
    rows = [r for r in csv.DictReader(open(path, newline=""))]
    if valid_only:
        rows = [r for r in rows if r.get("valid", "True") in ("True", "true", True)]
    keyed = collections.defaultdict(list)
    for r in rows:
        keyed[(r["server"].strip(), r["tool"].strip())].append(r)
    return keyed


def flag(r, field):
    v = (r.get(field) or "").strip().lower()
    return "true" if v in ("true", "1", "yes") else "false"


def compare(first, second):
    dup1 = sorted(k for k, v in first.items() if len(v) > 1)
    dup2 = sorted(k for k, v in second.items() if len(v) > 1)
    only1 = sorted(set(first) - set(second))
    only2 = sorted(set(second) - set(first))
    common = sorted((set(first) & set(second)) - set(dup1) - set(dup2))
    out = {"n_first": len(first), "n_second": len(second), "n_joined": len(common),
           "missing_in_second": [list(k) for k in only1], "missing_in_first": [list(k) for k in only2],
           "duplicates_first": [list(k) for k in dup1], "duplicates_second": [list(k) for k in dup2]}
    for name, get1, get2 in [("class", lambda r: r["class"], lambda r: r["class"]),
                             ("protection", lambda r: r["protection"], lambda r: r["protection"]),
                             ("vendor_only", lambda r: flag(r, "contested"), lambda r: flag(r, "vendor_only"))]:
        a = [get1(first[k][0]).strip() for k in common]
        b = [get2(second[k][0]).strip() for k in common]
        agree = sum(x == y for x, y in zip(a, b))
        out[name] = {"kappa": agr.kappa(a, b), "raw_agreement": (agree / len(common)) if common else None, "n": len(common)}
    out["to_adjudicate"] = [
        {"server": k[0], "tool": k[1],
         "first": {"class": first[k][0]["class"], "protection": first[k][0]["protection"]},
         "second": {"class": second[k][0]["class"], "protection": second[k][0]["protection"],
                    "evidence": second[k][0].get("evidence", "")}}
        for k in common
        if "A" in (first[k][0]["class"], second[k][0]["class"])
        and (first[k][0]["class"], first[k][0]["protection"]) != (second[k][0]["class"], second[k][0]["protection"])]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("first")
    ap.add_argument("second")
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    res = compare(read(a.first), read(a.second, valid_only=True))
    Path(a.out).write_text(json.dumps(res, indent=2))
    print(json.dumps({k: res[k] for k in ("n_first", "n_second", "n_joined", "class", "protection", "vendor_only")}, indent=1))
    print("to adjudicate:", len(res["to_adjudicate"]))


if __name__ == "__main__":
    main()
