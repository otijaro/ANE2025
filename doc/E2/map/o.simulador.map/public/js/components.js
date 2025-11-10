import { map, layerByType, state, SKCG, LA_POPA } from './map.js';
import { iconFor } from './icons.js';
import { API_BASE } from './map.js';
import { buildFilterCurve, selectedFilterId } from './filters.js';
import { showInterferenceModal } from './modal.js';


const listEl = document.getElementById('list');
const rxSelect  = document.getElementById('rxSelect');
const txSelect  = document.getElementById('txSelect');
const rxSelect2 = document.getElementById('rxSelect2');

export function addMarker(o){
  const m = L.marker([o.lat, o.lon], { draggable: true, icon: iconFor(o.tipo, o.nombre, o.heading_deg||0) });
  m.addTo(layerByType(o.tipo));
  m.on('dragend', (e)=> {
    const ll = e.target.getLatLng();
    o.lat = ll.lat; o.lon = ll.lng;
    renderList(); 
  });
  m.on('click', ()=> map.setView([o.lat, o.lon], Math.max(map.getZoom(), 14)));
  m.on('dblclick', async ()=> {
    if(o.tipo!=='avion') return;
    const rxFreq = parseFloat(document.getElementById('fMHz').value) || 118.1;
    const rxAir = { ...o, tipo:'receptor', frecuencia_MHz: rxFreq };
    const txs = state.components.filter(x=>x.tipo!=='receptor' && x.id!==o.id && x.potencia_dBm!=null && x.frecuencia_MHz!=null);
    const window_kHz = parseFloat(document.getElementById('winKhz').value)||500;
    const max_order  = parseInt(document.getElementById('ordMax').value)||3;
    const rxObj = components.find(c => c.id === rx_id);
    const f_rx  = rxObj?.f_MHz || 118.1;
    const filter_rejection_dB = buildFilterCurve(f_rx);

    //const filter_rejection_dB = buildFilterCurve(rxFreq);
    const payload = { receiver: rxAir, transmitters: txs, max_order, window_kHz, filter_rejection_dB };

    const r = await fetch(`${API_BASE}/radio/interference`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const data = await r.json();
    showInterferenceModal(data, 'A bordo — Interferencias');
  });
  state.markers[o.id] = m;
}

export function moveMarkerToLayer(o){
  const m = state.markers[o.id]; if(!m) return;
  Object.values(layerByType).forEach(()=>{});
  // quitar de todas:
  [ 'torre','antena','avion','receptor' ].forEach(k=>{
    try { layerByType(k).removeLayer(m); } catch(_){}
  });
  m.setIcon(iconFor(o.tipo, o.nombre, o.heading_deg||0));
  m.addTo(layerByType(o.tipo));
}

export function renderList(){
  listEl.innerHTML = '';
  state.components.forEach(o=>{
    const div = document.createElement('div'); div.className = 'item';
    div.innerHTML = `
      <div style="display:flex;justify-content:space-between;align-items:center">
        <strong>${o.nombre}</strong>
        <select data-k="tipo">
          <option ${o.tipo==='torre'?'selected':''}>torre</option>
          <option ${o.tipo==='antena'?'selected':''}>antena</option>
          <option ${o.tipo==='avion'?'selected':''}>avion</option>
          <option ${o.tipo==='receptor'?'selected':''}>receptor</option>
        </select>
      </div>
      <label>Nombre</label><input data-k="nombre" value="${o.nombre}">
      <label>Lat</label><input data-k="lat" type="number" step="0.000001" value="${o.lat}">
      <label>Lon</label><input data-k="lon" type="number" step="0.000001" value="${o.lon}">
      <label>Alt terreno (m)</label><input data-k="alt_terreno_m" type="number" step="0.1" value="${o.alt_terreno_m}">
      <label>Alt sobre terreno (m)</label><input data-k="alt_sobre_terreno_m" type="number" step="0.1" value="${o.alt_sobre_terreno_m}">
      <label>Frecuencia (MHz)</label><input data-k="frecuencia_MHz" type="number" step="0.001" value="${o.frecuencia_MHz??''}">
      <label>Potencia (dBm)</label><input data-k="potencia_dBm" type="number" step="0.1" value="${o.potencia_dBm??''}">
      ${o.tipo==='avion' ? `<label>Rumbo (°)</label><input data-k="heading_deg" type="number" min="0" max="359" step="1" value="${o.heading_deg ?? 0}">` : ''}
      <div style="display:flex;gap:6px;margin-top:6px">
        <button class="btn" data-act="focus">Enfocar</button>
        <button class="btn" data-act="del" style="border-color:#fecaca">Eliminar</button>
      </div>
    `;
    div.querySelectorAll('input,select').forEach(inp=>{
      inp.onchange = (e)=>{
        const k = e.target.dataset.k;
        let v = e.target.value;
        if(['lat','lon','alt_terreno_m','alt_sobre_terreno_m','frecuencia_MHz','potencia_dBm','heading_deg'].includes(k)) v = parseFloat(v);
        o[k] = v;
        const m = state.markers[o.id];
        if(m){ m.setLatLng([o.lat, o.lon]); m.setIcon(iconFor(o.tipo, o.nombre, o.heading_deg||0)); moveMarkerToLayer(o); }
        syncSelectors();
      };
    });
    div.querySelector('[data-act="focus"]').onclick = ()=> map.setView([o.lat, o.lon], 15);
    div.querySelector('[data-act="del"]').onclick = ()=>{
      state.components = state.components.filter(x=>x.id!==o.id);
      const m = state.markers[o.id];
      if(m){ ['torre','antena','avion','receptor'].forEach(k=>{ try{ layerByType(k).removeLayer(m);}catch(_){}}); delete state.markers[o.id]; }
      renderList(); syncSelectors();
    };
    listEl.appendChild(div);
  });
}

export function syncSelectors(){
  // lee valores UI
  const rx_id = (document.getElementById('rxSelect')?.value || '').trim();
  const window_kHz = parseFloat(document.getElementById('winKhz').value) || 500;  // 👈 K mayúscula
  const max_order  = parseInt(document.getElementById('ordMax').value) || 3;      // 👈 max_order
  const filter_id  = selectedFilterId();
  const components = (window.__osim_export && window.__osim_export()) || [];

  // payload alineado al modelo del back
  const payload = { rx_id, window_kHz, max_order, filter_id, components };
  console.log('[Interferencia] payload →', payload);

  const rxId = rxSelect.value; rxSelect.innerHTML='';
  const rxList = state.components.filter(o=>o.tipo==='receptor'); 
  rxList.forEach(o=>{ const opt = document.createElement('option'); opt.value=o.id; opt.textContent=o.nombre; rxSelect.appendChild(opt); });
  if (rxId) rxSelect.value = rxId;

  const txId = txSelect.value, rx2Id = rxSelect2.value; txSelect.innerHTML=''; rxSelect2.innerHTML='';
  const txCandidates = state.components.filter(o=>o.tipo!=='receptor');
  txCandidates.forEach(o=>{ const opt=document.createElement('option'); opt.value=o.id; opt.textContent=o.nombre; txSelect.appendChild(opt); });
  rxList.forEach(o=>{ const opt=document.createElement('option'); opt.value=o.id; opt.textContent=o.nombre; rxSelect2.appendChild(opt); });
  if (txId) txSelect.value = txId; if (rx2Id) rxSelect2.value = rx2Id;
}

export function seedCartagena(){
  const TWR = { id:'twr1', nombre:'Torre SKCG', tipo:'torre', lat:10.4452, lon:-75.5138, alt_terreno_m:3,  alt_sobre_terreno_m:30,  frecuencia_MHz:118.1, potencia_dBm:50 };
  const ANT = { id:'fm1',  nombre:'FM 99.1',    tipo:'antena',lat:10.44,   lon:-75.50,   alt_terreno_m:10, alt_sobre_terreno_m:60,  frecuencia_MHz: 99.1,  potencia_dBm: 70 };
  const FM2 = { id:'fm2', nombre:'FM 101.3 (La Popa)', tipo:'antena', lat:LA_POPA.lat+0.001,   lon:LA_POPA.lon,   alt_terreno_m:140, alt_sobre_terreno_m:50, frecuencia_MHz:101.3, potencia_dBm:68 };
  const FM3 = { id:'fm3', nombre:'FM 92.7 (La Popa)',  tipo:'antena', lat:LA_POPA.lat-0.0008, lon:LA_POPA.lon,   alt_terreno_m:140, alt_sobre_terreno_m:45, frecuencia_MHz:92.7,  potencia_dBm:65 };
  const AC1 = { id:'av1',  nombre:'Avión', tipo:'avion',  lat:10.455, lon:-75.51, alt_terreno_m:0, alt_sobre_terreno_m:300, frecuencia_MHz:null, potencia_dBm:null, heading_deg:190 };
  const RX  = { id:'rx1',  nombre:'VHF COM RX',  tipo:'receptor', lat:10.448, lon:-75.515, alt_terreno_m:3, alt_sobre_terreno_m:15, frecuencia_MHz:118.1 };

  state.components = [TWR, ANT, FM2, FM3, AC1, RX];
  state.components.forEach(addMarker);
  renderList();
  syncSelectors();

  // Botones de la UI
  document.getElementById('addBtn').onclick = ()=>{
    alert('En este módulo agregaremos un panel flotante para creación guiada. Por ahora, crea desde JSON o duplica uno en la lista.');
  };
  document.getElementById('saveBtn').onclick = ()=>{
    const blob = new Blob([JSON.stringify({objetos:state.components}, null, 2)], {type:'application/json'});
    const a = document.createElement('a'); a.href = URL.createObjectURL(blob); a.download = 'escenario.json'; a.click(); URL.revokeObjectURL(a.href);
  };
  document.getElementById('loadBtn').onclick = ()=> document.getElementById('fileInput').click();
  document.getElementById('fileInput').onchange = async (e)=>{
    const f = e.target.files?.[0]; if(!f) return;
    const text = await f.text(); const data = JSON.parse(text);
    state.components = data.objetos || [];
    Object.values(state.markers).forEach(m=>{ ['torre','antena','avion','receptor'].forEach(k=>{ try{ layerByType(k).removeLayer(m);}catch(_){}}); });
    for(const k in state.markers) delete state.markers[k];
    state.components.forEach(addMarker); renderList(); syncSelectors(); e.target.value='';
  };

  document.getElementById('saveSrv').onclick = async ()=>{
    const id = prompt('ID del escenario:', 'esc1'); if(!id) return;
    const name = prompt('Nombre del escenario:', 'Cartagena Popa'); if(!name) return;
    const payload = { id, name, owner_id:'demo', objetos: state.components };
    const r = await fetch(`${API_BASE}/scenario`, {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(payload)});
    const data = await r.json(); alert('Guardado: ' + data.name);
  };
  document.getElementById('loadSrv').onclick = async ()=>{
    const id = prompt('ID a cargar:', 'esc1'); if(!id) return;
    const r = await fetch(`${API_BASE}/scenario/${encodeURIComponent(id)}`);
    if(!r.ok){ alert('No existe'); return; }
    const data = await r.json();
    state.components = data.objetos || [];
    Object.values(state.markers).forEach(m=>{ ['torre','antena','avion','receptor'].forEach(k=>{ try{ layerByType(k).removeLayer(m);}catch(_){}}); });
    for(const k in state.markers) delete state.markers[k];
    state.components.forEach(addMarker); renderList(); syncSelectors();
  };

  document.getElementById('centerSkcgBtn').onclick = ()=> map.setView([SKCG.lat, SKCG.lon], SKCG.zoom);
}
// helper global para otros módulos (LOS, rutas)
window.__osim_findById = (id)=> state.components.find(o=>o.id===id);
window.__osim_markerFor = (id)=> state.markers[id];
window.__osim_iconFor   = (o)=> iconFor(o.tipo, o.nombre, o.heading_deg||0);
window.__osim_findPlane = ()=> state.components.find(o=>o.tipo==='avion');

function kindForBackend(o){
  if (o.tipo === 'receptor') return 'rx';
  const f = Number(o.frecuencia_MHz);
  // Heurística: FM si cae ~87–108 MHz, VHF COM si ~118–137 MHz, si no, tx_gen
  if (f >= 87 && f <= 108) return 'tx_fm';
  if (f >= 118 && f <= 137) return 'tx_vhf';
  return 'tx_gen';
}

function exportComponentsForBackend(){
  return (state.components || []).map(o => ({
    id: o.id,
    // --- esquema nuevo (sigue igual)
    kind: kindForBackend(o),
    lat: o.lat,
    lon: o.lon,
    h_m: (Number(o.alt_terreno_m) || 0) + (Number(o.alt_sobre_terreno_m) || 0),
    f_MHz: (o.frecuencia_MHz != null ? Number(o.frecuencia_MHz) : null),
    erp_dBm: (o.potencia_dBm  != null ? Number(o.potencia_dBm)  : null),
    name: o.nombre,

    // --- compatibilidad LEGACY que el back aún puede estar usando
    nombre: o.nombre,
    tipo:   o.tipo,
    // claves críticas en español:
    frecuencia_MHz: (o.frecuencia_MHz != null ? Number(o.frecuencia_MHz) : null),
    potencia_dBm:   (o.potencia_dBm  != null ? Number(o.potencia_dBm)  : null),
    alt_terreno_m:        (Number(o.alt_terreno_m)        || 0),
    alt_sobre_terreno_m:  (Number(o.alt_sobre_terreno_m)  || 0)
  }));
}


// helper global para el handler del botón "Calcular"
window.__osim_export = () => exportComponentsForBackend();
