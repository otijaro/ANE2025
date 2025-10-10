// === CONFIG ===
const qsApi = new URLSearchParams(location.search).get('api');

let API_BASE = qsApi || (location.port === '5173' ? 'http://localhost:8000/api' : '/api');


if (API_BASE.endsWith('/')) API_BASE = API_BASE.slice(0, -1);


const elApi = document.getElementById("api-base");
if (elApi) elApi.textContent = API_BASE;

console.log('API_BASE =', API_BASE);
//document.getElementById("api-base")?.textContent = API_BASE;

// === STATE ===
let scene = null;              // JSON /scene
let showLines = true;          // toggle líneas
let kmToPx = 10;               // px por km (autocalibrado)
let dragState = null;          // { id, startKm:{x,y}, startPx:{x,y} }

// === DOM ===
const svg = document.getElementById("scene");
const statsEl = document.getElementById("stats");

document.getElementById("btn-refresh").addEventListener("click", init);
document.getElementById("btn-toggle-lines").addEventListener("click", () => {
  showLines = !showLines; render();
});
const toNum = v => parseFloat(String(v).replace(',', '.'));

// Form agregar FM
document.getElementById("fm-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.currentTarget);
  const payload = {
    nombre: fd.get("nombre"),
    x_km: toNum(fd.get("x_km")),
    y_km: toNum(fd.get("y_km")),
    h_km: toNum(fd.get("h_km")),
    f_MHz: toNum(fd.get("f_MHz")),
    p_kW: toNum(fd.get("p_kW")),
  };
  await postJSON("/entity/add/fm", payload);
  await init(); // recarga escena y stats
});

document.getElementById("btn-save").addEventListener("click", async () => {
  await postJSON("/scene/save", {});
  alert("Escena guardada en /data (contenedor) o DATA_DIR.");
});
document.getElementById("btn-load").addEventListener("click", async () => {
  await postJSON("/scene/load", {});
  await init();
});

// === API helpers ===
async function getJSON(path) {
  const url = `${API_BASE}${path}`;
  console.log('GET', url);
  const r = await fetch(url, { method: 'GET' });
  if (!r.ok) {
    const text = await r.text().catch(() => '');
    console.error('GET failed', url, r.status, text);
    throw new Error(`GET ${url} -> ${r.status}`);
  }
  return r.json();
}
async function postJSON(path, body) {
  const url = `${API_BASE}${path}`;
  console.log('POST', url, body);
  const r = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!r.ok) {
    const text = await r.text().catch(() => '');
    console.error('POST failed', url, r.status, text);
    throw new Error(`POST ${url} -> ${r.status}`);
  }
  return r.json();
}

// === INIT ===
async function init() {
  // escena + stats
  scene = await getJSON("/scene");
  const st = await getJSON("/stats");
  statsEl.textContent = prettyStats(st);

  // ajustar escala (km->px) al tamaño del SVG
  fitScale();
  render();
}

function fitScale() {
  const bbox = svg.getBoundingClientRect();
  const margin = 20;
  const pxW = Math.max(100, bbox.width - margin * 2);
  const pxH = Math.max(100, bbox.height - margin * 2);
  const kmW = scene.scene.ancho_km;
  const kmH = scene.scene.alto_km;
  kmToPx = Math.min(pxW / kmW, pxH / kmH);
}
function kmToScreen(x_km, y_km) {
  const h_km = scene.scene.alto_km;
  const x = x_km * kmToPx;
  const y = (h_km - y_km) * kmToPx; // invertir Y
  return { x, y };
}

// === RENDER ===
function render() {
  svg.innerHTML = "";

  const w = scene.scene.ancho_km * kmToPx;
  const h = scene.scene.alto_km * kmToPx;
  svg.setAttribute("viewBox", `0 0 ${w} ${h}`);

  const gGrid = el("g");
  const step = 5;
  for (let xk = 0; xk <= scene.scene.ancho_km; xk += step) {
    const x = xk * kmToPx;
    gGrid.appendChild(line(x, 0, x, h, "grid-line"));
  }
  for (let yk = 0; yk <= scene.scene.alto_km; yk += step) {
    const y = (scene.scene.alto_km - yk) * kmToPx;
    gGrid.appendChild(line(0, y, w, y, "grid-line"));
  }
  svg.appendChild(gGrid);

  const av = scene.entities.find(e => e.type === "Aircraft");
  const tower = scene.entities.find(e => e.type === "ControlTower");
  const fms = scene.entities.filter(e => e.type === "FMTransmitter");

  if (showLines && av) {
    const gLines = el("g");
    for (const fm of fms) {
      const a = kmToScreen(fm.x_km, fm.y_km);
      const b = kmToScreen(av.x_km, av.y_km);
      gLines.appendChild(line(a.x, a.y, b.x, b.y, "line-los"));
    }
    svg.appendChild(gLines);
  }

  for (const fm of fms) drawEntity(fm, "fm");
  if (tower) drawEntity(tower, "tower", 7, "Torre");
  if (av) drawEntity(av, "plane", 7, av.nombre || "Avión");
}

function drawEntity(ent, cls, r = 6, label = null) {
  const { x, y } = kmToScreen(ent.x_km, ent.y_km);
  const g = el("g");
  const c = el("circle", { cx: x, cy: y, r, class: `handle ${cls}` });
  c.addEventListener("pointerdown", (ev) => startDrag(ev, ent));
  g.appendChild(c);

  const name = label || ent.nombre || ent.id;
  const text = el("text", { x: x + 8, y: y - 8, class: "entity-label" }, document.createTextNode(name));
  g.appendChild(text);
  svg.appendChild(g);
}

// === DRAG ===
function startDrag(ev, ent) {
  ev.preventDefault();
  svg.setPointerCapture(ev.pointerId);
  const p = clientToSvg(ev.clientX, ev.clientY);
  dragState = { id: ent.id, startPx: p, startKm: { x: ent.x_km, y: ent.y_km } };
  svg.addEventListener("pointermove", onDrag);
  svg.addEventListener("pointerup", endDrag);
}
function onDrag(ev) {
  if (!dragState) return;
  const p = clientToSvg(ev.clientX, ev.clientY);
  const dx_px = p.x - dragState.startPx.x;
  const dy_px = p.y - dragState.startPx.y;
  const dx_km = dx_px / kmToPx;
  const dy_km = -dy_px / kmToPx;

  const newX = clamp(dragState.startKm.x + dx_km, 0, scene.scene.ancho_km);
  const newY = clamp(dragState.startKm.y + dy_km, 0, scene.scene.alto_km);

  const ent = scene.entities.find(e => e.id === dragState.id);
  if (ent) { ent.x_km = newX; ent.y_km = newY; render(); }
}
async function endDrag(ev) {
  svg.releasePointerCapture(ev.pointerId);
  svg.removeEventListener("pointermove", onDrag);
  svg.removeEventListener("pointerup", endDrag);
  if (!dragState) return;
  const ent = scene.entities.find(e => e.id === dragState.id);
  if (ent) {
    try {
      await postJSON("/entity/move", { id: ent.id, x_km: ent.x_km, y_km: ent.y_km });
      const st = await getJSON("/stats");
      statsEl.textContent = prettyStats(st);
    } catch (e) {
      console.error(e);
      alert("Error al mover entidad en servidor.");
    }
  }
  dragState = null;
}
function clientToSvg(cx, cy) {
  const pt = svg.createSVGPoint();
  pt.x = cx; pt.y = cy;
  const m = svg.getScreenCTM().inverse();
  return pt.matrixTransform(m);
}

// === utils render ===
function el(tag, attrs = {}, child = null) {
  const n = document.createElementNS("http://www.w3.org/2000/svg", tag);
  for (const [k, v] of Object.entries(attrs)) n.setAttribute(k, v);
  if (child) n.appendChild(child);
  return n;
}
function line(x1, y1, x2, y2, cls) { return el("line", { x1, y1, x2, y2, class: cls }); }
function clamp(v, lo, hi) { return Math.max(lo, Math.min(hi, v)); }

function prettyStats(st) {
  if (!st || !st.count) return "No hay emisoras.";
  const lines = [];
  lines.push(`N° emisoras: ${st.count}`);
  lines.push(`Potencia total: ${st.p_total_kW?.toFixed(2)} kW`);
  lines.push(`FSPL min/avg/max (FM→Avión): ${st.fspl_min?.toFixed(2)} / ${st.fspl_avg?.toFixed(2)} / ${st.fspl_max?.toFixed(2)} dB`);
  if (st.best_fm) lines.push(`Mejor FM→Avión: ${st.best_fm.nombre} (d=${st.best_fm.d_km?.toFixed(2)} km, FSPL=${st.best_fm.fspl_dB?.toFixed(2)} dB)`);
  return lines.join("\n");
}

// === arranque ===
(async function boot() {
  try { await init(); }
  catch (err) {
    console.error('boot error', err);
    if (statsEl) statsEl.textContent = "Error al iniciar (ver consola)";
  }
})();
