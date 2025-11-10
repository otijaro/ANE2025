import { API_BASE } from './map.js';

export function initLOS(){
  const btn = document.getElementById('losBtn');
  if(!btn) return;
    btn.onclick = async () => {
    // Ejemplo de payload: ajusta a tu LOSRequest real
    const req = {
        lat_tx: Number(document.querySelector('#lat_tx').value),
        lon_tx: Number(document.querySelector('#lon_tx').value),
        lat_rx: Number(document.querySelector('#lat_rx').value),
        lon_rx: Number(document.querySelector('#lon_rx').value),
        freq_mhz: Number(document.querySelector('#freq_mhz').value),
        ptx_dbm: Number(document.querySelector('#ptx_dbm').value),
        // ...cualquier otro campo requerido por LOSRequest
    };

    try {
        const res = await fetch('http://127.0.0.1:8000/radio/los', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        // Si usas cookies/autenticación: credentials: 'include',
        body: JSON.stringify(req),
        });

        if (!res.ok) {
        // Intenta leer texto para ver 404/422/500 con detalle
        const txt = await res.text();
        throw new Error(`HTTP ${res.status} — ${txt.slice(0, 500)}`);
        }

        const r = await res.json();
        console.log('[LOS] ok:', r);
        // TODO: pinta r en tu UI
    } catch (e) {
        console.error('[LOS] fetch falló:', e);
        alert('No se pudo obtener LOS. Revisa payload y que el backend esté en POST /radio/los.');
        return; // evita usar r después de un error
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
