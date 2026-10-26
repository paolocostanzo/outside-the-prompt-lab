#!/usr/bin/env python3
"""RQ1: the author's labelling sheet (R0, D42 points 3-4) as one self-contained HTML page, no network, no AI.

    python3 preregistration/rq1/r0_sheet.py OUT.html

Cases come from rq1-cases.json (the checked summaries; null = non-response) in the order SHA-256(seed + ":r0:" + case id), seed
from rq1-sample-manifest.json (D44 point 4). Each case shows its summary, a link to its primary source, the four classes and a
"source opened" box. The page shows no proposed class, model output or suggestion. Progress is kept in the browser; the export
button writes rq1-r0.json ({"classes": {id: 1-4 or null}, "source_opened": {...}, "declaration": ...}).
"""
import csv, hashlib, html, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from classify import CRITERIA  # noqa: E402  (the same criteria the model raters get)


def main(out):
    seed = json.loads((HERE / "rq1-sample-manifest.json").read_text())["seed"]
    cases = json.loads((HERE / "rq1-cases.json").read_text())
    bundles = {r["case_id"] for r in json.loads((HERE / "rq1-summary-records.json").read_text()) if len(r["findings"]) > 1}
    src = {r["case_id"]: r["primary_source"] for r in csv.DictReader(open(HERE / "rq1-frame.csv", newline=""))}
    order = sorted(cases, key=lambda c: hashlib.sha256(f"{seed}:r0:{c['id']}".encode()).hexdigest())
    labelled = [c for c in order if c["summary"] is not None]
    nonresponse = [c["id"] for c in order if c["summary"] is None]
    criteria = CRITERIA.rsplit("\nAnswer with", 1)[0].replace("You are classifying", "Classify")
    rows = []
    for i, c in enumerate(labelled, 1):
        cid = html.escape(c["id"])
        radios = "".join(f'<label><input type="radio" name="{cid}" value="{k}"> {k}</label> ' for k in (1, 2, 3, 4))
        rows.append(f'<section id="{cid}"><h2>{i} / {len(labelled)} · {cid}</h2><p>{html.escape(c["summary"])}</p>'
                    f'<p><a href="{html.escape(src[c["id"]])}" target="_blank" rel="noopener noreferrer" data-case="{cid}">primary '
                    f'source</a> · <label><input type="checkbox" class="opened" data-case="{cid}"> source opened</label></p>'
                    f'<p class="cls">Class: {radios}</p>'
                    + (f'<p class="cls">Several findings (D45): does at least one finding, taken alone, work only because the model '
                       f'follows instructions it should not have trusted? <label><input type="radio" name="b-{cid}" value="yes"> yes'
                       f'</label> <label><input type="radio" name="b-{cid}" value="no"> no</label></p>' if c["id"] in bundles else "")
                    + '</section>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>R0 sheet</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:0 auto;padding:1rem;background:#fff;color:#111}}
pre{{white-space:pre-wrap;background:#f4f4f4;padding:.8rem;font-size:14px}} section{{border-top:1px solid #ccc;padding:.6rem 0}}
.cls label{{margin-right:1.2rem}} button{{font-size:16px;padding:.4rem 1rem}} #status{{font-weight:bold}}
#warn{{position:sticky;top:0;background:#b00020;color:#fff;padding:.6rem;font-weight:bold;display:none}}
</style></head><body>
<div id="warn"></div>
<h1>RQ1 — R0 labels</h1>
<p><button id="backup">Save progress to a file</button> <label>Load progress from a file: <input type="file" id="restore"
accept="application/json"></label></p>
<p>Label each case from its summary with the criteria below; open the primary source when needed and tick "source opened".
No class is proposed anywhere on this page. Cases are in the order fixed by D44 (seed {seed[:12]}…). {len(labelled)} cases to
label; {len(nonresponse)} sampled cases without a summary (non-response) are exported as null.</p>
<pre>{html.escape(criteria)}</pre>
{''.join(rows)}
<section><p><label><input type="checkbox" id="decl"> I labelled these cases myself, without AI assistance (D42 point 4).</label></p>
<p><button id="export">Export rq1-r0.json</button> <span id="status"></span></p></section>
<script>
const NONRESP = {json.dumps(nonresponse)}; const KEY = "rq1-r0-" + {json.dumps(seed[:16])};
const OWNER = KEY + "-owner"; const ME = String(Date.now()) + Math.random(); let blocked = false;
function warn(msg) {{ const w = document.getElementById("warn"); w.textContent = msg; w.style.display = "block"; }}
try {{ localStorage.setItem(OWNER, ME); }} catch (e) {{ warn("This browser does not keep progress: use 'Save progress to a file' often."); }}
window.addEventListener("storage", e => {{ if (e.key === OWNER && e.newValue !== ME) {{ blocked = true;
  warn("The sheet was opened in another tab or window. This one no longer saves: close it and continue in the newest one."); }} }});
const ids = [...document.querySelectorAll("section[id]")].map(s => s.id);
const bids = ids.filter(id => document.querySelector(`input[name="b-${{id}}"]`));
function snapshot() {{ const d = {{c: {{}}, o: {{}}, decl: document.getElementById("decl").checked}};
  ids.forEach(id => {{ const r = document.querySelector(`input[name="${{id}}"]:checked`); if (r) d.c[id] = +r.value; }});
  d.b = {{}}; bids.forEach(id => {{ const r = document.querySelector(`input[name="b-${{id}}"]:checked`); if (r) d.b[id] = r.value; }});
  document.querySelectorAll(".opened").forEach(b => d.o[b.dataset.case] = b.checked);
  return d; }}
function save() {{ status(); if (blocked) return;
  try {{ if (localStorage.getItem(OWNER) !== ME) {{ blocked = true;
      warn("The sheet was opened in another tab or window. This one no longer saves: close it and continue in the newest one."); return; }}
    localStorage.setItem(KEY, JSON.stringify(snapshot())); }}
  catch (e) {{ warn("Progress could not be saved in this browser (" + e.name + "): use 'Save progress to a file' now."); }} }}
function apply(d) {{  // replaces whatever is on the page with a saved snapshot
  document.querySelectorAll("section[id] input[type=radio]").forEach(r => r.checked = false);
  Object.entries(d.c).forEach(([id, v]) => {{ const r = document.querySelector(`input[name="${{id}}"][value="${{v}}"]`); if (r) r.checked = true; }});
  Object.entries(d.b || {{}}).forEach(([id, v]) => {{ const r = document.querySelector(`input[name="b-${{id}}"][value="${{v}}"]`); if (r) r.checked = true; }});
  document.querySelectorAll(".opened").forEach(b => b.checked = !!d.o[b.dataset.case]);
  document.getElementById("decl").checked = !!d.decl; status(); }}
function load() {{ try {{ const d = JSON.parse(localStorage.getItem(KEY) || "null"); if (d) apply(d); }}
  catch (e) {{ warn("Saved progress could not be read (" + e.name + ")."); }} }}
function status() {{ const n = ids.filter(id => document.querySelector(`input[name="${{id}}"]:checked`)).length;
  document.getElementById("status").textContent = `${{n}} / ${{ids.length}} labelled`; }}
document.querySelectorAll("a[data-case]").forEach(a => a.addEventListener("click", () => {{
  document.querySelector(`.opened[data-case="${{a.dataset.case}}"]`).checked = true; save(); }}));
document.addEventListener("change", e => {{ if (e.target.id !== "restore") save(); }});
document.getElementById("backup").addEventListener("click", () => {{
  const blob = new Blob([JSON.stringify({{progress: snapshot(), seed: KEY, saved: new Date().toISOString()}}, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "rq1-r0-progress.json"; a.click(); }});
document.getElementById("restore").addEventListener("change", async e => {{
  const f = e.target.files[0]; if (!f) return;
  let j; try {{ j = JSON.parse(await f.text()); }} catch (err) {{ warn("The progress file is not valid JSON; nothing was changed."); return; }}
  const bad = validBackup(j); if (bad) {{ warn("The progress file was rejected (" + bad + "); nothing was changed."); return; }}
  const before = snapshot();
  try {{ apply(j.progress); blocked = false; localStorage.setItem(OWNER, ME); document.getElementById("warn").style.display = "none"; save(); }}
  catch (err) {{ apply(before); warn("The progress file could not be applied (" + err.name + "); the previous answers were kept."); }} }});
function validBackup(j) {{  // the whole structure is checked before anything on the page changes
  if (!j || typeof j !== "object" || j.seed !== KEY) return "it belongs to another sheet";
  const d = j.progress; if (!d || typeof d !== "object") return "no progress";
  if (!d.c || typeof d.c !== "object" || !d.o || typeof d.o !== "object") return "missing parts";
  for (const [id, v] of Object.entries(d.c)) if (!ids.includes(id) || ![1, 2, 3, 4].includes(v)) return "unknown case or class " + id;
  for (const [id, v] of Object.entries(d.b || {{}})) if (!bids.includes(id) || !["yes", "no"].includes(v)) return "bad answer for " + id;
  for (const [id, v] of Object.entries(d.o)) if (!ids.includes(id) || typeof v !== "boolean") return "bad source-opened value " + id;
  if (typeof d.decl !== "boolean") return "bad declaration value";
  return null; }}
document.getElementById("export").addEventListener("click", () => {{
  const classes = {{}}, opened = {{}}; let missing = [];
  ids.forEach(id => {{ const r = document.querySelector(`input[name="${{id}}"]:checked`); if (r) classes[id] = +r.value; else missing.push(id); }});
  bids.forEach(id => {{ if (!document.querySelector(`input[name="b-${{id}}"]:checked`)) missing.push(id + " (several findings question)"); }});
  if (missing.length) {{ alert("Not labelled yet: " + missing.join(", ")); return; }}
  const bundle = {{}}; bids.forEach(id => bundle[id] = document.querySelector(`input[name="b-${{id}}"]:checked`).value === "yes");
  if (!document.getElementById("decl").checked) {{ alert("Tick the declaration first."); return; }}
  NONRESP.forEach(id => classes[id] = null);
  document.querySelectorAll(".opened").forEach(b => opened[b.dataset.case] = b.checked);
  const blob = new Blob([JSON.stringify({{classes, bundle_model_finding: bundle, source_opened: opened, declaration: "labelled by the author without AI assistance (D42 point 4)",
    exported: new Date().toISOString()}}, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "rq1-r0.json"; a.click(); }});
load(); status();
</script></body></html>"""
    pathlib.Path(out).write_text(page)
    print(f"{len(labelled)} cases, {len(nonresponse)} non-response -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
