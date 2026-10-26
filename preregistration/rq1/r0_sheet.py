#!/usr/bin/env python3
"""RQ1: the author's labelling sheet (R0, D42 points 3-4) as one self-contained HTML page, no network, no AI.

    python3 preregistration/rq1/r0_sheet.py OUT.html

Cases come from rq1-cases.json (the checked summaries; null = non-response) in the order SHA-256(seed + ":r0:" + case id), seed
from rq1-sample-manifest.json (D44 point 4). One case per screen: its summary, a link to its primary source with a "source
opened" record, the four classes, and for the eight bundles the D45 question (shown once the class is chosen) and the counting rule;
the full criteria stay in view. Keys: 1-4 choose the class, S/Y and N answer D45 (a key only chooses; Enter moves to the next case
to do), left/right move, U the last answered case, O open the source, B save a copy; key repeat and Space never answer. The page
shows no proposed class, model output or suggestion. Progress is kept in the browser (one tab writes; copies to a file can be
saved and restored, validated before use); the export writes rq1-r0.json ({"classes": {id: 1-4 or null},
"bundle_model_finding": {...}, "source_opened": {...}, "declaration": ...}) only when every case is answered and the declaration
is ticked.
"""
import csv, hashlib, json, pathlib, sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from classify import CRITERIA, CRITERIA_SHA256  # noqa: E402  (the same criteria the model raters get)

TEMPLATE = r"""<!doctype html><html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>R0 sheet</title><style>
:root{--bg:#fbfaf7;--fg:#1d1d1b;--muted:#5d5b55;--card:#fff;--line:#e3e0d8;--accent:#1f5f8b;--sel:#1f5f8b;--selfg:#fff;--warn:#b00020;--note:#8a5a00;--notebg:#fff4e0;--done:#2f7d46;--part:#b7791f}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--bg:#17171a;--fg:#ecebe6;--muted:#a8a69f;--card:#212125;--line:#34343a;--accent:#7fb6dd;--sel:#7fb6dd;--selfg:#111;--warn:#ff6b7a;--note:#f0b35a;--notebg:#2c2316;--done:#7fcf95;--part:#e0a84a}}
:root[data-theme="dark"]{--bg:#17171a;--fg:#ecebe6;--muted:#a8a69f;--card:#212125;--line:#34343a;--accent:#7fb6dd;--sel:#7fb6dd;--selfg:#111;--warn:#ff6b7a;--note:#f0b35a;--notebg:#2c2316;--done:#7fcf95;--part:#e0a84a}
*{box-sizing:border-box} body{margin:0;background:var(--bg);color:var(--fg);font:17px/1.55 system-ui,-apple-system,"Segoe UI",sans-serif}
#banners{position:sticky;top:0;z-index:3}
header{position:sticky;top:0;z-index:2;background:var(--bg);border-bottom:1px solid var(--line);padding:.5rem 16px}
.bar{height:8px;background:var(--line);border-radius:4px;overflow:hidden;margin:.35rem 0} .bar>i{display:block;height:100%;background:var(--done);width:0}
.top{display:flex;flex-wrap:wrap;gap:.5rem;align-items:center;justify-content:space-between} .muted{color:var(--muted);font-size:.9rem}
button{font:inherit;font-size:.95rem;padding:.4rem .8rem;border:1px solid var(--line);background:var(--card);color:var(--fg);border-radius:7px;cursor:pointer}
button:disabled{opacity:.45;cursor:default}
main{display:grid;grid-template-columns:minmax(0,1fr) 24rem;gap:1rem;max-width:76rem;margin:0 auto;padding:1rem 16px 3rem}
@media (max-width:980px){main{grid-template-columns:1fr}}
.card{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:1rem 1.1rem}
#summary{font-size:1.12rem;line-height:1.65;margin:.4rem 0 1rem}
.classes{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:.6rem;margin:.8rem 0}
.classes button,.yn button{padding:.8rem;text-align:left;font-size:1rem} .classes b,.yn b{font-size:1.15rem;margin-right:.4rem}
.classes button.on,.yn button.on{background:var(--sel);color:var(--selfg);border-color:var(--sel)}
.yn{display:flex;gap:.6rem;margin:.5rem 0;flex-wrap:wrap} #bundle{border-top:1px dashed var(--line);margin-top:.8rem;padding-top:.6rem}
.rule{font-size:.9rem} .rule h3{font-size:1rem;margin:.2rem 0 .4rem} kbd{border:1px solid var(--line);border-bottom-width:2px;border-radius:4px;padding:0 .3rem;font-size:.85em}
#warn{display:none;background:var(--warn);color:#fff;padding:.5rem 16px;font-weight:600}
#note{display:none;background:var(--notebg);color:var(--note);padding:.5rem 16px;font-weight:600}
#grid{display:none;grid-template-columns:repeat(auto-fill,minmax(2.1rem,1fr));gap:.3rem;max-width:76rem;margin:.6rem auto;padding:0 16px}
#grid button{padding:.25rem 0;font-size:.8rem} #grid button.done{background:var(--done);color:#fff;border-color:var(--done)}
#grid button.part{background:var(--part);color:#111;border-color:var(--part)} #grid button.cur{outline:2px solid var(--accent)}
pre{white-space:pre-wrap;font-size:.82rem;background:var(--bg);padding:.6rem;border-radius:6px;margin:.3rem 0}
#finish,#countrule{display:none} #summary_en{display:none;border-left:3px solid var(--line);padding-left:.8rem;color:var(--muted)} a{color:var(--accent)} #nextbtn{font-weight:600}
</style></head><body>
<div id="banners"><div id="warn"></div><div id="note"></div></div>
<header><div class="top"><div><b id="count"></b> <span class="muted" id="last"></span></div>
<div><button id="btn-grid">Griglia</button> <button id="btn-backup">Salva copia (B)</button>
<label class="muted">Carica copia <input type="file" id="restore" accept="application/json"></label></div></div>
<div class="bar"><i id="barfill"></i></div></header>
<div id="grid"></div>
<main><section class="card">
<div class="top"><div class="muted" id="pos"></div><div><button id="prev">← Prec.</button> <button id="next">Succ. →</button> <button id="lastbtn">Ultimo (U)</button></div></div>
<p id="summary"></p><p class="muted" id="langline"><button id="btn-lang">Mostra l'originale inglese (T)</button>
<span>Testo in italiano: traduzione controllata (D46); il riferimento è l'originale inglese, lo stesso dato ai modelli.</span></p>
<p id="summary_en" lang="en"></p>
<p><a id="src" href="#" target="_blank" rel="noopener noreferrer">Apri la fonte primaria (O)</a> · <label><input type="checkbox" id="opened"> fonte aperta</label></p>
<div id="guide" class="card" style="margin:.4rem 0 .8rem">
<div id="qhist" class="muted"></div>
<p id="qtext" style="font-weight:600;margin:.4rem 0"></p><p id="qhint" class="muted" style="margin:.2rem 0 .6rem"></p>
<div class="yn" id="qbtns"><button data-q="yes"><b>S</b>sì</button><button data-q="no"><b>N</b>no</button><button data-q="unk"><b>?</b>non so</button></div>
<p id="qresult" style="font-weight:600;margin:.5rem 0 0"></p>
<p class="muted" style="margin:.3rem 0 0"><button id="qreset">Ricomincia le domande (R)</button></p></div>
<p class="muted" id="manualhint" style="margin:.2rem 0">Oppure scegli o cambia tu la classe:</p>
<div class="classes" id="classes"></div>
<div id="bundle"><p><b>Più rilievi nello stesso caso (D45).</b> Almeno uno dei rilievi, preso da solo, funziona solo perché il modello
segue istruzioni di cui non avrebbe dovuto fidarsi? <span class="muted">(Does at least one finding, taken alone, work only because the model
follows instructions it should not have trusted?)</span></p><div class="yn"><button data-b="yes"><b>S</b>sì</button><button data-b="no"><b>N</b>no</button></div></div>
<p><button id="nextbtn">Avanti: prossimo da fare (Invio)</button></p>
<div id="finish" class="card"><p><b>Tutti i casi hanno una risposta.</b> Ricontrolla dalla griglia se vuoi, poi:</p>
<p><label><input type="checkbox" id="decl"> I labelled these cases myself, without AI assistance (D42 point 4).</label></p>
<p><button id="export">Esporta rq1-r0.json</button></p></div>
</section>
<aside class="card rule"><h3>Criteri (traduzione controllata, D46)</h3><pre lang="it">__CRITERIA_IT__</pre>
<p><button id="btn-crit-en">Criteri originali in inglese (E)</button></p><pre id="crit_en" lang="en" style="display:none">__CRITERIA__</pre>
<div id="countrule"><h3>Questo caso ha più rilievi</h3><p class="muted">Applica la regola di conteggio qui sopra.</p></div>
<p class="muted">Tasti: <kbd>1</kbd>–<kbd>4</kbd> sceglie la classe · <kbd>S</kbd>/<kbd>N</kbd>/<kbd>?</kbd> rispondono alle domande (poi alla D45) · <kbd>R</kbd> ricomincia le domande · <kbd>Invio</kbd> prossimo
da fare · <kbd>←</kbd> <kbd>→</kbd> sposta · <kbd>U</kbd> ultimo risposto · <kbd>T</kbd> riassunto inglese · <kbd>E</kbd> criteri inglesi ·
<kbd>O</kbd> fonte · <kbd>B</kbd> salva copia. Un tasto sceglie e non fa avanzare: si avanza solo con Invio. Nessuna classe è
proposta in questa pagina.</p></aside></main>
<script>
const CASES = __DATA__; const NONRESP = __NONRESP__; const KEY = "rq1-r0-" + __SEEDKEY__; const NAMES = __NAMES__;
const SEED = __SEED__; const CRIT_SHA = __CRITSHA__;
const ids = CASES.map(c => c.id); const bids = CASES.filter(c => c.bundle).map(c => c.id);
const OWNER = KEY + "-owner"; const BKEY = KEY + "-since-backup"; const ME = String(Date.now()) + Math.random(); let blocked = false;
let state = {c: {}, o: {}, a: {}, b: {}, q: {}, m: {}, x: {}, decl: false}; let cur = 0; let lastIdx = null; let showEn = false;
const $ = id => document.getElementById(id);
function warn(msg) { $("warn").textContent = msg; $("warn").style.display = "block"; }
function note(msg) { $("note").textContent = msg; $("note").style.display = msg ? "block" : "none"; }
function block(msg) { blocked = true; warn(msg); render(); }
const OTHER = "Il foglio è stato aperto in un'altra scheda o finestra. Questa non salva e non accetta risposte: chiudila e continua nella più recente.";
let memoryOnly = false;  // storage unavailable: answers live in memory only, file copies are the only backup
try { localStorage.setItem(OWNER, ME); } catch (e) { memoryOnly = true;
  warn("Questo browser non conserva i progressi (" + e.name + "): lavori in memoria. Salva una copia su file spesso (tasto B) e prima di chiudere."); }
window.addEventListener("storage", e => { if (e.key === OWNER && e.newValue !== ME) block(OTHER); });
let memBackup = 0;
function sinceBackup() { if (memoryOnly) return memBackup; try { return +(localStorage.getItem(BKEY) || 0); } catch (e) { return memBackup; } }
// D47: the decision rule and counting rule of the criteria as yes/no questions, in the rule's order, worded as the checked
// Italian criteria (criteria-it.txt); hints say only where to look. The first decisive answer gives the class.
const Q = {
  q1: {text: "L'attacco funziona solo perché il modello segue istruzioni di cui non avrebbe dovuto fidarsi, qualunque sia il canale di consegna?",
       hint: "Dove guardare: chi o che cosa fornisce l'input che fa scattare il difetto. Sì = classe 4."},
  q1b: {text: "Questo caso ha più rilievi. Ogni rilievo richiede che il modello segua istruzioni di cui non avrebbe dovuto fidarsi?",
       hint: "Dove guardare: per ogni rilievo, chi o che cosa fornisce l'input che lo fa scattare. Sì = classe 4 (regola di conteggio)."},
  q2: {text: "Il difetto viene eseguito all'avvio o prima della decisione di fiducia dell'utente, oppure è un difetto nei meccanismi di avvio ed esecuzione dell'agente stesso (confini della sandbox, invocazioni di tool in background, risoluzione dei percorsi) che permette al contenuto del repository di eseguire codice senza alcuna decisione dell'utente o del modello?",
       hint: "Dove guardare: quando scatta il difetto e se qualcuno (utente o modello) deve decidere qualcosa prima. Sì = classe 1."},
  q3: {text: "Il passaggio di conferma o di consenso rappresenta in modo falso o salta ciò che accade?",
       hint: "Dove guardare: che cosa vede o conferma l'utente e che cosa accade davvero. Sì = classe 2."},
  q4: {text: "È un difetto classico di autenticazione, autorizzazione o origine nei servizi intorno all'agente (server MCP, SDK, connettori, bridge)?",
       hint: "Dove guardare: chi può chiamare o usare il servizio e con quali controlli. Sì = classe 3."},
  d45: {text: "Domanda D45: almeno uno dei rilievi, preso da solo, funziona solo perché il modello segue istruzioni di cui non avrebbe dovuto fidarsi?",
       hint: "Serve solo per un'analisi secondaria (rilievi misti). Non cambia la classe."}};
const BUNDLE_NOTE = " Considera solo i rilievi che funzionano senza che il modello segua tali istruzioni: vale il primo sì (la prima tra le classi 1-3).";
function flow(id) {  // -> {next, cls, manual, unk}
  const a = state.q[id] || {}; const first = bids.includes(id) ? "q1b" : "q1";
  if (a[first] === undefined) return {next: first};
  if (a[first] === "yes") return {cls: 4};
  let unk = a[first] === "unk";  // a "don't know" never stops the questions; before the first yes, the author chooses
  for (const [k, cls] of [["q2", 1], ["q3", 2], ["q4", 3]]) {
    if (a[k] === undefined) return {next: k, unk};
    if (a[k] === "unk") { unk = true; continue; }  // keep asking, but an earlier unknown step means the author chooses
    if (a[k] === "yes") return unk ? {manual: true, unk} : {cls};
  }
  return {manual: true, unk}; }
function slot(id) {  // what the question slot asks now: a rule question, then D45 for bundles
  if (state.m[id] && state.c[id] !== undefined) return bids.includes(id) && state.b[id] === undefined ? "d45" : null;
  const f = flow(id); if (f.next) return f.next;
  if (state.c[id] !== undefined && bids.includes(id) && state.b[id] === undefined) return "d45";
  return null; }
let guardUntil = 0;  // a fast extra S/N right after the slot changes never answers the new question
function answerSlot(v) { const id = ids[cur]; const k = slot(id); if (blocked || !k || Date.now() < guardUntil) return;
  if (k === "d45") { if (v === "unk") return; setBundle(v); guardUntil = Date.now() + 500; return; }
  answer(id => { state.q[id] = {...(state.q[id] || {}), [k]: v}; const g = flow(id);
    if (g.cls) { state.c[id] = g.cls; state.m[id] = false; } });
  guardUntil = Date.now() + 500; }
function resetQ() { if (blocked) return; answer(id => { delete state.q[id]; delete state.c[id]; delete state.m[id]; delete state.b[id]; delete state.x[id]; }); }
function contradicts(id, k) {  // does class k go against any recorded answer? (D47 amendment)
  const a = state.q[id] || {}; const f = flow(id);
  if (f.cls !== undefined) return f.cls !== k;
  const first = bids.includes(id) ? "q1b" : "q1"; const step = {1: "q2", 2: "q3", 3: "q4"};
  if (a[first] === "yes") return k !== 4;
  if (a[first] === "no" && k === 4) return true;
  if (k <= 3) return a[step[k]] === "no" || [1, 2, 3].some(j => j < k && a[step[j]] === "yes");
  return false; }
function answered(id) { return state.c[id] !== undefined && (!bids.includes(id) || state.b[id] !== undefined); }
function save() { if (blocked) return false; if (memoryOnly) return true;
  try { if (localStorage.getItem(OWNER) !== ME) { block(OTHER); return false; }
    localStorage.setItem(KEY, JSON.stringify(state)); return true; }
  catch (e) { warn("Non riesco a salvare in questo browser (" + e.name + "): premi subito 'Salva copia'."); return false; } }
function render() {
  const c = CASES[cur]; const id = c.id; const done = ids.filter(answered).length;
  $("count").textContent = done + " / " + ids.length + " fatti";
  $("barfill").style.width = (100 * done / ids.length) + "%";
  $("pos").textContent = "Caso " + (cur + 1) + " / " + ids.length + " · " + id;
  $("summary").textContent = c.summary_it; $("summary_en").textContent = c.summary;
  $("summary_en").style.display = showEn ? "block" : "none";
  $("btn-lang").textContent = showEn ? "Nascondi l'originale inglese (T)" : "Mostra l'originale inglese (T)"; $("src").href = c.src; $("opened").checked = !!(state.o[id] || state.a[id]);
  $("opened").disabled = !!state.a[id] || blocked;
  document.querySelectorAll("#classes button").forEach(b => { b.classList.toggle("on", state.c[id] === +b.dataset.k); b.disabled = blocked; });
  const f = flow(id); const qa = state.q[id] || {}; const k = slot(id);
  $("qhist").textContent = Object.entries(qa).map(([q, v]) => (q === "q1b" ? "Q1 (più rilievi)" : q.toUpperCase()) + ": " + {yes: "sì", no: "no", unk: "non so"}[v]).join(" · ")
    + (state.b[id] ? " · D45: " + (state.b[id] === "yes" ? "sì" : "no") : "");
  if (k) { $("qtext").textContent = Q[k].text;
    $("qhint").textContent = Q[k].hint + (bids.includes(id) && ["q2", "q3", "q4"].includes(k) ? BUNDLE_NOTE : "");
    $("qbtns").style.display = "flex"; document.querySelector('#qbtns [data-q="unk"]').style.display = k === "d45" ? "none" : ""; }
  else { $("qtext").textContent = ""; $("qhint").textContent = ""; $("qbtns").style.display = "none"; }
  document.querySelectorAll("#qbtns button").forEach(b => b.disabled = blocked);
  $("qresult").textContent = state.c[id] !== undefined
    ? "Classe: " + state.c[id] + " — " + NAMES[state.c[id] - 1] + (state.m[id] ? (state.x[id] ? " (scelta da te, diversa dalle risposte)" : " (scelta da te)") : " (dalle tue risposte)")
    : (f.manual ? (f.unk ? "Hai risposto \u201cnon so\u201d a un passaggio: scegli tu la classe con 1–4 qui sotto." : "Nessuna risposta sì: scegli tu la classe con 1–4 qui sotto.") : "");
  $("bundle").style.display = "none";  // D45 is asked in the question slot (D47)
  $("countrule").style.display = c.bundle ? "block" : "none";
  $("prev").disabled = cur === 0; $("next").disabled = cur === ids.length - 1; $("lastbtn").disabled = lastIdx === null;
  $("finish").style.display = done === ids.length ? "block" : "none"; $("decl").checked = !!state.decl;
  $("decl").disabled = blocked; $("export").disabled = blocked;
  const g = $("grid"); if (g.style.display === "grid") g.querySelectorAll("button").forEach((b, i) => {
    b.classList.toggle("done", answered(ids[i])); b.classList.toggle("part", !answered(ids[i]) && state.c[ids[i]] !== undefined);
    b.classList.toggle("cur", i === cur); }); }
function go(i) { cur = Math.max(0, Math.min(ids.length - 1, i)); render(); window.scrollTo(0, 0); }
function firstTodo() { const i = ids.findIndex(id => !answered(id)); return i < 0 ? null : i; }
function nextTodo() { for (let k = 1; k <= ids.length; k++) { const i = (cur + k) % ids.length; if (!answered(ids[i])) return go(i); }
  note("Tutti i casi hanno una risposta: spunta la dichiarazione ed esporta."); render(); }
function answer(fn) { if (blocked) return; const id = ids[cur]; const was = answered(id); fn(id);
  if (!save()) { render(); return; } lastIdx = cur;
  $("last").textContent = "· ultimo: " + id + " → " + state.c[id] + (state.b[id] ? " / D45 " + (state.b[id] === "yes" ? "sì" : "no") : "");
  if (!was && answered(id)) { memBackup = sinceBackup() + 1; if (!memoryOnly) try { localStorage.setItem(BKEY, String(memBackup)); } catch (e) {}
    if (sinceBackup() >= 20) note("Promemoria: salva una copia su file ora (tasto B)."); }
  render(); }
function setClass(k) { const id = ids[cur]; if (blocked) return; const f = flow(id);
  if (f.cls === k) { answer(id => { state.c[id] = k; state.m[id] = false; delete state.x[id]; }); return; }
  if (f.next && !confirm("Non hai finito le domande. Scegliere comunque la classe " + k + "?")) return;
  const contra = contradicts(id, k);
  if (contra && !confirm("La classe " + k + " non segue dalle risposte che hai dato. Sceglierla comunque? (viene registrato)")) return;
  answer(id => { state.c[id] = k; state.m[id] = true; if (contra) state.x[id] = true; else delete state.x[id]; }); }
function setBundle(v) { const id = ids[cur]; if (!bids.includes(id) || state.c[id] === undefined) return; answer(id => state.b[id] = v); }
function markOpened() { if (blocked) return; state.a[ids[cur]] = true; save(); render(); }
function openSource() { markOpened(); window.open(CASES[cur].src, "_blank", "noopener,noreferrer"); }
function snapshot() { return JSON.parse(JSON.stringify(state)); }
function validBackup(j) {  // the whole structure is checked before anything changes
  if (!j || typeof j !== "object" || j.seed !== KEY) return "è di un altro foglio";
  const d = j.progress; if (!d || typeof d !== "object") return "manca progress";
  if (!d.c || typeof d.c !== "object" || !d.o || typeof d.o !== "object") return "mancano parti";
  for (const [id, v] of Object.entries(d.c)) if (!ids.includes(id) || ![1, 2, 3, 4].includes(v)) return "caso o classe sconosciuti: " + id;
  for (const [id, v] of Object.entries(d.b || {})) if (!bids.includes(id) || !["yes", "no"].includes(v)) return "risposta D45 non valida: " + id;
  for (const part of ["o", "a"]) for (const [id, v] of Object.entries(d[part] || {}))
    if (!ids.includes(id) || typeof v !== "boolean") return "valore 'fonte aperta' non valido: " + id;
  for (const [id, a] of Object.entries(d.q || {})) { if (!ids.includes(id) || !a || typeof a !== "object") return "risposte guidate non valide: " + id;
    for (const [k, v] of Object.entries(a)) if (!["q1", "q1b", "q2", "q3", "q4"].includes(k) || !["yes", "no", "unk"].includes(v)) return "risposta guidata non valida: " + id; }
  for (const part of ["m", "x"]) for (const [id, v] of Object.entries(d[part] || {}))
    if (!ids.includes(id) || typeof v !== "boolean") return "valore 'scelta da te' non valido: " + id;
  for (const [id, a] of Object.entries(d.q || {})) {
    if ((a.q1 !== undefined && bids.includes(id)) || (a.q1b !== undefined && !bids.includes(id))) return "domanda 1 incoerente: " + id; }
  if (typeof d.decl !== "boolean") return "dichiarazione non valida";
  return null; }
function adopt(d) { const q = {}; Object.entries(d.q || {}).forEach(([k, v]) => q[k] = {...v});
  const st = {c: {...d.c}, o: {...d.o}, a: {...(d.a || {})}, b: {...(d.b || {})}, q, m: {...(d.m || {})}, x: {...(d.x || {})}, decl: d.decl};
  const saved = state; state = st;  // flow() reads state
  for (const id of Object.keys(st.c)) {  // a class not produced by the recorded answers counts as chosen directly (e.g. older progress)
    if (!st.m[id] && flow(id).cls !== st.c[id]) st.m[id] = true; }
  state = saved; return st; }
function load() { if (memoryOnly) return; let raw = null;
  try { raw = localStorage.getItem(KEY); } catch (e) { memoryOnly = true;
    warn("Questo browser non conserva i progressi (" + e.name + "): lavori in memoria. Salva una copia su file spesso (tasto B)."); return; }
  if (!raw) return;
  try { const d = JSON.parse(raw);
    const bad = validBackup({seed: KEY, progress: d}); if (bad) throw new Error(bad); state = adopt(d); }
  catch (e) { try { localStorage.setItem(KEY + "-quarantine-" + Date.now(), raw || ""); } catch (x) {}
    block("I progressi salvati non sono leggibili (" + e.message + "): sono stati messi da parte e nulla viene sovrascritto. " +
          "Carica la tua ultima copia con 'Carica copia'."); } }
document.addEventListener("keydown", e => {
  if (e.ctrlKey || e.metaKey || e.altKey || e.repeat) { if (e.repeat) e.preventDefault(); return; }
  const t = e.target.tagName; if (t === "INPUT" && e.target.type === "file") return;
  const k = e.key.toLowerCase();
  const answerBtn = t === "BUTTON" && (e.target.closest("#classes") || e.target.closest("#bundle") || e.target.closest("#qbtns"));
  if ((k === " " || k === "enter") && answerBtn) { e.preventDefault(); return; }  // a focused answer button is never re-pressed
  if ((k === " " || k === "enter") && (t === "INPUT" || t === "BUTTON" || t === "A")) return;  // native activation elsewhere
  if (k === " ") return;
  if (["1", "2", "3", "4"].includes(k)) setClass(+k);
  else if (k === "s" || k === "y") answerSlot("yes"); else if (k === "n") answerSlot("no");
  else if (k === "?") answerSlot("unk"); else if (k === "r") resetQ();
  else if (k === "enter") nextTodo(); else if (k === "arrowright") go(cur + 1); else if (k === "arrowleft") go(cur - 1);
  else if (k === "u") { if (lastIdx !== null) go(lastIdx); }
  else if (k === "o") openSource(); else if (k === "b") $("btn-backup").click();
  else if (k === "t") { showEn = !showEn; render(); } else if (k === "e") $("btn-crit-en").click();
  else return; e.preventDefault(); });
function btn(el, fn) { el.addEventListener("click", e => { fn(e); el.blur(); }); }
NAMES.forEach((n, i) => { const b = document.createElement("button"); b.dataset.k = i + 1;
  b.innerHTML = "<b>" + (i + 1) + "</b>"; b.append(document.createTextNode(n)); btn(b, () => setClass(i + 1)); $("classes").append(b); });
document.querySelectorAll("#bundle button").forEach(b => btn(b, () => setBundle(b.dataset.b)));
document.querySelectorAll("#qbtns button").forEach(b => btn(b, () => answerSlot(b.dataset.q)));
btn($("qreset"), resetQ);
btn($("prev"), () => go(cur - 1)); btn($("next"), () => go(cur + 1)); btn($("nextbtn"), nextTodo);
btn($("lastbtn"), () => { if (lastIdx !== null) go(lastIdx); });
btn($("btn-lang"), () => { showEn = !showEn; render(); });
btn($("btn-crit-en"), () => { const p = $("crit_en"); p.style.display = p.style.display === "block" ? "none" : "block"; });
const src = $("src"); src.addEventListener("click", e => { e.preventDefault(); openSource(); });
src.addEventListener("auxclick", markOpened); src.addEventListener("contextmenu", markOpened);
$("opened").addEventListener("change", e => { if (!blocked) { state.o[ids[cur]] = e.target.checked; save(); } e.target.blur(); render(); });
$("decl").addEventListener("change", e => { if (!blocked) { state.decl = e.target.checked; save(); } e.target.blur(); render(); });
btn($("btn-grid"), () => { const g = $("grid"); g.style.display = g.style.display === "grid" ? "none" : "grid"; render(); });
ids.forEach((id, i) => { const b = document.createElement("button"); b.textContent = i + 1; b.title = id; btn(b, () => go(i)); $("grid").append(b); });
btn($("btn-backup"), () => {
  const blob = new Blob([JSON.stringify({progress: snapshot(), seed: KEY, saved: new Date().toISOString()}, null, 2)], {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "rq1-r0-progress.json"; a.click();
  memBackup = 0; if (!memoryOnly) try { localStorage.setItem(BKEY, "0"); } catch (e) {} note(""); });
$("restore").addEventListener("change", async e => {
  const f = e.target.files[0]; e.target.value = ""; if (!f) return;
  let j; try { j = JSON.parse(await f.text()); } catch (err) { warn("La copia non è un file JSON valido; nulla è cambiato."); return; }
  const bad = validBackup(j); if (bad) { warn("Copia rifiutata (" + bad + "); nulla è cambiato."); return; }
  const nNew = Object.keys(j.progress.c).length, nNow = Object.keys(state.c).length;
  if (!confirm("Copia del " + (j.saved || "?") + " con " + nNew + " risposte. Ora nel foglio ce ne sono " + nNow +
               ". Sostituire le risposte attuali con quelle della copia?")) return;
  const before = snapshot();
  try { state = adopt(j.progress); blocked = false; if (!memoryOnly) localStorage.setItem(OWNER, ME);
    if (!memoryOnly) $("warn").style.display = "none";
    save(); const i = firstTodo(); go(i === null ? 0 : i); }
  catch (err) { state = before; render(); warn("La copia non si può applicare (" + err.name + "); restano le risposte di prima."); } });
btn($("export"), () => {
  if (blocked) return;
  const missing = ids.filter(id => !answered(id));
  if (missing.length) { alert("Mancano risposte: " + missing.join(", ")); return; }
  if (!state.decl) { alert("Spunta prima la dichiarazione."); return; }
  const odd = bids.filter(id => (state.c[id] === 4 && state.b[id] === "no") || ((state.q[id] || {}).q1b === "yes" && state.b[id] === "no"));
  if (odd.length && !confirm("Ricontrolla questi casi con più rilievi (classe e risposta D45 da rileggere insieme alla regola di conteggio): "
                             + odd.join(", ") + ". Esportare comunque?")) return;
  const classes = {}; ids.forEach(id => classes[id] = state.c[id]); NONRESP.forEach(id => classes[id] = null);
  const bundle = {}; bids.forEach(id => bundle[id] = state.b[id] === "yes");
  const auto = {}, manual = {}, opened = {}; ids.forEach(id => { auto[id] = !!state.a[id]; manual[id] = !!state.o[id]; opened[id] = auto[id] || manual[id]; });
  const guided = {}, direct = {}, contra = {}; ids.forEach(id => { guided[id] = state.q[id] || {}; direct[id] = !!state.m[id]; contra[id] = !!state.x[id]; });
  const blob = new Blob([JSON.stringify({classes, bundle_model_finding: bundle, guided_answers: guided, class_set_directly: direct, direct_class_contradicts_answers: contra,
    source_opened: opened, source_opened_auto: auto,
    source_opened_manual: manual, declaration: "labelled by the author without AI assistance (D42 point 4)",
    seed: SEED, criteria_sha256: CRIT_SHA, sheet: "v3-guided", exported: new Date().toISOString()}, null, 2)], {type: "application/json"});
  const a = document.createElement("a"); a.href = URL.createObjectURL(blob); a.download = "rq1-r0.json"; a.click(); });
load(); { const i = firstTodo(); go(i === null ? 0 : i); }
if (sinceBackup() >= 20) note("Promemoria: salva una copia su file ora (tasto B).");
</script></body></html>"""


def main(out):
    seed = json.loads((HERE / "rq1-sample-manifest.json").read_text())["seed"]
    cases = json.loads((HERE / "rq1-cases.json").read_text())
    bundles = {r["case_id"] for r in json.loads((HERE / "rq1-summary-records.json").read_text()) if len(r["findings"]) > 1}
    src = {r["case_id"]: r["primary_source"] for r in csv.DictReader(open(HERE / "rq1-frame.csv", newline=""))}
    order = sorted(cases, key=lambda c: hashlib.sha256(f"{seed}:r0:{c['id']}".encode()).hexdigest())
    it = {c["id"]: c["summary_it"] for c in json.loads((HERE / "rq1-cases-it.json").read_text())}
    labelled = [{"id": c["id"], "summary": c["summary"], "summary_it": it[c["id"]], "src": src[c["id"]], "bundle": c["id"] in bundles}
                for c in order if c["summary"] is not None]
    criteria_it = (HERE / "criteria-it.txt").read_text().strip()
    nonresponse = [c["id"] for c in order if c["summary"] is None]
    criteria = CRITERIA.rsplit("\nAnswer with", 1)[0].replace("You are classifying", "Classify")
    names = [line.split(". ", 1)[1].split(" - ")[0] for line in criteria_it.splitlines() if line[:2] in ("1.", "2.", "3.", "4.")]
    assert len(names) == 4, names
    esc = lambda t: t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    unwrap = lambda t: "\n".join(l if not l.startswith("   ") else "\0" + l.strip() for l in t.splitlines()).replace("\n\0", " ")
    # display only: continuation lines (indented) join their item, so the narrow column wraps naturally; words unchanged
    js = lambda v: json.dumps(v, ensure_ascii=False).replace("</", "<\\/")
    assert unwrap(criteria).split() == criteria.split() and unwrap(criteria_it).split() == criteria_it.split()
    page = (TEMPLATE.replace("__CRITERIA_IT__", esc(unwrap(criteria_it))).replace("__CRITERIA__", esc(unwrap(criteria))).replace("__DATA__", js(labelled))
            .replace("__NONRESP__", js(nonresponse)).replace("__SEEDKEY__", js(seed[:16])).replace("__NAMES__", js(names))
            .replace("__SEED__", js(seed)).replace("__CRITSHA__", js(CRITERIA_SHA256)))
    assert "__" not in page.replace("__proto__", ""), "unfilled placeholder"
    pathlib.Path(out).write_text(page)
    print(f"{len(labelled)} cases, {len(nonresponse)} non-response, {len(bundles)} bundles -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
