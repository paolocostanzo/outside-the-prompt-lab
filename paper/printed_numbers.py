#!/usr/bin/env python3
"""Write PAPER-NUMBERS.csv: every value of paper/results/numbers.json in the
forms the paper prints it, so a reader (or a text search) can find a printed
number without re-deriving the rounding.

Shares in numbers.json are fractions (0.92574 is printed as 92.6%); kappas and
other coefficients are printed to two or three decimals. This script only reads
numbers.json; it does not change it.

Usage: python3 paper/printed_numbers.py
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "paper" / "results" / "numbers.json"
OUT = ROOT / "PAPER-NUMBERS.csv"


def leaves(node, prefix=""):
    if isinstance(node, dict):
        for key, value in node.items():
            if key == "provenance" and not prefix:
                continue
            yield from leaves(value, f"{prefix}.{key}" if prefix else key)
    elif isinstance(node, list):
        for i, value in enumerate(node):
            yield from leaves(value, f"{prefix}[{i}]")
    elif isinstance(node, (int, float)) and not isinstance(node, bool):
        yield prefix, node


def main() -> None:
    data = json.loads(SRC.read_text(encoding="utf-8"))
    rows = []
    for key, value in leaves(data):
        if isinstance(value, int):
            rows.append([key, value, "", "", "", value])
            continue
        percent = f"{value * 100:.1f}" if -1.0 <= value <= 1.0 else ""
        rows.append([key, repr(value), percent, f"{value:.3f}", f"{value:.2f}", f"{value:.1f}"])
    with OUT.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle, lineterminator="\n")
        writer.writerow(["numbers_json_key", "stored", "percent_1dp", "value_3dp", "value_2dp", "value_1dp"])
        writer.writerows(rows)
    print(f"{OUT.name}: {len(rows)} values from {SRC.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
