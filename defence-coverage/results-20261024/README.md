# RQ4 census, final (24 Oct 2026)

Servers: Azure DevOps (Microsoft), GitHub, Sentry, AWS IaC, SQL Server and Oracle (AWS), at the pinned commits of the census.
- `first-reading.csv`, `second-reading.csv`: the two readings (D17, D22), rows of these servers only.
- `adjudication.csv`: the author's decision on the 91 tools where the readings disagree (D22, D38); the note column records, for
  each case, whether the third reading's proposal was taken as it was or the author chose otherwise.
- `third-reading/`: the third reading's proposals and its instructions (D38).
- `final-census.csv`, `coverage.json`, `COVERAGE.md`: output of `scripts/final_census.py` with
  `--servers azure-devops-mcp,github-mcp-server,sentry-mcp,aws-iac-mcp-server,mssql-mcp-server,oracle-mcp-server`.
Agreement between the two readings is measured before any decision, on their original labels.
AWS was informed before publication and assessed these gaps as having no significant security impact.
