#!/usr/bin/env python3
"""RQ1 frame, step 3: rq1-frame.csv (schema of D44 point 1) from the screening decisions, the grouping into disclosures (D41
point 1), the eligibility check of every included case (D44 point 5, eligibility-ledger.csv), the timeline events and the pilot
exclusions. Mechanical: every judgement is in the input files and FRAME-NOTES.md.

    python3 preregistration/rq1/build_frame.py
"""
import csv, json, pathlib

HERE = pathlib.Path(__file__).resolve().parent
WINDOW = ("2026-06-26", "2026-09-24")
COLUMNS = ["case_id", "records", "date", "product", "product_type", "source", "primary_source", "decision", "reason", "note"]
PRECEDENCE = ["agent client", "MCP server or connector", "SDK"]  # D41 point 3
TIMELINE_RECORDS = {"CVE-2026-76404"}  # Splunk SVD-2026-0808, the one timeline event outside the pilot (timeline-events.csv)
# Disclosure dates that precede the records' own dates (FRAME-NOTES.md): the write-up is the disclosure.
WRITEUP_DATES = {"CVE-2026-30623": ("2026-04-15", "E6", "OX Security MCP supply-chain write-up of 15 Apr 2026, before the window")}
# Follow-ups (incomplete fix, bypass) join the disclosure they continue (D41 point 1); these continue disclosures published
# before the window (NVD publication date of the parent), so the case is dated by the parent and excluded (E6).
for _rec, _par, _date in (("CVE-2026-69263", "CVE-2025-8943", "2025-08-14"), ("CVE-2026-53509", "CVE-2026-33060", "2026-03-20"),
                          ("CVE-2026-77262", "CVE-2026-27825", "2026-03-10"), ("CVE-2026-77249", "CVE-2026-27826", "2026-03-10"),
                          ("CVE-2026-47394", "CVE-2026-44336", "2026-05-08"), ("CVE-2026-46678", "CVE-2026-25580", "2026-02-06"),
                          ("CVE-2026-69257", "CVE-2026-31829", "2026-03-10"), ("CVE-2026-75858", "CVE-2026-45311", "2026-05-28"),
                          ("CVE-2026-59973", "CVE-2026-39885", "2026-04-08"),
                          ("GHSA-8q49-2h5h-434x", "GHSA-65h7-9wrw-629c", "2026-06-22")):  # found by the eligibility check
    WRITEUP_DATES[_rec] = (_date, "E6", f"follow-up of {_par} (published {_date}), a disclosure before the window (D41 point 1)")


def main():
    cand = {c["id"]: c for c in json.loads((HERE / "candidates-20261025.json").read_text())}
    scr = {r["id"]: r for r in csv.DictReader(open(HERE / "screening-20261025.csv", newline=""))}
    for o in csv.DictReader(open(HERE / "screening-overrides.csv", newline="")):  # corrections after review, with their source
        scr[o["id"]].update(decision=o["decision"], reason=o["reason"], product_type=o["product_type"],
                            note=f"{o['note']} [override: {o['source']}]")
    first = {r["record"]: r for r in csv.DictReader(open(HERE / "disclosure-dates.csv", newline=""))}
    groups = json.loads((HERE / "grouping-20261025.json").read_text())
    grouped = {r for g in groups for r in g["records"]}
    groups += [{"records": [r], "rule": "single", "note": ""} for r, x in sorted(scr.items())
               if x["decision"] == "include" and not x["pilot"] and r not in grouped]
    ledger = {r["records"].split(";")[0]: r for r in csv.DictReader(open(HERE / "eligibility-ledger.csv", newline=""))}
    rows, seen, mismatch = [], set(), []
    for g in groups:
        recs = g["records"]; seen.update(recs)
        sr = [scr[r] for r in recs]
        assert all(s["decision"] == "include" and not s["pilot"] for s in sr), recs
        ids = []
        for r in recs:
            ids += [r] + [x for x in scr[r]["ghsa"].split(";") if x and x != r]
        date = min(first[r]["first_disclosure"] for r in recs)  # D14 point 2: first public advisory or write-up
        date_src = min((first[r]["first_disclosure"], first[r]["source_url"]) for r in recs)[1]
        decision, reason = "include", ("I?" if any(s["reason"] == "I?" for s in sr) else "I")
        note = g["note"] if len(recs) > 1 else sr[0]["note"]
        for r in recs:
            if r in WRITEUP_DATES:
                date, reason, why = WRITEUP_DATES[r]; decision = "exclude"; note = why
        if decision == "include" and not WINDOW[0] <= date <= WINDOW[1]:
            decision, reason = "exclude", "E6"
            note = f"first public disclosure {date} ({date_src}), outside the window"
        led = ledger.get(recs[0])
        followup = any(r in WRITEUP_DATES for r in recs)
        if not followup:
            assert led, f"no eligibility check for {recs[0]} (D44 point 5)"
            if led["failed"] in ("i", "ii", "pilot"):
                decision, reason = "exclude", f"E-{led['failed']}"
                note = f"eligibility check (D44 point 5): fails ({led['failed']}); {led['note']}"
            elif (led["failed"] == "iii") != (decision == "exclude"):
                mismatch.append((recs[0], date, led["eligible"], led["note"][:80]))
        ptype = next(t for t in PRECEDENCE if any(s["product_type"] == t for s in sr))
        c0 = cand[recs[0]]
        src = next((u for u in c0["refs"] if "/security/advisories/" in u or "github.com/advisories/" in u), None) \
            or f"https://nvd.nist.gov/vuln/detail/{recs[0]}"
        if decision == "include":
            src = date_src
        rows.append({"records": ";".join(dict.fromkeys(ids)), "date": date,
                     "product": "; ".join(dict.fromkeys(s["product"] for s in sr)),
                     "product_type": ptype if decision == "include" else "n/a",
                     "source": ("timeline" if set(recs) & TIMELINE_RECORDS else "query only") if decision == "include" else "",
                     "primary_source": src, "decision": decision, "reason": reason, "note": note})
    for r, s in scr.items():
        if r in seen:
            continue
        assert s["decision"] == "exclude" or s["pilot"], r
        rows.append({"records": ";".join([r] + [x for x in s["ghsa"].split(";") if x and x != r]), "date": s["published"],
                     "product": s["product"], "product_type": "n/a", "source": "", "primary_source":
                     f"https://nvd.nist.gov/vuln/detail/{r}" if r.startswith("CVE") else f"https://github.com/advisories/{r}",
                     "decision": "exclude", "reason": f"pilot {s['pilot']}" if s["pilot"] else s["reason"],
                     "note": "component or alias of a pilot case (D3)" if s["pilot"] else s["note"]})
    for t in csv.DictReader(open(HERE / "timeline-events.csv", newline="")):
        if t["decision"] == "include":
            continue  # its record is a query case (TIMELINE_RECORDS)
        rows.append({"records": t["maps_to"], "date": t["date"], "product": t["event"], "product_type": "n/a", "source": "",
                     "primary_source": f"timeline:{t['timeline']}", "decision": "exclude",
                     "reason": t["final_reason"], "note": t["final_note"]})
    rows.sort(key=lambda r: (r["decision"] != "include", r["date"], r["records"]))
    for i, r in enumerate(rows, 1):
        r["case_id"] = f"RQ1-{i:04d}"
    with open(HERE / "rq1-frame.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNS, lineterminator="\n"); w.writeheader(); w.writerows(rows)
    inc = [r for r in rows if r["decision"] == "include"]
    with open(HERE / "date-vs-ledger.csv", "w", newline="") as f:  # the date table decides (iii); the ledger is the cross-check
        w = csv.writer(f, lineterminator="\n"); w.writerow(["first_record", "first_disclosure", "ledger_eligible", "ledger_note"])
        w.writerows(mismatch)
    print(len(rows), "rows;", len(inc), "included cases;", {t: sum(r["product_type"] == t for r in inc) for t in PRECEDENCE},
          "timeline", sum(r["source"] == "timeline" for r in inc), "flagged", sum(r["reason"] == "I?" for r in inc),
          "date/ledger disagreements", len(mismatch))


if __name__ == "__main__":
    main()
