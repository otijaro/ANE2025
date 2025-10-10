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


🚀 Cómo ejecutar
A) Solo backend (FastAPI) en Docker

Construir y levantar:

docker compose build --no-cache api
docker compose up -d api


Probar:

curl http://localhost:8000/api/healthz
curl http://localhost:8000/api/scene
curl http://localhost:8000/api/stats


La escena se persiste en ./data/scene.json (montado como volumen).

B) Frontend + Backend con Docker (stack completo)

Construir y levantar ambos:

docker compose build --no-cache
docker compose up -d


Abrir en el navegador:

Frontend: http://localhost:8081/

API (vía proxy): http://localhost:8081/api/healthz

El frontend usa "/api" por defecto y Nginx proxy-a al servicio api:8000.

C) Desarrollo local (sin Docker)

Backend:

# desde la raíz
python -m venv .venv && . .venv/bin/activate    # (Windows: .venv\Scripts\activate)
pip install -r web_api/requirements.txt
uvicorn web_api.main:app --reload --port 8000


Frontend (servidor estático):

cd web_frontend
python -m http.server 5173
# abre http://localhost:5173/?api=http://localhost:8000/api


En dev (:5173), main.js apunta por defecto a http://localhost:8000/api.
Si cambias el puerto de la API, pásalo en ?api=http://host:puerto/api.

Escritorio (PySide6):

pip install -r requirements.txt
python run_desktop.py

🧩 API de referencia (FastAPI)

Base URL (Docker): http://localhost:8000/api

GET /healthz → { "status": "ok" }

GET /scene → estado completo (escena + entidades)

GET /stats → métricas (FSPL min/avg/max, mejor FM, etc.)

POST /entity/move
Body:

{ "id": "AVION1", "x_km": 55.0, "y_km": 32.0 }


POST /entity/add/fm
Body:

{ "nombre": "FM_2", "x_km": 35, "y_km": 40, "h_km": 0.1, "f_MHz": 101.1, "p_kW": 5.0 }


DELETE /entity/{id} → elimina entidad por id

POST /scene/save → guarda a DATA_DIR/scene.json

POST /scene/load → carga desde DATA_DIR/scene.json

La CORS policy está abierta por defecto (CORS_ORIGINS=*); restringir en producción.

🖼️ Frontend (HTML + SVG)

Render en SVG del área en km (grid cada 5 km).

Entidades: Avión, FM_N y Torre (draggable).

Líneas LOS FM → Avión (toggle).

Form para agregar emisoras (valores con , o . aceptados).

Estadísticas: N°, Potencia total, FSPL min/prom/max, mejor FM.

⚙️ Configuración

Variables:

DATA_DIR (por defecto /data en contenedor; en Compose se monta ./data).

CORS_ORIGINS (lista de orígenes permitidos; * en dev).

Puertos:

API: 8000 (publicado en host)

Web: 8081 → 80 (Nginx)

🧪 Pruebas rápidas
# agregar una emisora
curl -X POST http://localhost:8000/api/entity/add/fm \
  -H "Content-Type: application/json" \
  -d '{"nombre":"FM_2","x_km":35,"y_km":40,"h_km":0.1,"f_MHz":101.1,"p_kW":5.0}'

# mover avión
curl -X POST http://localhost:8000/api/entity/move \
  -H "Content-Type: application/json" \
  -d '{"id":"AVION1","x_km":56,"y_km":33}'

🛠️ Desarrollo y contribuciones

Issues y PRs bienvenidos.

Estilo:

Python: PEP8, tipado opcional.

JS: módulos simples y funciones puras donde sea posible.

Roadmap corto:

 Logs estructurados (API + Nginx).

 Headers de seguridad y compresión en Nginx.

 Modo “mapa base” (tiles/imagen) con configuración.

 CI/CD (GitHub Actions) para build y push de imágenes.