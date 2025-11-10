// Punto único de arranque del front
// Carga módulos y deja todo inicializado en el orden correcto.

import { initMap } from './map.js';
import { seedCartagena } from './components.js';
import { initLOS } from './los.js';
import { initRoutes } from './routes.js';
import { initHeatmap } from './heatmap.js';
import { initModal, showInterferenceModal } from './modal.js';
import { loadFilterPresets, selectedFilterId, buildFilterCurve } from './filters.js';



// Permite configurar el backend sin tocar código (opcional)
window.API_BASE = window.API_BASE || localStorage.getItem('API_BASE') || 'http://127.0.0.1:8000' || 'http://10.1.51.193:8000/';


window.addEventListener('DOMContentLoaded', () => {
  // 1) Mapa y capas
  initMap();

  // 2) UI secundaria (modal, presets)
  //initModal();

  console.info('[app] DOM listo');
    initModal();
    loadFilterPresets();
    const calcBtn = document.getElementById('calcBtn');
    if (!calcBtn) {
      console.warn('[app] No encontré #calcBtn');
      return;
    }

  document.getElementById('calcBtn').onclick = async () => {
  console.log('[Interferencia] click recibido');

  const rx_id = (document.getElementById('rxSelect')?.value || '').trim();
  if (!rx_id) { alert('Selecciona un receptor (RX)'); return; }

  // Exporta todo para poder separar RX vs TX
  const components = (window.__osim_export && window.__osim_export()) || [];
  console.log('[Interferencia] componentes →', components.length, components);
  if (!components.length) {
    alert('Agrega al menos 1 RX y 1–2 TX en “Componentes” antes de calcular.');
    return;
  }

  // --- separar según lo que pide el backend ---
  const receiver = components.find(c => c.id === rx_id && c.kind === 'rx');
  if (!receiver) { alert('El RX seleccionado no existe en la lista de componentes'); return; }

  // Solo TX válidos (con frecuencia y potencia definidas)
  const transmitters = components.filter(c =>
    c.kind !== 'rx' && c.f_MHz != null && c.erp_dBm != null
  );

  if (!transmitters.length) { alert('Necesitas al menos un transmisor con f y potencia'); return; }

  // Parámetros con nombres EXACTOS del back
  const window_kHz = parseFloat(document.getElementById('winKhz').value) || 500;
  const max_order  = parseInt(document.getElementById('ordMax').value) || 3;

  // Filtro: id + curva (por compatibilidad hacia atrás)
  const filter_id  = selectedFilterId();
  const f_rx_MHz   = receiver.f_MHz ?? 118.1;
  const filter_rejection_dB = buildFilterCurve(f_rx_MHz);

  const payload = { receiver, transmitters, window_kHz, max_order, filter_id, filter_rejection_dB };
  console.log('[Interferencia] payload →', payload);

  try {
    const r = await fetch(`${window.API_BASE}/radio/interference`, {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify(payload)
    });

    if (!r.ok) {
      const errBody = await r.json().catch(()=>null);
      console.log('[Interferencia] HTTP', r.status, errBody);
      if (errBody?.detail) {
        console.table(errBody.detail.map(d => ({
          loc: Array.isArray(d.loc) ? d.loc.join('.') : d.loc, msg: d.msg, type: d.type
        })));
      }
      throw new Error(`HTTP ${r.status}`);
    }

    const data = await r.json();

    // Normaliza si el back devuelve array (p.ej., FSPL sueltos)
    const resp = Array.isArray(data)
      ? { fspl_tx_rx: data, items: [], rx_power_sum_dBm: null }
      : data;

    // (A) Pinta SIEMPRE el objeto en el <pre id="result">
    const pre = document.getElementById('result');
    if (pre) pre.textContent = JSON.stringify(resp, null, 2);

    // (B) Abre el modal sólo si hay items para tabla
    if (resp?.items?.length) {
      try { showInterferenceModal(resp, 'Interferencias — cálculo'); }
      catch (e) { console.warn('[Interferencia] showInterferenceModal:', e, resp); }
    } else {
      console.info('[Interferencia] sin items; revisa ventana/filtro.');
    }

    console.log('[Interferencia] OK', resp);

  } catch (e) {
    console.error('[Interferencia] error:', e);
    alert('No se pudo calcular interferencia. Revisa consola y backend.');
  }
};




  // 3) Semilla de componentes (Cartagena + La Popa)
  seedCartagena();

  // 4) Módulos funcionales
  initLOS();
  initRoutes();
  initHeatmap();

  console.log('[O.simulador_map] Front inicializado');
});
