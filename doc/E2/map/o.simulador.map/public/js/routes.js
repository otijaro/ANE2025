import { map, state } from './map.js';

// Proyección a segmento más cercano de las aerovías
function projectPointOnSegment(p, a, b){
  const toXY = (pt, a0)=>{
    const R = 6371000, p2 = Math.PI/180;
    const x = (pt[1] - a0[1]) * Math.cos((pt[0]+a0[0]) * p2/2) * p2 * R;
    const y = (pt[0] - a0[0]) * p2 * R;
    return [x,y];
  };
  const pxy = toXY(p, a), axy=[0,0], bxy=toXY(b, a);
  const ab = [bxy[0]-axy[0], bxy[1]-axy[1]];
  const ap = [pxy[0]-axy[0], pxy[1]-axy[1]];
  const ab2 = ab[0]*ab[0]+ab[1]*ab[1];
  const t = Math.max(0, Math.min(1, (ap[0]*ab[0]+ap[1]*ab[1])/(ab2||1)));
  const projXY = [axy[0]+ab[0]*t, axy[1]+ab[1]*t];

  const R = 6371000, p2 = Math.PI/180;
  const dLat = projXY[1]/R*(180/Math.PI);
  const dLon = projXY[0]/(R*Math.cos((a[0]) * p2))*(180/Math.PI);
  return [a[0]+dLat, a[1]+dLon];
}

function snapToAirways(lat, lon){
  if(!state.airways.length) return [lat,lon];
  let best = null, bestD2 = 1e18;
  const p = [lat,lon];
  for(const line of state.airways){
    for(let i=0;i<line.length-1;i++){
      const q = projectPointOnSegment(p, line[i], line[i+1]);
      const px = map.latLngToContainerPoint(p);
      const qx = map.latLngToContainerPoint(q);
      const d2 = (px.x-qx.x)**2 + (px.y-qx.y)**2;
      if(d2 < bestD2){ bestD2 = d2; best = q; }
    }
  }
  return best || [lat,lon];
}

export function headingFrom(a,b){
  const toRad = d=>d*Math.PI/180, toDeg = r=>r*180/Math.PI;
  const lat1=toRad(a[0]), lon1=toRad(a[1]), lat2=toRad(b[0]), lon2=toRad(b[1]);
  const dLon = lon2-lon1;
  const y = Math.sin(dLon)*Math.cos(lat2);
  const x = Math.cos(lat1)*Math.sin(lat2)-Math.sin(lat1)*Math.cos(lat2)*Math.cos(dLon);
  let brng = (toDeg(Math.atan2(y,x))+360)%360;
  brng = (brng - 90 + 360)%360; // nuestro SVG apunta al Este
  return brng;
}

export function initRoutes(){
  let route = [];
  let routePolyline = null;
  let timer = null;
  let idx = 0;

  const airwayInput = document.getElementById('airwayFile');
  const routeInput  = document.getElementById('routeFile');
  const snapChk     = document.getElementById('snapAirway');
  const playBtn     = document.getElementById('routePlay');
  const pauseBtn    = document.getElementById('routePause');

  airwayInput.onchange = async (e)=>{
    const f = e.target.files?.[0]; if(!f) return;
    const text = await f.text(); const gj = JSON.parse(text);
    state.airways = []; state.airwaysLayer.clearLayers();
    (gj.features||[]).forEach(feat=>{
      const coords = (feat.geometry && feat.geometry.type==='LineString') ? feat.geometry.coordinates : null;
      if(!coords) return;
      const line = coords.map(([lon,lat])=>[lat,lon]);
      state.airways.push(line);
      L.polyline(line, {color:'#0ea5a3', weight:2, dashArray:'4 4'}).addTo(state.airwaysLayer);
    });
    const b = state.airwaysLayer.getBounds();
    if(b && b.isValid()) map.fitBounds(b.pad(0.2));
  };

  function parseCSV(text){
    const lines = text.split(/\r?\n/).filter(l=>l.trim().length);
    const out = [];
    for(const ln of lines){
      const [a,b] = ln.split(',').map(s=>s.trim());
      const lat = parseFloat(a), lon = parseFloat(b);
      if(Number.isFinite(lat) && Number.isFinite(lon)) out.push([lat,lon]);
    }
    return out;
  }
  function parseGPX(text){
    const pts = [...text.matchAll(/<trkpt[^>]*?lat=\"([^\"]+)\"[^>]*?lon=\"([^\"]+)\"/g)];
    return pts.map(m=>[parseFloat(m[1]), parseFloat(m[2])]).filter(([a,b])=>Number.isFinite(a)&&Number.isFinite(b));
  }

  routeInput.onchange = async (e)=>{
    const f = e.target.files?.[0]; if(!f) return;
    const text = await f.text();
    route = f.name.toLowerCase().endsWith('.gpx') ? parseGPX(text) : parseCSV(text);
    if(route.length<2){ alert('Ruta inválida o muy corta'); return; }
    if(routePolyline){ map.removeLayer(routePolyline); routePolyline=null; }
    routePolyline = L.polyline(route, {color:'#2563eb'}).addTo(map);
    map.fitBounds(routePolyline.getBounds().pad(0.2));
    idx = 0;
  };

  playBtn.onclick = ()=>{
    if(!route || route.length<2){ alert('Carga una ruta GPX/CSV'); return; }
    clearInterval(timer);
    timer = setInterval(()=>{
      const plane = window.__osim_findById('av1') || (window.__osim_findPlane && window.__osim_findPlane());
      if(!plane){ alert('Crea un componente tipo "avion"'); clearInterval(timer); return; }

      const sp = Math.max(0.5, parseFloat(document.getElementById('routeSpeed').value)||1);
      idx = Math.min(route.length-2, idx + Math.max(1, Math.round(sp)));
      const A = route[idx], B = route[idx+1];
      let lat=A[0], lon=A[1];
      if(snapChk.checked){ [lat,lon] = snapToAirways(lat, lon); }

      plane.lat = lat; plane.lon = lon;
      plane.heading_deg = headingFrom(A,B);

      const m = window.__osim_markerFor && window.__osim_markerFor(plane.id);
      if(m){ m.setLatLng([plane.lat, plane.lon]); m.setIcon(window.__osim_iconFor(plane)); }

      // Triggers opcionales (LOS/INT en vivo) ya los haces en tu index si quieres

      if(idx >= route.length-2){ clearInterval(timer); }
    }, 600);
  };

  pauseBtn.onclick = ()=> clearInterval(timer);
}
