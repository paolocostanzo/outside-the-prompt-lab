#!/usr/bin/env python3
"""Agreement of the two rule authors on H5 (D24): for every client/event pair, whether each author's rules tell the event apart
from the baseline, with the detections, and whether the two verdicts agree, on the author's pairs (the second author's extra
pairs are listed on stderr and not compared). Written on 28 Oct 2026 to regenerate the committed
evidence/scores-20261024/agreement.json, which had been produced without a committed script; output is byte-identical.

    python3 rules/agreement.py S/h5-author.json S/h5-second-author.json > S/agreement.json
"""
import json, sys


def agreement(author, second):
    if not set(author["pairs"]) <= set(second["pairs"]):
        sys.exit("the second author's H5 file lacks pairs of the author's")
    extra = sorted(set(second["pairs"]) - set(author["pairs"]))
    if extra:  # e.g. a pair split by the second author's rules; compared only on the author's pairs, as committed
        print(f"not compared (second author only): {', '.join(extra)}", file=sys.stderr)
    rows = [[k, a["tells_apart"], second["pairs"][k]["tells_apart"], a["detected"], second["pairs"][k]["detected"],
             a["tells_apart"] == second["pairs"][k]["tells_apart"]] for k, a in author["pairs"].items()]
    return {"pairs": rows, "agreement": f"{sum(r[5] for r in rows)}/{len(rows)}"}


if __name__ == "__main__":
    a, b = (json.load(open(p)) for p in sys.argv[1:3])
    sys.stdout.write(json.dumps(agreement(a, b), indent=1))  # no trailing newline, like score.py
