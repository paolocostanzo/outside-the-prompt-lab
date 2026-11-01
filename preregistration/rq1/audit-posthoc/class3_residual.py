#!/usr/bin/env python3
"""Post hoc, exploratory: per-case map of the 58 class-3 labels that reach
class 3 only through the decision rule ("none of the three").

Pure file reading, stdlib only. Run with:  python3 -I class3_residual.py [--draft OUT]

Step 1 (automatic): for each of the 58 cases collect r0, scope (from the audit
CSV), mechanism (from the audit CSV), CWE ids (saved advisory copy -> saved CVE
record -> saved NVD copy -> raw NVD/GHSA dumps -> "not found") and the evidence
file (folder RQ1-xxxx + basename + SHA-256; the local path is not recorded).

Step 2 (manual, written by an AI coder after all results, no second rater):
the per-case violated property, paraphrase and coverage judgement live in
ANNOT below. They were written by reading each case's own saved source.
The script merges both steps into rq1-class3-residual-map.csv.

--draft OUT writes the step-1 draft plus the source description text to OUT
(for reading only; OUT must be outside the repository: it holds names).
No label, data file or confirmatory script is modified.
"""
import csv
import gzip
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
RQ1 = os.path.dirname(HERE)
SOURCES = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(RQ1))),
                       "reports", "a2-riassunti", "sources")
CASES = os.path.join(HERE, "rq1-audit-cases.csv")
OUT = os.path.join(HERE, "rq1-class3-residual-map.csv")
RAW = os.path.join(RQ1, "raw-20261025")

COLS = ["case_id", "r0", "scope", "mechanism", "cwe_ids", "violated_property",
        "evidence_paraphrase", "evidence_ref", "class3_wording_covers",
        "competing_literal_class", "label_kept"]


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 16), b""):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (ValueError, OSError, UnicodeDecodeError):
        return None


def scope_of(product_type):
    return "agent_client" if product_type == "agent client" else "service_around_agent"


def raw_cwe_index():
    """CVE/GHSA id -> CWE ids from the raw dumps (fallback only)."""
    idx = {}
    for name in sorted(os.listdir(RAW)):
        p = os.path.join(RAW, name)
        data = None
        if name.endswith(".json.gz"):
            with gzip.open(p, "rt", encoding="utf-8") as f:
                data = json.load(f)
        elif name.endswith(".json"):
            data = load_json(p)
        if not isinstance(data, list):
            continue
        for it in data:
            if not isinstance(it, dict):
                continue
            if "cve" in it:  # NVD 2.0 item
                c = it["cve"]
                ids = [d.get("value") for w in c.get("weaknesses", [])
                       for d in w.get("description", [])
                       if str(d.get("value", "")).startswith("CWE-")]
                if ids:
                    idx.setdefault(c.get("id"), set()).update(ids)
            elif "ghsa_id" in it:
                ids = [w.get("cwe_id") for w in it.get("cwes") or [] if w.get("cwe_id")]
                if ids:
                    for k in (it.get("ghsa_id"), it.get("cve_id")):
                        if k:
                            idx.setdefault(k, set()).update(ids)
    return idx


def case_sources(cid):
    """Return list of (basename, url, parsed-json-or-None) for a case folder."""
    folder = os.path.join(SOURCES, cid)
    index = load_json(os.path.join(folder, "index.json")) or {}
    out = []
    for url, base in index.items():
        p = os.path.join(folder, base)
        out.append((base, url, load_json(p) if base.endswith(".json") else None))
    return folder, out


def cwes_and_evidence(cid, rawidx):
    folder, srcs = case_sources(cid)
    ghsa = [(b, u, d) for b, u, d in srcs if isinstance(d, dict) and "ghsa_id" in d]
    cverec = [(b, u, d) for b, u, d in srcs if isinstance(d, dict) and "cveMetadata" in d]
    nvd = [(b, u, d) for b, u, d in srcs if isinstance(d, dict) and "vulnerabilities" in d]
    cwes, ids = [], set()
    for b, u, d in ghsa:
        cwes += [w.get("cwe_id") for w in d.get("cwes") or [] if w.get("cwe_id")]
        ids.update(x for x in (d.get("ghsa_id"), d.get("cve_id")) if x)
    if not cwes:
        for b, u, d in cverec:
            for pt in d.get("containers", {}).get("cna", {}).get("problemTypes", []):
                cwes += [x.get("cweId") for x in pt.get("descriptions", []) if x.get("cweId")]
            ids.add(d.get("cveMetadata", {}).get("cveId"))
    if not cwes:
        for b, u, d in nvd:
            for v in d.get("vulnerabilities", []):
                c = v.get("cve", {})
                ids.add(c.get("id"))
                for w in c.get("weaknesses", []):
                    cwes += [x.get("value") for x in w.get("description", [])
                             if str(x.get("value", "")).startswith("CWE-")]
    if not cwes:
        for k in ids:
            cwes += sorted(rawidx.get(k, ()))
    cwes = sorted(set(c for c in cwes if c and c.startswith("CWE-")))
    ev = (ghsa or cverec or nvd or srcs)
    base = ev[0][0] if ev else None
    if base is None:
        return (";".join(cwes) or "not found"), "not found", None, srcs, folder
    digest = sha256(os.path.join(folder, base))
    return (";".join(cwes) or "not found"), base, digest, srcs, folder


def description_text(srcs, folder):
    parts = []
    for b, u, d in srcs:
        if isinstance(d, dict) and "ghsa_id" in d:
            parts.append(f"[{b} advisory] {d.get('summary','')}\n{d.get('description','')}")
        elif isinstance(d, dict) and "cveMetadata" in d:
            for x in d.get("containers", {}).get("cna", {}).get("descriptions", []):
                parts.append(f"[{b} cve] {x.get('value','')}")
        elif isinstance(d, dict) and "vulnerabilities" in d:
            for v in d["vulnerabilities"]:
                for x in v.get("cve", {}).get("descriptions", []):
                    if x.get("lang") == "en":
                        parts.append(f"[{b} nvd] {x.get('value','')}")
    return "\n".join(parts)


# ---- Step 2: manual per-case annotations (AI coder, post hoc, single rater) ----
# case_id -> (violated_property, evidence_paraphrase, class3_wording_covers,
#             competing_literal_class)
ANNOT = {
    "RQ1-0001": ("validation of attachment URLs against internal or private address ranges",
                 "Attachment URLs are not checked against private ranges, letting a caller make the server fetch internal services.", "no", ""),
    "RQ1-0004": ("synchronisation of shared state while parsing protocol messages",
                 "A message-parsing function in the response handler is improperly synchronised; remote, high-complexity exploitation.", "no", ""),
    "RQ1-0006": ("confinement of outbound requests to the operator-configured path scope",
                 "Dot segments in path parameters escape the configured path, reaching restricted endpoints with forwarded credentials.", "arguable_authorisation", ""),
    "RQ1-0014": ("release of per-session server memory when request validation fails",
                 "A session is allocated before body validation and never freed on failure; repeated requests exhaust memory.", "no", ""),
    "RQ1-0016": ("confinement of run-directory access to the runs base directory",
                 "A caller-supplied run identifier is joined to the base directory unvalidated, allowing out-of-directory reads and overwrites.", "no", ""),
    "RQ1-0027": ("rejection of traversal or absolute paths in generated manifest file references",
                 "An untrusted API description can place an out-of-package file path verbatim into the generated plugin manifest.", "no", ""),
    "RQ1-0034": ("neutralisation of a caller-supplied table name used as an SQL identifier",
                 "An authenticated user's table name is interpolated into SQL, allowing arbitrary queries on the metrics database.", "no", ""),
    "RQ1-0039": ("confinement of file writes to the configured sandbox directory",
                 "The write check uses a caller-chosen base directory, so downloaded bytes land at any writable path.", "no", ""),
    "RQ1-0066": ("confinement of a manifest path argument to the intended location",
                 "Manipulating the package manifest path argument of a dependency-scan tool leads to path traversal; local attack.", "no", ""),
    "RQ1-0067": ("effectiveness of the path validator for project and schematic paths",
                 "Manipulating project or schematic path arguments defeats the path-validation protection mechanism; local attack.", "no", ""),
    "RQ1-0074": ("confinement of a root path argument to the intended directory",
                 "Manipulating the root path argument of a component-generator tool leads to path traversal; local attack.", "no", ""),
    "RQ1-0096": ("validation of server configuration files before they are executed",
                 "Incomplete validation of tool-server configuration files could allow remote code execution.", "no", "1"),
    "RQ1-0109": ("confinement of file search to the configured base directory",
                 "A crafted search pattern escapes the base directory and returns names and contents of other files.", "no", ""),
    "RQ1-0122": ("restriction of authenticated requests to the intended destination host",
                 "An unvalidated page URL makes the tool send its bearer token to any host, including an attacker listener.", "no", ""),
    "RQ1-0124": ("network isolation of server containers and authentication on local management endpoints",
                 "Containers reach host-local services by default while management and proxy endpoints accept unauthenticated calls.", "arguable_authorisation", ""),
    "RQ1-0130": ("blocking of disallowed code and fetches before code runs in an unsandboxed interpreter",
                 "Obfuscated code passes a blocklist validator and runs unsandboxed; unblocked functions also allow internal requests.", "no", "1"),
    "RQ1-0131": ("validation of command, arguments and environment before starting a local tool server",
                 "Authenticated users bypass validation via environment variables and arguments, running commands when a local server starts.", "no", "1"),
    "RQ1-0144": ("confinement of schema module paths derived from node type strings",
                 "A member-level user's node type string with traversal sequences loads attacker files, executing code in the main process.", "no", "1"),
    "RQ1-0148": ("neutralisation of host and username arguments before command execution",
                 "Host or username arguments lead to command injection; the maintainer disputes this given the intended threat model.", "no", ""),
    "RQ1-0155": ("neutralisation of arguments passed to a version-control command",
                 "Manipulating the args parameter of a diff-review endpoint leads to command injection.", "no", ""),
    "RQ1-0156": ("neutralisation of a date argument before it reaches a command",
                 "Manipulating a date-range argument of a usage endpoint leads to remotely triggerable command injection.", "no", ""),
    "RQ1-0157": ("confinement of record identifiers and filenames to the storage directory",
                 "Manipulating identifier or filename arguments of storage functions leads to path traversal; local attack.", "no", ""),
    "RQ1-0159": ("neutralisation of an output directory argument before command execution",
                 "Manipulating the output directory argument of a chart-generation tool leads to command injection; local access.", "no", ""),
    "RQ1-0168": ("confinement of a workspace path argument to the intended workspace",
                 "Manipulating the workspace path argument of install and update functions leads to path traversal; local attack.", "no", ""),
    "RQ1-0174": ("neutralisation of name, file and location arguments before command execution",
                 "Manipulating several tool arguments leads to command injection; the attack is local.", "no", ""),
    "RQ1-0176": ("restriction of destinations fetched by a webpage-reading tool",
                 "Manipulating the url argument of a page-reading tool leads to server-side request forgery; local execution.", "no", ""),
    "RQ1-0177": ("confinement of folder and name arguments to the output directory",
                 "Manipulating folder or name arguments of a diagram generator leads to path traversal; local attack.", "no", ""),
    "RQ1-0178": ("restriction of destinations reached through a resource URI parameter",
                 "Manipulating the resource request URI leads to server-side request forgery, launchable remotely.", "no", ""),
    "RQ1-0180": ("confinement of file path arguments to permitted locations",
                 "Manipulating file path arguments of several analysis tools leads to path traversal; local attack.", "no", ""),
    "RQ1-0182": ("confinement of session path arguments used in file reads and writes",
                 "Manipulating session command or path arguments in file operations leads to path traversal; local access.", "no", ""),
    "RQ1-0184": ("confinement of an upload file argument to permitted locations",
                 "Manipulating the file argument of a document-upload tool's file read leads to path traversal; local attack.", "no", ""),
    "RQ1-0185": ("restriction of the configured backend URL to intended destinations",
                 "Manipulating the backend URL in the configuration schema leads to server-side request forgery from the local host.", "no", ""),
    "RQ1-0186": ("restriction of destinations requested by a proxy endpoint",
                 "Manipulating the url argument of a proxy endpoint leads to remotely triggerable server-side request forgery.", "no", ""),
    "RQ1-0187": ("restriction of destinations fetched by an article-fetching tool",
                 "Manipulating the url argument of an article-fetch function leads to server-side request forgery from remote.", "no", ""),
    "RQ1-0196": ("restriction of destinations fetched when loading an API specification",
                 "A manipulation in the specification-loading function leads to remotely triggerable server-side request forgery.", "no", ""),
    "RQ1-0198": ("bounded buffering of a streamed server response in the client",
                 "The client appends stream chunks without limit until a delimiter arrives; a malicious server exhausts its memory.", "no", ""),
    "RQ1-0208": ("URL validation blocking cloud metadata and internal destinations",
                 "A manipulation in the URL validation of fetch tools leads to remotely launchable server-side request forgery.", "no", ""),
    "RQ1-0218": ("not stated in the source",
                 "Server-side request forgery lets an authorised attacker disclose information over a network; no mechanism given.", "no", ""),
    "RQ1-0222": ("egress filtering of user-registered server URLs and the privilege check on server creation",
                 "Non-admin users register arbitrary-URL servers, since the admin check covers only command servers; no egress filtering.", "arguable_authorisation", ""),
    "RQ1-0227": ("mediation of attribute access in the restricted code-execution sandbox",
                 "An exposed attribute builtin and literal-string validation let submitted code escape the sandbox and run commands.", "no", ""),
    "RQ1-0250": ("confinement of a path argument in a context-reading function",
                 "Manipulating the path argument of a context-reading function leads to remotely initiable path traversal.", "no", ""),
    "RQ1-0251": ("confinement of note-handling file operations to the intended folder",
                 "A manipulation of note ingest, sync and folder functions leads to remotely launchable path traversal.", "no", ""),
    "RQ1-0255": ("confinement of import and export file paths",
                 "Manipulating the file path argument of session import and export leads to remotely launchable path traversal.", "no", ""),
    "RQ1-0258": ("confinement of an image path argument used for file reads",
                 "Manipulating the image path argument of an upload tool's file read leads to path traversal.", "no", ""),
    "RQ1-0279": ("authentication of the agent-registration endpoint and validation of executed binary and arguments",
                 "Anonymous requests count as authenticated when login is off; attacker binary and version command are then executed.", "arguable_authorisation", "1"),
    "RQ1-0283": ("bounding of per-request size and cost in the shared agent worker pool",
                 "An authenticated user's large or costly requests hold agent workers for minutes, exhausting the pool for others.", "no", ""),
    "RQ1-0285": ("directory containment of a parse tool's file path argument",
                 "An unconstrained file path argument lets absolute or traversal paths read sensitive files returned to the model.", "no", ""),
    "RQ1-0288": ("neutralisation of data-model names inserted into a code-generation template",
                 "Crafted table, index or attribute names in a data model file execute code on the host deploying generated code.", "no", ""),
    "RQ1-0292": ("enforcement of the read-only scope by the statement validator",
                 "An incomplete deny-list lets crafted SQL in submitted content modify data beyond the read-only scope.", "arguable_authorisation", ""),
    "RQ1-0299": ("confinement of a code-search path argument to the project root",
                 "The search handler skips the project-boundary check, reading source files anywhere; available under every permission preset.", "arguable_authorisation", ""),
    "RQ1-0307": ("recursive inspection of nested payload content by protection mechanisms",
                 "An authenticated user can bypass protection mechanisms because nested payload content is not inspected recursively.", "no", ""),
    "RQ1-0311": ("not stated in the source",
                 "Command injection lets an unauthorised attacker disclose information over a network; no mechanism described.", "no", ""),
    "RQ1-0312": ("not stated in the source",
                 "Command injection in an assistant feature lets an unauthorised attacker disclose information; no mechanism described.", "no", ""),
    "RQ1-0313": ("not stated in the source",
                 "Command injection lets an authorised attacker elevate privileges over a network; no mechanism described.", "no", ""),
    "RQ1-0316": ("neutralisation of a URL argument passed to a shell command",
                 "Manipulating the url argument of a re-authentication tool reaches a shell call, giving remote command injection.", "no", ""),
    "RQ1-0317": ("confinement of a filename argument in a data-analysis tool",
                 "Manipulating the filename argument of a data-analysis tool leads to remotely exploitable path traversal.", "no", ""),
    "RQ1-0321": ("restriction of destinations reached through a document path argument",
                 "Manipulating the document path argument of a document tool leads to remotely initiable server-side request forgery.", "no", ""),
    "RQ1-0328": ("boundary-correct confinement of log downloads to the log folder",
                 "A string-prefix check lets an authenticated admin read log-type files in sibling directories outside the folder.", "no", ""),
}


def main():
    draft = None
    if len(sys.argv) == 3 and sys.argv[1] == "--draft":
        draft = sys.argv[2]
        if os.path.abspath(draft).startswith(os.path.dirname(os.path.dirname(RQ1))):
            sys.exit("draft output must be outside the repository")
    with open(CASES, encoding="utf-8", newline="") as f:
        cases = [r for r in csv.DictReader(f)
                 if r["r0"] == "3" and r["a_class3_clause"].startswith("none of the three")]
    if len(cases) != 58:
        sys.exit(f"expected 58 cases, found {len(cases)}")
    rawidx = raw_cwe_index()
    rows, dumps = [], []
    for r in cases:
        cid = r["case_id"]
        cwes, base, digest, srcs, folder = cwes_and_evidence(cid, rawidx)
        ref = f"{cid}/{base} sha256:{digest[:12]}" if digest else "not found"
        a = ANNOT.get(cid)
        rows.append({
            "case_id": cid, "r0": r["r0"], "scope": scope_of(r["product_type"]),
            "mechanism": r["mechanism"], "cwe_ids": cwes,
            "violated_property": a[0] if a else "",
            "evidence_paraphrase": a[1] if a else "",
            "evidence_ref": ref,
            "class3_wording_covers": a[2] if a else "",
            "competing_literal_class": a[3] if a else "",
            "label_kept": "yes",
        })
        if draft:
            dumps.append(f"=== {cid} | {r['product_type']} | {r['mechanism']} | {cwes} | {ref}\n"
                         f"{description_text(srcs, folder)[:2500]}\n")
    if draft:
        with open(draft, "w", encoding="utf-8") as f:
            f.write("\n".join(dumps))
        print(f"draft: {len(dumps)} cases -> {draft}")
        return
    missing = [r["case_id"] for r in rows if not r["violated_property"]]
    if missing:
        sys.exit(f"missing annotations: {missing}")
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLS, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    n = len(rows)
    arg = sum(r["class3_wording_covers"] == "arguable_authorisation" for r in rows)
    c1 = sum(r["competing_literal_class"] == "1" for r in rows)
    c1a = sum(r["competing_literal_class"] == "1" and r["scope"] == "agent_client" for r in rows)
    ns = sum(r["violated_property"] == "not stated in the source" for r in rows)
    nf = sum(r["cwe_ids"] == "not found" for r in rows)
    print(f"rows={n} arguable_authorisation={arg} competing_class1={c1} "
          f"(agent_client={c1a}) not_stated={ns} cwe_not_found={nf} -> {OUT}")


if __name__ == "__main__":
    main()
