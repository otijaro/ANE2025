import { API_BASE, map, state, LA_POPA } from './map.js';
import { buildFilterCurve } from './filters.js';

// Canvas y helpers
const heatCanvas = document.getElementById('heatCanvas');
const heatCtx = heatCanvas.getContext('2d', { willReadFrequently: true });

export function resizeHeatCanvas(){
  const sz = map.getSize();
  heatCanvas.width  = Math.max(1, sz.x);
  heatCanvas.height = Math.max(1, sz.y);
}

function dbmToAlpha(dbm){
  const cl = Math.max(-130, Math.min(-60, dbm));
  const t = (cl + 130) / 70;
  const gamma = 0.9;
  return Math.pow(t, gamma);
}

export function drawHeatCanvas(points, params = { radiusPx: 26, maxAlpha: 0.65 }){
  resizeHeatCanvas();
  if (heatCanvas.width === 0 || heatCanvas.height === 0) {
    requestAnimationFrame(()=> drawHeatCanvas(points, params));
    return;
  }
  heatCtx.clearRect(0,0,heatCanvas.width, heatCanvas.height);

  const r = params.radiusPx;
  const gradCanvas = document.createElement('canvas');
  gradCanvas.width = gradCanvas.height = r*2;
  const gctx = gradCanvas.getContext('2d');
  const g = gctx.createRadialGradient(r,r,0, r,r,r);
  g.addColorStop(0, 'rgba(0,0,0,1)');
  g.addColorStop(1, 'rgba(0,0,0,0)');
  gctx.fillStyle = g; gctx.fillRect(0,0,gradCanvas.width, gradCanvas.height);

  heatCtx.globalCompositeOperation = 'source-over';
  for(const pt of points){
    const p = map.latLngToContainerPoint([pt.lat, pt.lon]);
    heatCtx.globalAlpha = dbmToAlpha(pt.score_dBm) * params.maxAlpha;
    heatCtx.drawImage(gradCanvas, Math.round(p.x - r), Math.round(p.y - r));
  }

  const img = heatCtx.getImageData(0,0,heatCanvas.width,heatCanvas.height);
  const d = img.data;
  for(let i=0;i<d.length;i+=4){
    const a = d[i+3]/255; if(a<=0) continue;
    const col = a<0.25 ? [34,197,94]
            : a<0.5  ? [132,204,22]
            : a<0.7  ? [245,158,11]
            : a<0.85 ? [249,115,22]
            :          [239,68,68];
    d[i]=col[0]; d[i+1]=col[1]; d[i+2]=col[2]; d[i+3]=Math.min(255, Math.round(a*255));
  }
  heatCtx.putImageData(img,0,0);

  state.lastHeatPoints = points;
  state.lastHeatParams = params;
}

export function initHeatmap(){
  window.addEventListener('resize', ()=>{ if(state.lastHeatPoints) drawHeatCanvas(state.lastHeatPoints, state.lastHeatParams); });
  map.on('moveend zoomend', ()=>{ if(state.lastHeatPoints) drawHeatCanvas(state.lastHeatPoints, state.lastHeatParams); });
  map.whenReady(()=> resizeHeatCanvas());

  const btn = document.getElementById('hmBtn');
  const opacity = document.getElementById('hmOpacity');
  const opacityVal = document.getElementById('hmOpacityVal');
  const clearBtn = document.getElementById('hmClear');

  if (opacity && opacityVal){
    opacityVal.textContent = opacity.value;
    opacity.oninput = ()=>{
      opacityVal.textContent = opacity.value;
      if(state.lastHeatPoints && state.lastHeatParams){
        drawHeatCanvas(state.lastHeatPoints, { ...state.lastHeatParams, maxAlpha: parseFloat(opacity.value) || 0.65 });
      }
    };
  }

  if (clearBtn){
    clearBtn.onclick = ()=>{
      heatCtx.clearRect(0,0,heatCanvas.width,heatCanvas.height);
      state.lastHeatPoints = null;
      state.lastHeatParams = null;
    };
  }

  if (btn){
    btn.onclick = async ()=>{
      const txs = state.components.filter(o => (o.tipo==='antena' || o.tipo==='torre') && o.potencia_dBm!=null && o.frecuencia_MHz!=null);
      const body = {
        center_lat: LA_POPA.lat,
        center_lon: LA_POPA.lon,
        radius_km: parseFloat(document.getElementById('hmRad').value)||3,
        step_m: parseInt(document.getElementById('hmStep').value)||200,
        f_rx_MHz: parseFloat(document.getElementById('hmFRx').value)||118.1,
        window_kHz: parseFloat(document.getElementById('hmWin').value)||150,
        transmitters: txs,
        filter_rejection_dB: buildFilterCurve(parseFloat(document.getElementById('hmFRx').value)||118.1)
      };
      const r = await fetch(`${API_BASE}/radio/heatmap`, { method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify(body) });
      if(!r.ok){
        const txt = await r.text(); alert('Error heatmap: '+txt); return;
      }
      const data = await r.json();
      const maxA = parseFloat((opacity||{}).value) || 0.65;
      drawHeatCanvas(data.points, {radiusPx: 26, maxAlpha: maxA});
    };
  }
}
