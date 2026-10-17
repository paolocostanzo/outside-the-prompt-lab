#!/usr/bin/env python3
"""Second, independent reading of the RQ4 per-tool census by Codex CLI (deviation D22, point 2).

For each repository: clone it at the pinned commit on the host, check the commit, then run one fresh Codex session in the isolated
container of ../../tool-change/scripts/isolated_codex.py with the clone mounted read-only at /work/src. Codex gets the rules below
verbatim and returns one row per registered tool name. The first census is never mounted or quoted. A reading counts only if the
isolation probe and the initial-context check pass.

  python3 census_codex.py --config CONFIG.json --clones DIR --auth ~/.codex/auth.json --out OUT_DIR [--model gpt-6.1-sol --effort medium]

CONFIG.json: [{"repo": "owner/name", "url": "https://github.com/owner/name.git", "commit": "<sha>",
               "servers": [{"name": "<server>", "path": "<folder in the repo>"}]}]
"""
import argparse, csv, importlib.util, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
_spec = importlib.util.spec_from_file_location("isolated_codex", HERE.parents[1] / "tool-change/scripts/isolated_codex.py")
iso = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(iso)

RULES = """Census rules (deviation D17 points 2-4, and the operational definitions of D22 point 2), given verbatim:

- One row per registered tool name: every tool the server registers with its MCP SDK, including tools that are only registered
  under a flag or a toolset, with the file:line where it is registered.
- Class A: the tool returns free prose written by third parties (titles, descriptions, bodies, comments, messages, file contents,
  logs). Names and identifier-like strings (names of branches, repositories, projects, pipelines, teams, users, display names,
  tags or labels used as identifiers) do not make a tool class A. Otherwise the class is B.
- Vendor-only prose: the only prose the tool returns is written by the vendor itself (documentation, curated advisories). Such prose
  counts as qualifying prose for class and protection: the tool is class A and gets a protection label like any other, and
  vendor_only is true. A tool that returns both vendor and third-party prose is class A with vendor_only false.
- Protection, for class A tools, refers to the server's own output-side defence against untrusted content (for example a
  delimiter or boundary around untrusted data, character hygiene, or provenance marking applied to the tool result):
  full = all the qualifying prose the tool can return passes through the defence;
  partial = only part of it does, including when an error branch or a secondary branch returns qualifying prose outside the defence;
  none = none of it does.
  For class B tools, protection is n-a.
- Mechanism: name the defence function or wrapper and how it is applied (or "none").
- Evidence: file:line for the registration, for where the prose is returned, and for the defence call (or its absence).
"""

TASK = """You are reading open-source code for a research census. The repository is mounted read-only at /work/src at commit {commit}.
Census these servers only:
{servers}
Read the source with the shell tools available (read-only). Do not guess: every label needs file:line evidence from /work/src.

{rules}
Return the JSON object requested by the output schema: "rows", one object per registered tool of the listed servers."""

ROW = {"type": "object", "additionalProperties": False,
       "properties": {k: {"type": "string"} for k in ("server", "tool", "registered_at", "class", "class_reason", "protection",
                                                      "mechanism", "evidence")} | {"vendor_only": {"type": "boolean"}},
       "required": ["server", "tool", "registered_at", "class", "class_reason", "protection", "mechanism", "evidence", "vendor_only"]}
ROW["properties"]["class"] = {"type": "string", "enum": ["A", "B"]}
ROW["properties"]["protection"] = {"type": "string", "enum": ["full", "partial", "none", "n-a"]}
SCHEMA = {"type": "object", "additionalProperties": False, "properties": {"rows": {"type": "array", "items": ROW}},
          "required": ["rows"]}
FIELDS = ["repo", "commit", "server", "tool", "registered_at", "class", "class_reason", "protection", "mechanism", "vendor_only", "evidence"]


def clone_at(url, commit, dest: Path):
    if not dest.exists():
        subprocess.run(["git", "init", "-q", str(dest)], check=True)
        subprocess.run(["git", "-C", str(dest), "fetch", "-q", "--depth", "1", url, commit], check=True)
        subprocess.run(["git", "-C", str(dest), "-c", "advice.detachedHead=false", "checkout", "-q", "FETCH_HEAD"], check=True)
    head = subprocess.run(["git", "-C", str(dest), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    if head != commit:
        sys.exit(f"{dest}: HEAD {head} is not the pinned commit {commit}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", required=True)
    ap.add_argument("--clones", required=True)
    ap.add_argument("--auth", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--model", default="gpt-6.1-sol")
    ap.add_argument("--effort", default="medium")
    ap.add_argument("--timeout", type=int, default=3600)
    a = ap.parse_args()
    cfg = json.loads(Path(a.config).read_text())
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=False)
    rows, sessions = [], []
    for entry in cfg:
        src = Path(a.clones) / entry["repo"].replace("/", "__")
        clone_at(entry["url"], entry["commit"], src)
        servers = "\n".join(f"- {s['name']}: folder {s['path']}" for s in entry["servers"])
        prompt = TASK.format(commit=entry["commit"], servers=servers, rules=RULES)
        root = out / "sessions" / entry["repo"].replace("/", "__")
        rec = iso.run_session(prompt, root, Path(a.auth), a.model, a.effort, SCHEMA, ro_binds=((src, "/work/src"),),
                              timeout=a.timeout)
        ctx = (iso.check_context(root / rec["rollouts"][0], prompt) if rec.get("rollouts")
               else {"ok": False, "problems": ["no rollout"], "developer_tags": []})
        got = []
        try:
            got = json.loads(rec.get("reply") or "")["rows"]
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        valid = rec.get("status") == "completed" and rec["probe"]["ok"] and ctx["ok"] and bool(got)
        for r in got:
            rows.append({"repo": entry["repo"], "commit": entry["commit"], **r, "vendor_only": str(r.get("vendor_only")).lower(),
                         "valid": valid})
        sessions.append({"repo": entry["repo"], "commit": entry["commit"], "status": rec.get("status"), "probe": rec["probe"],
                         "context": ctx, "valid": valid, "n_rows": len(got), "rollouts": rec.get("rollouts", [])})
        print(entry["repo"], len(got), "rows", "valid" if valid else "INVALID", flush=True)
    with open(out / "second-reading.csv", "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=FIELDS + ["valid"], extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    (out / "second-reading.json").write_text(json.dumps({"model": a.model, "effort": a.effort, "rules": RULES, "schema": SCHEMA,
                                                         "sessions": sessions}, indent=2))


if __name__ == "__main__":
    main()
