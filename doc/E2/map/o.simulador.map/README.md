O.simulador.map — Demo interactiva (Cartagena / VHF-COM vs FM)

Simulador web para explorar interferencia (portadoras, IM2, IM3), perfil del terreno y LOS, rutas y un heatmap alrededor de Cerro de La Popa (Cartagena).

Arquitectura mínima: Frontend estático (Leaflet + JS) + Backend FastAPI (endpoints /radio/* y /scenario*).

Tip de UX en GitHub: este README usa secciones plegables <details> para simular “pestañas”.

Índice

1) Estructura

2) Puesta en marcha

2.1 Backend (FastAPI)

2.2 Frontend estático

2.3 Conexión Front ↔ API

3) Uso de la interfaz

4) API de referencia

4.1 /radio/interference (POST)

4.2 /radio/los (POST)

4.3 Escenarios /scenario*

5) Troubleshooting

6) Roadmap

7) Licencia

1) Estructura
o.simulador.map/
├── app/                     # Backend FastAPI
│   ├── main.py              # uvicorn: app.main:app
│   ├── api/
│   │   ├── radio.py         # Endpoints /radio/los, /radio/interference
│   │   └── scenarios.py     # Endpoints /scenario, /scenario/{id}
│   └── core/
│       ├── db.py            # Almacenamiento simple (archivo/memoria)
│       └── ...              # Utilidades
├── index.html               # Front: UI principal (mapa + panel lateral)
├── js/
│   ├── app.js               # Arranque del front
│   ├── map.js               # Leaflet + capas
│   ├── icons.js             # Íconos de marcadores
│   ├── components.js        # CRUD de componentes (lista/mapa)
│   ├── filters.js           # Presets de filtros y curvas
│   ├── modal.js             # Modal de resultados (Portadoras, IM2, IM3)
│   ├── los.js               # Perfil de terreno y LOS
│   ├── routes.js            # Rutas y “vuelo guiado”
│   └── heatmap.js           # Heatmap local
└── requirements.txt         # (si aplica)

2) Puesta en marcha
2.1 Backend (FastAPI)

Ejecuta estos comandos desde la carpeta que contiene app/ (donde está app/main.py).

# (opcional) entorno virtual
python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# (Bash)
# source .venv/bin/activate

# Dependencias mínimas (ajusta según tu requirements.txt)
pip install fastapi uvicorn pydantic[dotenv]

# CORS: autoriza los orígenes donde servirás el front
# Windows PowerShell:
$env:OSIM_CORS="http://127.0.0.1:8000,http://localhost:8000,http://10.1.51.193:8000"
# (en Bash) export OSIM_CORS="http://127.0.0.1:8000,http://localhost:8000,http://10.1.51.193:8000"

# Levantar API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

2.2 Frontend estático

Ejecuta desde la carpeta que contiene index.html.

# Opción sencilla
python -m http.server 8000

# Abre el front:
# http://127.0.0.1:8000

2.3 Conexión Front ↔ API

El front usa window.API_BASE:

Por defecto: intenta localStorage.API_BASE; si no existe, usa http://127.0.0.1:8000.

En HTML (antes de app.js):

<script>window.API_BASE = 'http://127.0.0.1:8000';</script>
<script type="module" src="/js/app.js"></script>


Rápido por consola:

localStorage.setItem('API_BASE','http://127.0.0.1:8000'); location.reload();

3) Uso de la interfaz

Componentes

Usa la semilla Cartagena (cargada al iniciar) o crea/edita en la sección Componentes.

Cada item tiene: tipo (torre/antena/avión/receptor), lat/lon, alturas, frecuencia (MHz), potencia (dBm).

Arrastra los marcadores en el mapa para reposicionarlos.

Interferencia (demo)

Elige Receptor (RX), ajusta Ventana (±kHz) y Orden máx (2–5).

Selecciona Filtro (p. ej., “BPF comercial 200 kHz”).

Presiona Calcular: se abre el modal con tres “pestañas”:

Portadoras

IM2 (2º orden: f1±f2, 2f1, 2f2)

IM3 (3º orden: 2f1±f2, 2f2±f1, 3f1, 3f2)

La tabla muestra: frecuencia (MHz), nivel bruto (dBm), nivel tras filtro (dBm) e IDs de contribuyentes.

Perfil & LOS

Selecciona TX/RX, define f (MHz) y k-factor.

Perfil y LOS: dibuja el perfil de terreno, Fresnel y clearance.

Rutas y “Vuelo guiado”

Carga GPX/CSV; usa Play/Pause y velocidad.

Opciones de LOS/interferencia en vivo mientras se mueve el avión.

Heatmap local (La Popa)

Ajusta f_RX, ±kHz, radio (km) y step (m) → Generar mapa.

4) API de referencia

Asume API_BASE=http://127.0.0.1:8000.

4.1 /radio/interference (POST)

Calcula portadoras e intermodulación (hasta max_order), aplicando atenuación de filtro.

Body (ejemplo mínimo)

{
  "receiver": {
    "id": "rx1",
    "name": "VHF COM RX",
    "kind": "rx",
    "lat": 10.448,
    "lon": -75.515,
    "h_m": 18,
    "f_MHz": 118.1
  },
  "transmitters": [
    {
      "id": "twr1",
      "name": "Torre SKCG",
      "kind": "tx_vhf",
      "lat": 10.4452,
      "lon": -75.5138,
      "h_m": 33,
      "f_MHz": 118.1,
      "erp_dBm": 50
    },
    {
      "id": "fm2",
      "name": "FM 101.3 (La Popa)",
      "kind": "tx_fm",
      "lat": 10.423,
      "lon": -75.519,
      "h_m": 190,
      "f_MHz": 101.3,
      "erp_dBm": 68
    }
  ],
  "window_kHz": 500,
  "max_order": 3,
  "filter_id": "bpf_200k",
  "filter_rejection_dB": { "0":0, "25":8, "50":14, "100":24, "150":35, "200":45, "300":60, "500":80 }
}


Curl

curl -X POST "$API_BASE/radio/interference" \
  -H "Content-Type: application/json" \
  -d @payload_interf.json


Respuesta (resumen)

{
  "rx_power_sum_dBm": -87.3,
  "fspl_tx_rx": [
    {"tx_id":"twr1","path_loss_dB":120.1},
    {"tx_id":"fm2","path_loss_dB":134.7}
  ],
  "items": [
    {"kind":"carrier","f_MHz":118.1000,"raw_level_dBm":-75.1,"after_filter_dBm":-75.1,"contributor_ids":["twr1"]},
    {"kind":"im3","f_MHz":118.3000,"raw_level_dBm":-82.4,"after_filter_dBm":-90.0,"contributor_ids":["fm2","twr1"]}
  ]
}

4.2 /radio/los (POST)

Devuelve perfil entre TX/RX, curvatura (k-factor) y Fresnel.

Body

{
  "tx": {"lat":10.4452,"lon":-75.5138,"h_m":33},
  "rx": {"lat":10.4480,"lon":-75.5150,"h_m":18},
  "frecuencia_MHz": 118.1,
  "k_factor": 1.33,
  "samples": 128
}


Curl

curl -X POST "$API_BASE/radio/los" \
  -H "Content-Type: application/json" \
  -d @payload_los.json


Respuesta (resumen)

{
  "clearance": true,
  "grazing_points": [],
  "profile": [ {"d_m":0,"h_m":33}, {"d_m":100,"h_m":34.2} ],
  "fresnel_radius_m": [ ... ]
}

4.3 Escenarios /scenario*

Guardar:

curl -X POST "$API_BASE/scenario" \
  -H "Content-Type: application/json" \
  -d '{
    "id":"esc1",
    "name":"Cartagena Popa",
    "owner_id":"demo",
    "objetos":[ /* componentes tal como front */ ]
  }'


Cargar:

curl "$API_BASE/scenario/esc1"

5) Troubleshooting
<details> <summary><b>422 Unprocessable Entity</b></summary>

Campos faltantes (ej. receiver.name, transmitters[].name, kind/tipo).

Asegura nombres exactos: el front exporta {id,name,kind,lat,lon,h_m,f_MHz,erp_dBm}.

Revisa la consola del navegador: el payload se imprime antes del fetch.

</details> <details> <summary><b>404 o CORS bloqueado</b></summary>

Confirma window.API_BASE y el origen del front (127.0.0.1 vs IP LAN).

Variable OSIM_CORS en el backend debe incluir todos los orígenes usados por el front.

</details> <details> <summary><b>No abre el modal o no hay resultados</b></summary>

Verifica que se invoque initModal() y existan #tab_carriers, #tab_im2, #tab_im3.

Si la respuesta tiene items: [], puede ser por filtros muy restrictivos o falta de TX con f/potencia válidas.

</details>
6) Roadmap

 Modelo de propagación y pérdidas (topografía/clutter).

 Diagramas de antena, polarización, tilt.

 Reporte PDF (figuras + tablas + parámetros).

 Presets de filtros por usuario y editor visual.

 Dataset/benchmarks para validar IM2/IM3 vs mediciones reales.

7) Licencia

Autor: Omar J Tíjaro R, licencia libre, generada desde la Universidad Industrial de Santander.