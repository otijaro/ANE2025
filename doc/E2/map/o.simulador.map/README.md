# O.simulador.map

Webapp ligera para **explorar interferencia** (VHF-COM vs FM), **perfil del terreno y LOS**, y **gestión de escenarios** en Leaflet.

> Carpeta del módulo: `doc/E2/map/o.simulador.map/`  
> Front: [`index.html`](./front/index.html) y módulos en [`./front/js`](./front/js/)

---

## Tabla de contenidos
- [Arquitectura](#arquitectura)
- [Arranque rápido](#arranque-rápido)
- [Estructura del front](#estructura-del-front)
- [Flujos principales](#flujos-principales)
- [Modelo de datos (front → back)](#modelo-de-datos-front--back)
- [UI y controles](#ui-y-controles)

---

## Arquitectura
- **Front**: HTML + ES Modules + Leaflet.  
- **Back**: FastAPI (REST).  
- **Comunicación**: JSON sobre HTTP.

---

## Arranque rápido

1. **Backend** FastAPI (puerto `:8000`) con endpoints:
   - `POST /radio/interference`
   - `POST /radio/los`
   - `POST /scenario`
   - `GET  /scenario/{id}`

2. **Front** (servidor estático) desde esta carpeta:
   ```bash
   # dentro de doc/E2/map/o.simulador.map
   python -m http.server 8000


## Estructura-del-front

- **Entrada**: index.html.  
- **Módulos**: (./js/.)  
- **app.js**:  bootstrap del front, eventos de “Calcular” e “LOS”.
- **map.js**: Leaflet, capas, estado y API_BASE.
- **components.js**: CRUD de componentes, semilla Cartagena, export para backend.
- **filters.js**: presets, selección y curva de rechazo.
- **modal.js**: modal con pestañas (Portadoras/IM2/IM3) y tabla responsive.
- **los.js**: perfil del terreno + LOS (SVG).
- **routes.js**: carga de rutas/”vuelo guiado”.
- **heatmap.js**: heatmap por canvas.
- **icons.js**: iconografía por tipo.

**Helpers globales** (expuestos por components.js):

- **window.__osim_export()** → lista de componentes “back-ready”.

- **window.__osim_findById(id), __osim_markerFor(id), __osim_iconFor(o), __osim_findPlane()**.

## Flujos principales
**Interferencia (demo)**

1. Botón **Calcular** en la sección Interferencia (demo).

2. El front toma RX, ventana (±kHz), orden máx, filtro y exporta componentes con **__osim_export()**.

3. Separa **{receiver, transmitters}** y envía a **POST /radio/interference**.

4. Muestra resultados en el **modal** (pestañas: Portadoras, IM2, IM3).

## Perfil y LOS

1. Selecciona **TX** y **RX**, f(MHz) y k-factor.

2. Envía **POST /radio/los**.

3. Dibuja perfil en **#profileSvg** y leyendas en **#losInfo**.

## Escenarios

- **Guardar**: POST /scenario (incluye objetos: state.components).

- **Cargar**: GET /scenario/{id}.

- **Semilla**: “Centrar SKCG” crea el escenario de Cartagena + La Popa.

## Modelo-de-datos-front--back

**Componentes exportados**
  ```bash
   {
  "id": "string",
  "kind": "rx" | "tx_fm" | "tx_vhf" | "tx_gen",
  "lat": 10.44,
  "lon": -75.51,
  "h_m": 185,          // alt_terreno_m + alt_sobre_terreno_m
  "f_MHz": 101.3,      // null si aplica
  "erp_dBm": 68,       // null si aplica
  "name": "FM 101.3 (La Popa)"
}

POST /radio/interference (**request esperado**)

```bash
{
  "receiver": { /* componente kind:'rx' */ },
  "transmitters": [ /* TX con f_MHz y erp_dBm */ ],
  "window_kHz": 500,
  "max_order": 3,
  "filter_id": "bpf_200k",
  "filter_rejection_dB": { "0":0, "25":8, "50":14, "100":24, "150":35, "200":45, "300":60, "500":80 }
}

POST /radio/interference (**response**)
```bash
{
  "fspl_tx_rx": [ /* opcional */ ]  ,
  "rx_power_sum_dBm": -64.3,
  "items": [
    { "kind":"carrier", "f_MHz":118.1, "raw_level_dBm":-14.5, "after_filter_dBm":-14.5, "contributor_ids":["twr1"] }
  ]
}

POST /radio/los (**request**)
```bash
{ "tx":{...}, "rx":{...}, "frecuencia_MHz":118.1, "k_factor":1.33, "samples":128 }


## UI y controles

- **Componentes**: crear/editar (lista y mapa), arrastrar marcadores, enfocarlos/eliminarlos, cargar/guardar JSON local.

- **Interferencia (demo)**: RX, ventana ±kHz, orden máx, filtro (select) y Calcular.

- **Perfil & LOS**: TX/RX + f(MHz) + k-factor → Perfil y LOS.

- **Heatmap**: parámetros y botón Generar mapa.

- **Modal**: pestañas Portadoras / IM2 / IM3; tabla responsive; botón Cerrar.