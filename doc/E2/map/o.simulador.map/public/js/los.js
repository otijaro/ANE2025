import { API_BASE } from './map.js';

export function initLOS(){
  const btn = document.getElementById('losBtn');
  if(!btn) return;

  btn.onclick = async ()=>{
    const txSel = document.getElementById('txSelect');
    const rxSel = document.getElementById('rxSelect2');
    if(!txSel.value || !rxSel.value){ alert('Selecciona TX y RX'); return; }

    // Recogemos objetos desde el DOM (components los gestiona components.js)
    const tx = window.__osim_findById(txSel.value);
    const rx = window.__osim_findById(rxSel.value);
    if(!tx || !rx){ alert('TX/RX no válidos'); return; }

    const frecuencia_MHz = parseFloat(document.getElementById('fMHz').value)||118.1;
    const k_factor = parseFloat(document.getElementById('kFactor').value)||1.33;
    const payload = { tx, rx, frecuencia_MHz, k_factor, samples: 128 };
    try {
      const r = await fetch('/radio/los', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // credentials: 'include', // solo si usas sesión/cookies
        body: JSON.stringify(payload),
      });
      if (!r.ok) throw new Error(`HTTP ${r.status}`);
      const data = await r.json();
      console.log('OK', data);
      drawProfile(data);
    } catch (e) {
      console.error('[LOS] fetch falló:', e);
      alert('No se pudo conectar con /radio/los. Revisa bloqueadores/CORS/HTTPS.');
      return;
    }    
  };
}

// Dibuja SVG del perfil
export function drawProfile(data){
  const svg = document.getElementById('profileSvg');
  const W=800, H=240; svg.setAttribute('viewBox',`0 0 ${W} ${H}`); svg.innerHTML='';
  const padL=40, padR=10, padT=10, padB=30;

  const xs = (d)=> padL + (d/data.distance_m)*(W-padL-padR);
  const elevs = data.profile.map(p=>p.elev_m);
  const rays  = data.profile.map(p=>p.ray_h_m);
  const minV = Math.min(...elevs, ...rays);
  const maxV = Math.max(...elevs, ...rays);
  const ys = (v)=> padT + (1 - (v-minV)/(maxV-minV+1e-6))*(H-padT-padB);

  let dPath = '';
  data.profile.forEach((p,i)=>{ dPath += (i? 'L':'M') + xs(p.d_m) + ',' + ys(p.elev_m);});
  const ground = document.createElementNS('http://www.w3.org/2000/svg','path');
  ground.setAttribute('d', dPath); ground.setAttribute('stroke','#6b7280'); ground.setAttribute('fill','none'); ground.setAttribute('stroke-width','1.5'); svg.appendChild(ground);

  let rPath = '';
  data.profile.forEach((p,i)=>{ rPath += (i? 'L':'M') + xs(p.d_m) + ',' + ys(p.ray_h_m);});
  const ray = document.createElementNS('http://www.w3.org/2000/svg','path');
  ray.setAttribute('d', rPath); ray.setAttribute('stroke','#2563eb'); ray.setAttribute('fill','none'); ray.setAttribute('stroke-width','2'); svg.appendChild(ray);

  let fTop='', fBot='';
  data.profile.forEach((p,i)=>{ fTop += (i? 'L':'M') + xs(p.d_m) + ',' + ys(p.ray_h_m + p.f1_m); });
  [...data.profile].reverse().forEach((p,i)=>{ fBot += (i? 'L':'L') + xs(p.d_m) + ',' + ys(p.ray_h_m - p.f1_m); });
  const fres = document.createElementNS('http://www.w3.org/2000/svg','path');
  fres.setAttribute('d', fTop + fBot + 'Z'); fres.setAttribute('fill','rgba(37,99,235,0.15)'); fres.setAttribute('stroke','none'); svg.appendChild(fres);

  const axis = document.createElementNS('http://www.w3.org/2000/svg','line'); axis.setAttribute('x1',padL); axis.setAttribute('x2',W-padR); axis.setAttribute('y1',H-padB); axis.setAttribute('y2',H-padB); axis.setAttribute('stroke','#e5e7eb'); svg.appendChild(axis);
  const tick = document.createElementNS('http://www.w3.org/2000/svg','text'); tick.setAttribute('x',W-padR-40); tick.setAttribute('y',H-10); tick.setAttribute('fill','#111827'); tick.setAttribute('font-size','12'); tick.textContent = (data.distance_m/1000).toFixed(2)+' km'; svg.appendChild(tick);

  const info = document.getElementById('losInfo');
  info.innerHTML = `<b>LOS:</b> ${data.has_los ? 'Sí' : 'No'} · <b>FSPL:</b> ${data.fspl_dB.toFixed(2)} dB · <b>Peor despeje Fresnel:</b> ${data.fresnel_clearance_min_pct.toFixed(1)}% · <b>Peor clearance:</b> ${data.clearance_worst_point_m.toFixed(2)} m · <b>Elevación:</b> ${data.source}`;
}
