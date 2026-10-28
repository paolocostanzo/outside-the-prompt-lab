#!/usr/bin/env python3
"""RQ1, EXPLORATORY (D51): the labelling sheet for a second, independent human rater (H2). Same page, criteria, summaries,
sources and D45 question as the author's sheet (r0_sheet.py), so the two humans are labelled alike; only what identifies the
rater changes: case order SHA-256(seed + ":h2:" + case id), browser storage key, export file names (rq1-h2.json) and the
declaration. The page shows no class from R0 or the models.

    python3 preregistration/rq1/h2_sheet.py OUT.html      # also writes OUT-calibration.md (the pilot examples R0 saw)

Before sending it, the rater must not have seen rq1-r0.json, the model outputs, the results or the manuscript.
"""
import json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import r0_sheet  # noqa: E402

SWAPS = [  # (text in the author's page, text in the H2 page); each must occur, so a change to r0_sheet.py stops this script
    ('<title>R0 sheet</title>', '<title>H2 sheet</title>'),
    ('const KEY = "rq1-r0-" +', 'const KEY = "rq1-h2-" +'),
    ('I labelled these cases myself, without AI assistance (D42 point 4).',
     'I labelled these cases myself, without AI assistance, and before labelling I had not seen any other rater\'s labels, '
     'the model outputs or the results.'),
    ('Esporta rq1-r0.json', 'Esporta rq1-h2.json'),
    ('a.download = "rq1-r0-progress.json"', 'a.download = "rq1-h2-progress.json"'),
    ('declaration: "labelled by the author without AI assistance (D42 point 4)"',
     'rater: "H2", declaration: "labelled by a second human rater without AI assistance, blind to all other labels (D51)"'),
    ('a.download = "rq1-r0.json"', 'a.download = "rq1-h2.json"'),
    ('sheet: "v3-guided"', 'sheet: "v3-guided-h2"'),
]


def build():
    """The author's page with the H2 order and identity."""
    page, _ = r0_sheet.build_page("h2")
    for old, new in SWAPS:
        if page.count(old) != 1:
            sys.exit(f"r0_sheet.py changed: {old!r} occurs {page.count(old)} times, expected once")
        page = page.replace(old, new)
    return page


PILOT = HERE.parent / "pilot"
NAMES = {1: "Before trust", 2: "Interaction layer", 3: "Plumbing", 4: "Authority"}


def calibration():
    """The ten pilot cases with their published labels, C01 corrected to 4 (D14); no sampled case appears. R0 saw the same
    cases and labels and, in addition, worked walkthroughs of them with the D47 questions (D50 point 1), which were not saved:
    H2 gets the labels and the same guided questions on the sheet, not those walkthroughs (D51)."""
    cases = json.loads((PILOT / "cases.json").read_text())
    labels = {**json.loads((PILOT / "human.json").read_text())["classes"], "C01": 4}
    out = ["# Calibrazione / Calibration — 10 casi del pilota (non fanno parte del campione)", "",
           "Leggi i dieci casi e la classe data a ciascuno, poi passa alla scheda. Sono gli stessi esempi visti dal primo "
           "valutatore, che li ha visti anche spiegati con le domande della scheda. / Read the ten cases and their class, then move "
           "to the sheet. The first rater saw the same cases and labels, also walked through with the sheet's questions.",
           ""]
    for c in cases:
        k = labels[c["id"]]
        out += [f"## {c['id']} — classe / class {k} ({NAMES[k]})", "", c["summary"], "", f"Fonte / source: {c['source']}", ""]
        if c["id"] == "C01":
            out += ["Nota: questo riassunto del pilota omette una condizione. L'advisory dice che lo sfruttamento richiedeva un "
                    "repository con contenuto di prompt injection eseguito con l'agente, quindi la classe corretta è 4 (D14). I "
                    "riassunti della scheda dichiarano tutte le condizioni. / Note: this pilot summary omits that exploitation "
                    "needed prompt-injection content run with the agent, hence class 4 (D14); the sheet's summaries state every "
                    "precondition.", ""]
    return "\n".join(out) + "\n"


def main(out):
    page = build()
    if "rq1-r0" in page:
        sys.exit("the H2 page still refers to the author's files")
    pathlib.Path(out).write_text(page)
    cal = pathlib.Path(out).with_name(pathlib.Path(out).stem + "-calibration.md")
    cal.write_text(calibration())
    print(f"H2 sheet -> {out}; calibration -> {cal}")


if __name__ == "__main__":
    main(sys.argv[1])
