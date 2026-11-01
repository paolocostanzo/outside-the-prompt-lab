# RQ1 frame check on the 120 sampled cases (post hoc, 1 Nov 2026)

Exploratory side product of the source audit (see SOURCE-AUDIT.md). One AI coder (Claude), from the saved primary
sources only, checked against `../SCREENING-RULES.md`. These are **suspicions to be read by a human**, not decisions;
nothing in the frame or the sample was changed. No product, vendor or repository names here.

## 1. Possible duplicates / grouping errors among sampled cases

No pair of sampled cases was found to describe the same underlying flaw (same code path, same fix). Pairs that share a
product, a reporter template or a fix and are worth a second look:

| Cases | Why it looks related | Assessment |
|---|---|---|
| RQ1-0143, RQ1-0302 (and RQ1-0096) | Same product, three vendor bulletins; 0143 includes a record on "improper validation of the command field in MCP server configurations", 0302 one on "improper validation of command-line arguments in the MCP stdio server configuration"; 0096 a validator bypass on MCP configuration upload | Most plausible overlap in the sample: could be one flaw and its incomplete fix, or one root cause split across bulletins. Check fix commits. |
| RQ1-0241, RQ1-0244 | Same vendor, two repositories, identical root cause (shared HTTP server helper started without the host allow-list) and near-identical advisory text | Two products, two records: probably correct as two disclosures, but the same underlying defect in a shared helper. |
| RQ1-0088, RQ1-0089 | Same product, same fix commit and release, same reporter | Different tools and different flaws (symlink read vs environment leak): probably correct as two. |
| RQ1-0201, RQ1-0299 | Same product, path traversal in MCP tools, same advisory template | Different handlers and different fixed versions: probably correct as two. |
| RQ1-0144, RQ1-0145 | Same product, same fixed release | Different flaws (traversal in schema loader vs credential-reference check): correct as two. |
| RQ1-0311, RQ1-0312, RQ1-0313 | Same vendor, same release date, all one-line "command injection" records for related assistants | Not decidable from the sources (one-liners); cannot rule out one flaw in a shared component. |
| RQ1-0296, RQ1-0297 | Same product pair, same release date, one-liners | Different weakness types (command injection vs credential protection): probably two. |

Multi-record cases (grouped by bulletin or researcher write-up): RQ1-0127 (2 records), RQ1-0130 (2), RQ1-0143 (5),
RQ1-0215 (2), RQ1-0302 (3), RQ1-0327 (5). Within each, the records point the same way in the source audit, so the
grouping does not change the audit outcome. One to check against the grouping rule:

- **RQ1-0215** groups records for **two different products** of one vendor (an AI toolkit's agent run history and a
  separate MCP server app) that share only the bulletin. If grouping is meant to be per product/flaw, this is a grouping
  error (one case should be two, one of which may fall outside the sample).

Source-folder hygiene (no effect on the frame): RQ1-0185 holds a saved file belonging to another sampled product
(marked "different product, not used" in its index); RQ1-0309's researcher write-up also contains an unrelated finding;
RQ1-0283's bulletin lists third-party library CVEs besides the case record.

## 2. Possible ineligibility under SCREENING-RULES (ii) / E2–E4

| Case | Suspicion | Rule |
|---|---|---|
| RQ1-0005 | Flaw is in a workflow-checkpoint save/restore endpoint of an assistant plugin (object-key reuse), not obviously in its agent, tool or MCP component | E3? |
| RQ1-0027 | Product is a code generator that writes plugin manifests for an assistant; it is not itself an agent, connector called by an agent, or tool-calling SDK | E2/E3? |
| RQ1-0300 | Flaw is in the handling of a crafted link by a desktop agent application (URL handler); no tie to the agent's tool component in the record | E3? |
| RQ1-0025 | One-line record (open redirect) for a general assistant; nothing shows the flaw is in its agent or tool component | U (cannot be decided from the record) |
| RQ1-0156 | Command injection in a usage-statistics dashboard endpoint of an MCP gateway, not in its gateway/proxy function | Eligible as a whole MCP-gateway product; weak E3 suspicion only |
| RQ1-0060 | A command guard installed for coding agents; counts as a connector/plugin only under a broad reading of (ii) | borderline (ii) |
| RQ1-0034 | SQL injection in a metrics-service component of an MCP gateway/registry | Eligible as an MCP gateway product; weak E3 suspicion only |

The other one-line records (RQ1-0077, 0218, 0277, 0296, 0297, 0311–0314, 0326) name an agent or connector product but
give too little to confirm that the flaw sits in its agent/tool component; they are eligible by the product test only.
No withdrawn or rejected record (E5) and no record outside the window was seen in the saved sources.
