# H.SimuladorPythonANE

Simulador interactivo para escenarios de **avión – emisoras FM – torre de control**.  
Proyecto híbrido **Escritorio (PySide6)** + **Web (FastAPI + Nginx estático)** con contenedores Docker.

---

## 🗂️ Estructura del proyecto

```text
.
│  .dockerignore
│  compose.yml
│  Dockerfile                 # Backend (FastAPI) - imagen de la API
│  estructura.txt
│  Readme.md
│  requirements.txt           # Reqs de escritorio (PySide6) y/o base
│  run_desktop.py             # Lanzador de app de escritorio (PySide6)
│
├─ data/
│   └─ scene.json             # Persistencia de escena (volumen Docker)
│
├─ h_simulador/               # Paquete de dominio y UI de escritorio
│   │  controller_core.py     # Lógica core (sin Qt)
│   │  controller_qt.py       # Controlador Qt (PySide6)
│   │  models.py              # Entity, Aircraft, FMTransmitter, ControlTower, Scene
│   │  utils.py               # Helpers: frange, Units, FSPL, etc.
│   │  __init__.py
│   │
│   └─ ui/
│      │  canvas.py           # CanvasWidget (pintado + eventos/drag + LOS)
│      │  Cartagena.png       # Imagen de mapa local (opcional)
│      │  dialogs.py          # Diálogos (agregar FM, etc.)
│      │  fm_list.py          # Tabla editable de emisoras
│      │  hud.py              # HUD (resumen avión + cercanías)
│      │  main_window.py      # Ventana principal (menú, docks, persistencia)
│      │  map_widget.py       # Widget de mapa (placeholder / local)
│      │  stats.py            # Panel de estadísticas
│      │  __init__.py
│      └─ __pycache__/        # (auto)
│
├─ web_api/                   # Servicio web (FastAPI)
│   │  main.py                # App FastAPI + montaje de router en /api
│   │  requirements.txt       # Reqs del backend
│   │  __init__.py
│   │
│   └─ app/
│      │  api.py              # Rutas REST (scene, stats, move, add FM, etc.)
│      │  schemas.py          # Pydantic models (requests/responses)
│      │  __init__.py
│
└─ web_frontend/              # Frontend estático (HTML + CSS + JS)
   │  Dockerfile              # Imagen Nginx para servir / y proxy /api → api:8000
   │  index.html
   │  main.js                 # UI SVG (render, drag, formularios)
   │  styles.css
   │
   └─ nginx/
      └─ default.conf         # Nginx con proxy_pass a /api
