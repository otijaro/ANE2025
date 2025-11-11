# O.simulador.map — Demo interactiva (Cartagena / VHF-COM vs FM)

Simulador web para explorar **interferencia** (portadoras, IM2, IM3), **perfil del terreno y LOS**, rutas y un **heatmap** alrededor del **Cerro de La Popa** (Cartagena).

Arquitectura mínima: **Frontend estático** (Leaflet + JS) + **Backend FastAPI** (`/radio/*` y `/scenario*`).

> Sugerencia: este README usa `<details>` para secciones plegables (simulan “pestañas” en GitHub).

---

## Índice
- [Estructura](#estructura)
- [Puesta en marcha](#puesta-en-marcha)
  - [Backend (FastAPI)](#backend-fastapi)
  - [Frontend estático](#frontend-estático)
  - [Conexión Front ↔ API](#conexión-front--api)
- [Uso de la interfaz](#uso-de-la-interfaz)
- [API de referencia](#api-de-referencia)
  - [`POST /radio/interference`](#post-radiointerference)
  - [`POST /radio/los`](#post-radiolos)
  - [Escenarios `/scenario*`](#escenarios-scenario)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Licencia](#licencia)

---

## Estructura
```
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

```

---

## Puesta en marcha

### Backend (FastAPI)

> Ejecuta estos comandos **desde la carpeta que contiene `app/`** (donde está `app/main.py`).

```bash
# (opcional) entorno virtual
python -m venv .venv
# Windows PowerShell:
. .venv/Scripts/Activate.ps1
# (Bash):
# source .venv/bin/activate

# Dependencias mínimas (ajusta con tu requirements.txt)
pip install fastapi uvicorn pydantic[dotenv]

# CORS: autoriza los orígenes donde servirás el front
# Windows PowerShell:
$env:OSIM_CORS="http://127.0.0.1:8000,http://localhost:8000,http://10.1.51.193:8000"
# Bash:
# export OSIM_CORS="http://127.0.0.1:8000,http://localhost:8000,http://10.1.51.193:8000"

# Levantar API
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

---
## Frontend estático

Ejecuta desde la carpeta que contiene `index.html`.

```python
# Servidor sencillo
python -m http.server 8000

# Abre el front:
# http://127.0.0.1:8000

```

## Conexión Front ↔ API

El front usa window.API_BASE:

1. **Por defecto**: intenta `localStorage.API_BASE`; si no existe, usa `http://127.0.0.1:8000`.

2. **En HTML** (antes de `app.js`):

```html
<script>window.API_BASE = 'http://127.0.0.1:8000';</script>
<script type="module" src="/js/app.js"></script>
```

3. **Rápido por consola del navegador**:
```js
localStorage.setItem('API_BASE','http://127.0.0.1:8000'); location.reload();
```

## Uso de la interfaz

<details> <summary><b>1) Componentes</b></summary>

- Carga automática de **semilla Cartagena** (SKCG + La Popa).

- En **Componentes** puedes crear/editar: tipo (torre/antena/avión/receptor), lat/lon, alturas, frecuencia (MHz), potencia (dBm).

-  Arrastra marcadores en el mapa para reposicionarlos.

-  Guarda/Carga **JSON** localmente o en el backend con **Escenarios**.

</details> <details> <summary><b>2) Interferencia (demo)</b></summary>

- Selecciona **Receptor (RX)**, ajusta **Ventana (±kHz)** y **Orden máx (2–5)**.

- Elige **Filtro** (p. ej., “BPF comercial 200 kHz”).

- **Calcular** abre un modal con 3 pestañas:

  - **Portadoras**

  - **IM2** (2º orden: f1±f2, 2f1, 2f2)

  - **IM3** (3º orden: 2f1±f2, 2f2±f1, 3f1, 3f2)

- Las tablas muestran: **f (MHz), Raw (dBm), Filtro (dBm) e IDs**.

</details> <details> <summary><b>3) Perfil & LOS</b></summary>

- Selecciona **TX/RX**, define **f (MHz)** y **k-factor**.

- **Perfil y LOS** dibuja perfil de terreno, Fresnel y clearance.

</details> <details> <summary><b>4) Rutas y “Vuelo guiado”</b></summary>

- Carga **GPX/CSV**; usa **Play/Pause** y velocidad.

- Opciones de **LOS/interferencia** en vivo mientras se mueve el avión.

</details> <details> <summary><b>5) Heatmap local (La Popa)</b></summary>

- Ajusta **f_RX, ±kHz, radio (km) y step (m) → Generar mapa**.

</details>

## API de referencia

  Asume `API_BASE=http://127.0.0.1:8000`.

`POST /radio/interference`

Calcula portadoras e intermodulación (hasta `max_order`), aplicando atenuación de filtro.

**Body (ejemplo mínimo)**
```json
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

```
**Curl**

```bash

curl -X POST "$API_BASE/radio/interference" \
  -H "Content-Type: application/json" \
  -d @payload_interf.json
```

**Respuesta (resumen)**
```json
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
```

`POST /radio/los`

Devuelve perfil entre TX/RX, curvatura (k-factor) y Fresnel.

**Body**
```json
{
  "tx": {"lat":10.4452,"lon":-75.5138,"h_m":33},
  "rx": {"lat":10.4480,"lon":-75.5150,"h_m":18},
  "frecuencia_MHz": 118.1,
  "k_factor": 1.33,
  "samples": 128
}
```

**Curl**
```bash
curl -X POST "$API_BASE/radio/los" \
  -H "Content-Type: application/json" \
  -d @payload_los.json
```

**Respuesta (resumen)**
```json
{
  "clearance": true,
  "grazing_points": [],
  "profile": [ {"d_m":0,"h_m":33}, {"d_m":100,"h_m":34.2} ],
  "fresnel_radius_m": [ ... ]
}
```

**Escenarios** `/scenario*`

**Guardar**

```bash
curl -X POST "$API_BASE/scenario" \
  -H "Content-Type: application/json" \
  -d '{
    "id":"esc1",
    "name":"Cartagena Popa",
    "owner_id":"demo",
    "objetos":[ /* componentes tal como front */ ]
  }'
```

**Cargar**
```bash
curl "$API_BASE/scenario/esc1"
```

## Troubleshooting
<details> <summary><b>422 Unprocessable Entity</b></summary>

- Campos faltantes (ej. `receiver.name`, `transmitters[].name`, `kind/tipo`).

- Asegura nombres exactos: {`id,name`,`kind`,`lat`,`lon`,`h_m`,`f_MHz`,`erp_dBm`}.

- Revisa la consola del navegador: el **payload** se imprime antes del fetch.

</details> <details> <summary><b>404 o CORS bloqueado</b></summary>

-  Confirma `window.API_BASE` y el origen del front (127.0.0.1 vs IP LAN).

- Variable `OSIM_CORS` en el backend debe incluir todos los orígenes usados por el front.

</details> <details> <summary><b>No abre el modal o no hay resultados</b></summary>

- Verifica que se invoque `initModal()` y existan `#tab_carriers`, `#tab_im2`, `#tab_im3`.

- Si la respuesta tiene `items: []`, puede ser por **filtros muy restrictivos** o falta de **TX con f/potencia** válidas.

</details>

## Roadmap

 - Propagación y pérdidas (topografía/clutter).

 - Diagramas de antena, polarización, tilt.

 - Reporte PDF (figuras + tablas + parámetros).

 - Editor visual de filtros/presets por usuario.

 - Dataset/benchmarks para validar IM2/IM3 vs mediciones reales.

 ## Licencia
 **Universidad Industrial de Santander** - **Agencia Nacional del Espectro**
 - Autores: Omar J Tíjaro - Homero Ortega
