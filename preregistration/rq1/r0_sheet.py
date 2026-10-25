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
                    f'<p class="cls">Class: {radios}</p></section>')
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>R0 sheet</title><style>
body{{font:16px/1.5 system-ui,sans-serif;max-width:46rem;margin:0 auto;padding:1rem;background:#fff;color:#111}}
pre{{white-space:pre-wrap;background:#f4f4f4;padding:.8rem;font-size:14px}} section{{border-top:1px solid #ccc;padding:.6rem 0}}
.cls label{{margin-right:1.2rem}} button{{font-size:16px;padding:.4rem 1rem}} #status{{font-weight:bold}}
</style></head><body>
<h1>RQ1 — R0 labels</h1>
<p>Label each case from its summary with the criteria below; open the primary source when needed and tick "source opened".
No class is proposed anywhere on this page. Cases are in the order fixed by D44 (seed {seed[:12]}…). {len(labelled)} cases to
label; {len(nonresponse)} sampled cases without a summary (non-response) are exported as null.</p>
<pre>{html.escape(criteria)}</pre>
{''.join(rows)}
<section><p><label><input type="checkbox" id="decl"> I labelled these cases myself, without AI assistance (D42 point 4).</label></p>
<p><button id="export">Export rq1-r0.json</button> <span id="status"></span></p></section>
<script>
const NONRESP = {json.dumps(nonresponse)}; const KEY = "rq1-r0-" + {json.dumps(seed[:16])};
const ids = [...document.querySelectorAll("section[id]")].map(s => s.id);
function save() {{ try {{ const d = {{c: {{}}, o: {{}}, decl: document.getElementById("decl").checked}};
  ids.forEach(id => {{ const r = document.querySelector(`input[name="${{id}}"]:checked`); if (r) d.c[id] = +r.value; }});
  document.querySelectorAll(".opened").forEach(b => d.o[b.dataset.case] = b.checked);
  localStorage.setItem(KEY, JSON.stringify(d)); status(); }} catch (e) {{}} }}
function load() {{ try {{ const d = JSON.parse(localStorage.getItem(KEY) || "null"); if (!d) return;
  Object.entries(d.c).forEach(([id, v]) => {{ const r = document.querySelector(`input[name="${{id}}"][value="${{v}}"]`); if (r) r.checked = true; }});
  document.querySelectorAll(".opened").forEach(b => b.checked = !!d.o[b.dataset.case]);
  document.getElementById("decl").checked = !!d.decl; }} catch (e) {{}} }}
function status() {{ const n = ids.filter(id => document.querySelector(`input[name="${{id}}"]:checked`)).length;
  document.getElementById("status").textContent = `${{n}} / ${{ids.length}} labelled`; }}
document.querySelectorAll("a[data-case]").forEach(a => a.addEventListener("click", () => {{
  document.querySelector(`.opened[data-case="${{a.dataset.case}}"]`).checked = true; save(); }}));
document.addEventListener("change", save);
document.getElementById("export").addEventListener("click", () => {{
  const classes = {{}}, opened = {{}}; let missing = [];
  ids.forEach(id => {{ const r = document.querySelector(`input[name="${{id}}"]:checked`); if (r) classes[id] = +r.value; else missing.push(id); }});
  if (missing.length) {{ alert("Not labelled yet: " + missing.join(", ")); return; }}
  if (!document.getElementById("decl").checked) {{ alert("Tick the declaration first."); return; }}
  NONRESP.forEach(id => classes[id] = null);
  document.querySelectorAll(".opened").forEach(b => opened[b.dataset.case] = b.checked);
  const blob = new Blob([JSON.stringify({{classes, source_opened: opened, declaration: "labelled by the author without AI assistance (D42 point 4)",
    exported: new Date().toISOString()}}, null, 2)], {{type: "application/json"}});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "rq1-r0.json"; a.click(); }});
load(); status();
</script></body></html>"""
    pathlib.Path(out).write_text(page)
    print(f"{len(labelled)} cases, {len(nonresponse)} non-response -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
