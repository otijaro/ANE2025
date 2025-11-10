# O.simulador.map

Webapp ligera para **explorar interferencia** (VHF-COM vs FM), **perfil del terreno y LOS**, y **gestión de escenarios** en Leaflet.

> Carpeta del módulo: `doc/E2/map/o.simulador.map/`  
> Front: [`index.html`](./front/index.html) y módulos en [`./js`](./front/js/)

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
