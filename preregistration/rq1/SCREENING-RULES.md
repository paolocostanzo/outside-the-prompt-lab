# RQ1 frame — screening rules for the query candidates (25 Oct 2026)

Written before screening, from §3 of the preregistration (inclusion criteria i–iii), D1 and D41. Screening decides only whether a
candidate enters the frame and records the product and its type; it never assigns or hints at a class (no class words, no guess
of where the flaw sits in the taxonomy).

## Inclusion (all three)
- (i) *Primary source*: the GHSA or CVE record itself counts (preregistration §3: "vendor advisory or CVE record"). Always met for
  query candidates; a candidate whose record is withdrawn or rejected is excluded (E5).
- (ii) *Tool-using AI agent or a connector of one*: the vulnerable component is one of
  - **agent client**: an AI agent that calls tools or acts on the user's system or accounts — coding agents and IDE agents (Claude
    Code, Codex, Gemini CLI, Copilot agent/Chat, Cursor, Cline, Goose…), assistants with tool use, and agent platforms or workflow
    builders when the flaw is in their agent, tool or MCP component (Dify, Langflow, Flowise, n8n AI nodes…);
  - **MCP server or connector**: an MCP server, MCP proxy/gateway/registry, or another tool/plugin/connector whose purpose is to be
    called by an AI agent;
  - **SDK**: an MCP SDK, an agent framework or library whose function is tool calling or agent orchestration (MCP SDKs, LangChain
    tool/agent modules, agent toolkits).
  For general products that only also contain an AI feature, the flaw must be in that agent, tool or MCP component.
- (iii) *Disclosed in the window* 26 Jun – 24 Sep 2026: met by construction of the query (publication date of the record).

## Exclusion reasons
- **E1 keyword false positive**: the matched word is not about an AI agent (database or UI "cursor", unrelated "MCP" acronym,
  "codex" as a product name unrelated to AI, …).
- **E2 AI product without tool use or agent**: model inference servers, model file loaders, LLM gateways/proxies that only relay
  prompts, chat UIs without tools, ML training libraries.
- **E3 flaw outside the agent component** of a general product (ii, last sentence).
- **E4 no product finding** (research papers, generic warnings, documentation-only records).
- **E5 record withdrawn or rejected**.
- **U uncertain**: cannot be decided from the record and its first references; listed for a second reading, never silently dropped.

## Recorded for every candidate
`id, decision (include|exclude|uncertain), reason (I|E1–E5|U), product (repository or product name), product_type (agent client |
MCP server or connector | SDK | n/a), note (≤ 20 words, factual, no class words)`.

Grouping into disclosures (D41 p.1), pilot exclusion across aliases (D3/D41), the timeline cases and the strata are later steps.
