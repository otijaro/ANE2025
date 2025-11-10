// Presets en IDs canónicos y carga del <select id="filterPreset">
export const FILTER_PRESETS_BY_ID = {
  cavity_8p: {
    label: "Cavity 8 polos (VHF COM)",
    data: { "0":0,"12.5":12,"25":25,"50":48,"75":60,"100":72,"150":85,"200":95,"300":110,"500":120 }
  },
  bpf_200k: {
    label: "BPF comercial (ancho 200 kHz)",
    data: { "0":0,"25":8,"50":14,"100":24,"150":35,"200":45,"300":60,"500":80 }
  },
  notch_fm_100: {
    label: "Notch FM (centro 100 MHz)",
    // el backend reconoce {"center_MHz", "curve":{...}} cuando es notch
    data: { center_MHz: 100.0, curve: {"0":80,"50":60,"100":40,"200":20,"400":8,"800":2} }
  }
};

export function loadFilterPresets(){
  const sel = document.getElementById('filterPreset');
  if (!sel) return;
  sel.innerHTML = '';
  Object.entries(FILTER_PRESETS_BY_ID).forEach(([id, obj])=>{
    const opt = document.createElement('option');
    opt.value = id;                // ← value = ID canónico
    opt.textContent = obj.label;   // ← se muestra etiqueta
    sel.appendChild(opt);
  });
  sel.value = 'bpf_200k'; // default
  console.log('[filters] opciones', [...sel.options].map(o=>({value:o.value,text:o.text})));
}

// Devuelve la curva/objeto de filtro según selección actual
export function buildFilterCurve(f_rx_MHz){
  const sel = document.getElementById('filterPreset');
  const id = sel?.value || 'bpf_200k';
  const preset = FILTER_PRESETS_BY_ID[id]?.data;
  return preset || FILTER_PRESETS_BY_ID['bpf_200k'].data;
}

export function selectedFilterId(){
  const sel = document.getElementById('filterPreset');
  const name = sel?.value || 'BPF comercial (ancho 200 kHz)';
  const map = {
    'BPF comercial (ancho 200 kHz)': 'bpf_200k',
    'Cavity 8 polos (VHF COM)': 'cavity8',
    'Notch FM (centro 100 MHz)': 'notch100'
  };
  return map[name] || 'bpf_200k';
}


// Ayuda: devolver el ID actual para el payload
export function currentFilterId(){
  return (document.getElementById('filterPreset')?.value) || 'bpf_200k';
}
