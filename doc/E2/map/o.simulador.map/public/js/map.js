// Inicializa Leaflet y capas, exporta mapa, capas y un estado compartido.
export const API_BASE = window.API_BASE || 'http://127.0.0.1:8000';

export const state = {
  components: [],           // modelos lógicos
  markers: {},              // id -> L.Marker
  airways: [],              // polylines (array de [lat,lon])
  airwaysLayer: null,       // L.FeatureGroup
  lastHeatPoints: null,     // cache heatmap
  lastHeatParams: null      // cache heatmap
};

export const SKCG = { lat: 10.442, lon: -75.513, zoom: 13 };
export const LA_POPA = { lat: 10.422, lon: -75.519 };

export const layers = {
  torre: null,
  antena: null,
  avion: null,
  receptor: null,
  heat: null
};

export let map;

export function initMap() {
  map = L.map('map').setView([SKCG.lat, SKCG.lon], SKCG.zoom);
  L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png', {maxZoom: 19, attribution: '&copy; OpenStreetMap'}).addTo(map);

  layers.torre    = L.layerGroup().addTo(map);
  layers.antena   = L.layerGroup().addTo(map);
  layers.avion    = L.layerGroup().addTo(map);
  layers.receptor = L.layerGroup().addTo(map);
  layers.heat     = L.layerGroup().addTo(map);

  L.control.layers(null, {
    "Torres": layers.torre,
    "Antenas": layers.antena,
    "Aviones": layers.avion,
    "Receptores": layers.receptor,
    "Heatmap Interferencia": layers.heat
  }, {collapsed: true, position:'topright'}).addTo(map);

  state.airwaysLayer = L.featureGroup().addTo(map);

  setTimeout(()=> {
    map.invalidateSize();
    // Si el canvas del heatmap existe, que ajuste tamaño
    const evt = new Event('resize');
    window.dispatchEvent(evt);
  }, 0);

  return map;
}

export function layerByType(t) {
  return layers[t] || layers.antena;
}

export function centerSKCG() {
  map.setView([SKCG.lat, SKCG.lon], SKCG.zoom);
}
