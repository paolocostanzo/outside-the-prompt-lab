# RQ1 frame — how `rq1-frame.csv` was built (25 Oct 2026)

Frame of D1 under D41 point 1 and D44 point 1, built before any summary or label. Reproducible: `python3 build_frame.py` from the
files listed below. Screening and grouping were done by AI assistants (Claude agents) and the whole frame is checked by Codex
before it is frozen.

| Step | Input → output | Count |
|---|---|---|
| Dated query (D1), 25 Oct 2026 15:57 UTC | `query_frame.py` → `raw-20261025/` (keyword hits and NVD results published; the two full GHSA dumps are not, see below; their hashes are in `SHA256SUMS-uncompressed` and `SHA256SUMS-gz`) | GHSA reviewed 3237 / unreviewed 30917 fetched; 540 keyword hits; NVD 516 CVEs |
| Merge by CVE (GHSA id when no CVE) | `build_candidates.py` → `candidates-20261025.json` | 695 candidates |
| Screening under `SCREENING-RULES.md` (4 agents, one batch each) | → `screening-20261025.csv` | 510 include, 142 exclude, 43 uncertain |
| Second reading of the 43 uncertain, primary sources opened (columns `second_reading`, `evidence`) | → same file | 31 include, 11 exclude, 1 still in doubt → included and flagged `I?` (CVE-2026-19374) |
| Pilot components and aliases removed (D3, D41 point 1) | `pilot` column | 8 records (C01, C02 ×4, C05, C06, C07) |
| Grouping into disclosures (D41 point 1) | `grouping-20261025.json` | 534 records → 471 groups |
| Timeline events (D1; both files match the hashes frozen in D1) | `timeline-events.csv` | 1 event outside the pilot (Splunk SVD-2026-0808), already in the query |
| Eligibility check of every case (D44 point 5), primary source opened, quote per case (4 Claude agents; GitHub advisory API, NVD, cve.org, vendor pages) | → `eligibility-ledger.csv` (keyed by records) | 461 checked: 369 eligible, 92 fail (iii) — repository advisory published before 26 Jun 2026 |
| First public disclosure of every record (D14 p.2): global and repository GitHub advisories (API), NVD, dated pages | `disclosure_dates.py` + `disclosure-manual.csv` → `disclosure-dates.csv` | 535 records; earliest source: 288 repository advisory, 212 global GHSA, 31 NVD, 4 manual |
| Corrections after review | `screening-overrides.csv` | 1 (n8n CVE-2026-86073 included, Codex frame review RQ1-001) |
| Frame | `build_frame.py` → `rq1-frame.csv` | 648 rows; **330 included cases**: 100 agent client, 210 MCP server or connector, 20 SDK; 1 timeline; 1 flagged; 142 E6; 40 date/ledger disagreements listed in `date-vs-ledger.csv` (the date table decides) |

## Rules applied beyond SCREENING-RULES.md
- **Grouping (D41 point 1).** Same product, same date and same cause → one case; follow-ups ("incomplete fix", "bypass of") join
  the disclosure they continue; two ids of one flaw → one case. One vendor bulletin with one id (IBM Langflow nodes 7282147 and
  7286666, HashiCorp HCSEC-2026-23 and -24, Splunk SVD-2026-0808) and one research write-up (playb0t mcp-remote) are one disclosure,
  within and across products; different findings inside them fall under the bundle rule of D41 point 1. A generic "issues fixed"
  list page is not a disclosure. In doubt, records stay separate (the grouping file lists the doubtful pairs kept apart).
- **Follow-ups of disclosures before the window** join the disclosure they continue (D41 point 1), which dates the case (D14:
  first public disclosure) before the window: excluded, E6, with the parent and its NVD publication date in the note. Nine cases:
  Flowise (CVE-2025-8943, 2025-08-14; CVE-2026-31829, 2026-03-10), ckan-mcp-server (CVE-2026-33060, 2026-03-20), mcp-atlassian
  (CVE-2026-27825 and CVE-2026-27826, 2026-03-10), PraisonAI (CVE-2026-44336, 2026-05-08), Pydantic AI (CVE-2026-25580,
  2026-02-06), CodeWhale (CVE-2026-45311, 2026-05-28), FrontMCP/mcp-from-openapi (CVE-2026-39885, 2026-04-08). Found by searching
  every included record for "incomplete fix", "bypass" and similar wording next to an id outside the frame.
- **Disclosure date (E6).** A case's date is its earliest public disclosure. The OX Security MCP supply-chain write-up (LiteLLM,
  GPT Researcher, Fay, LangBot) was published on 15 Apr 2026 (`datePublished` of the page), before the window: excluded, reason
  E6 "disclosed before the window" — the reason defined in D44 point 1 (criterion (iii) of §3 checked on the case; date as in
  D14 point 2).
- **Timeline events** whose type is not vulnerability or advisory (§3: "every event of type vulnerability or advisory") are
  excluded with reason T (UW agentic browsers study: Research; Black Hat talk: Talk). Workflow Identity Hijacking names no product
  or version for its reported instance: E4. Encrypted reasoning blocks: E2.
- **Product type** of a multi-record case: the first type present in the order agent client / MCP server or connector / SDK.
- **Pilot cases without ids** (PromptFiction, DeepJack, GitLost, Azure DevOps MCP, Kiro, the GitSpawn findings without a CVE) were
  searched in the frame by product, date and flaw; none appears. The Cursor, Codex and Claude Code cases in the frame are other
  flaws (e.g. RQ1-0120 Cursor binary planting of git.exe, RQ1-0354 Codex PowerShell parsing).

- **Date sources (D14 point 2, D44 point 1).** The case date is the earliest public advisory: repository security advisory, global GHSA, CVE record or vendor page, whichever is first, taken from
  `disclosure-dates.csv`. Many records carry a later GHSA/CVE date than the repository advisory they publish; 131 cases fall before
  the window this way (E6). The eligibility agents partly used the global GHSA date; where the ledger said "in the window" and
  the table says otherwise (40 cases), the table decides. A public issue or pull request describing the flaw is not
  an advisory or write-up and does not date the case (four cases: RQ1 MiniCode issue #35, mcp-toolbox PR #3324, next-ai-draw-io
  issues #754 and #755; they stay eligible, their earlier issue dates are in the ledger notes).
- **Eligibility notes to read at the frame review:** Copilot records that name no component; GitLab AI Gateway CVE-2026-19889;
  adafap/api-mcp (flagged I?); MountDev CVE-2026-85306 (same plugin as pilot C07, different CVE and versions: kept); Serena (blog
  byline and metadata dates disagree); ssh-mcp-server (disputed by the maintainer).

## Raw data not published
The two full GitHub Advisory Database dumps (`ghsa-reviewed.json`, `ghsa-unreviewed.json`; 34,154 advisories) are not in the
repository: advisory texts quote example tokens and keys from proofs of concept, and the lab never publishes anything that looks
like a credential. Their SHA-256 hashes are recorded; the author keeps the files and provides them on request. For the same reason the published `candidates-20261025.json` has no advisory description texts (`text` field) and the NVD
files keep only id, dates, status and reference URLs; the full versions, used by the screening agents, are kept by the author
and hashed in `SHA256SUMS-full-texts` (the frame commit e62676b in the git history still holds the full candidates file; the
release archives from v0.4.3 on do not). `build_frame.py` and `disclosure_dates.py` run from the published files (they never
read the texts); `build_candidates.py` needs the two dumps.

## Known limits
- Screening and grouping by AI assistants under written rules, not by a second human (as declared in D42/D44).
- The second reading could not open two sources (SiteGround Helper.php, a GitLab work item; 403) and decided from the advisory text.
