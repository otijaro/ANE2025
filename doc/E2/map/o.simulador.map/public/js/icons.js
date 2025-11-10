// Genera íconos SVG como L.divIcon
function svgIcon(svg, extraTransform=""){
  return L.divIcon({
    className: 'div-marker',
    html: `<div style="transform:translateY(-4px) ${extraTransform}; transform-origin:center;">${svg}</div>`,
    iconSize: [10,10],
    iconAnchor: [10,10]
  });
}

const ICONS = {
  torre: (name)=> svgIcon(`<svg width="90" height="28" viewBox="0 0 90 28" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" stroke="#7c3aed" stroke-width="2">
      <rect x="2" y="8" width="18" height="18" fill="#ffffff" stroke="#7c3aed" rx="3"/>
      <path d="M6,26 L15,8"/><path d="M16,26 L7,8"/>
      <circle cx="11" cy="6" r="3" fill="#7c3aed"/>
      <path d="M11 1 L11 5"/>
    </g>
    <text x="24" y="18" font-size="12" fill="#111827" font-weight="700">${name||'Torre'}</text>
  </svg>`),

  antena:(name)=> svgIcon(`<svg width="120" height="28" viewBox="0 0 120 28" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" stroke="#2563eb" stroke-width="2">
      <path d="M10 26 L10 10"/><circle cx="10" cy="8" r="3" fill="#2563eb"/>
      <path d="M2 26 H18"/>
      <path d="M16 8 C22 6, 22 2, 16 0" />
      <path d="M20 10 C30 6, 30 -2, 20 -4" opacity=".6" />
      <path d="M24 12 C38 6, 38 -4, 24 -8" opacity=".3" />
    </g>
    <text x="36" y="18" font-size="12" fill="#111827" font-weight="700">${name||'Antena FM'}</text>
  </svg>`),

  avion:(name, headingDeg=0)=> svgIcon(`
    <svg width="38" height="28" viewBox="0 0 38 28" xmlns="http://www.w3.org/2000/svg" aria-label="Avión">
      <g fill="#059669" stroke="#059669" stroke-width="1.2">
        <path d="M6 14 L19 14 L13 11 L13 17 Z"/>
        <path d="M12 14 L6 9 L7.5 8 L14 12 Z"/>
        <path d="M12 14 L6 19 L7.5 20 L14 16 Z"/>
        <path d="M9.5 13 L8 10 L9 10 L11 13 Z"/>
        <path d="M9.5 15 L8 18 L9 18 L11 15 Z"/>
      </g>
      <text x="24" y="18" font-size="11" fill="#111827" font-weight="700">${name||''}</text>
    </svg>
  `, `rotate(${headingDeg}deg)`),

  receptor:(name)=> svgIcon(`<svg width="110" height="28" viewBox="0 0 110 28" xmlns="http://www.w3.org/2000/svg">
    <g fill="none" stroke="#fb923c" stroke-width="2">
      <rect x="2" y="8" width="26" height="14" rx="4" fill="#ffffff" stroke="#fb923c"/>
      <circle cx="10" cy="15" r="2" fill="#fb923c"/>
      <circle cx="18" cy="15" r="2" fill="#fb923c"/>
    </g>
    <text x="34" y="18" font-size="12" fill="#111827" font-weight="700">${name||'Receptor'}</text>
  </svg>`)
};

export function iconFor(tipo, nombre, headingDeg=0){
  if (tipo==='torre')   return ICONS.torre(nombre);
  if (tipo==='antena')  return ICONS.antena(nombre);
  if (tipo==='avion')   return ICONS.avion(nombre, headingDeg);
  return ICONS.receptor(nombre);
}
