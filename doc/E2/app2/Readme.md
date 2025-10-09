# H.SimuladorPythonANE

Simulador 2D (en km) para estudiar **interferencias FM** entre **emisoras**, un **avión** y una **torre de control**.  
Permite **arrastrar** entidades con el mouse, **agregar emisoras** una a una, ver **líneas de propagación** con **distancia y FSPL**, editar **frecuencia/potencia** en una **tabla**, y **guardar/cargar** la escena en formato JSON.

---

## ✨ Características

- **Plano 2D** con unidades en **kilómetros** (escala configurable).
- Entidades:
  - **Avión** (arrastrable).
  - **Emisoras FM** (arrastrables, con `f` y `P` individuales).
  - **Torre de control** (fija, no arrastrable).
- **Agregar emisoras** desde un **menú** (diálogo con validación).
- **Líneas de propagación** FM→Avión con etiquetas (distancia + FSPL).
- **Tabla editable** (doble clic) para **Nombre, Frecuencia (MHz) y Potencia (kW)**.
- **Estadísticas**:
  - Resumen global (min/avg/max FSPL a Avión).
  - Por emisora: **FSPL a Avión** y **FSPL a Torre** (si existe torre).
- **Guardar/Cargar** escena (`.json`).

---

## 🗂 Estructura del proyecto
```
h_simulador_ane/
├─ run_desktop.py # punto de entrada de escritorio (PySide6)
├─ requirements.txt
└─ h_simulador/ # paquete Python (dominio + UI)
├─ init.py
├─ utils.py # frange, UnitsConverter
├─ models.py # Entity, Aircraft, FMTransmitter, ControlTower, Scene
├─ controller.py # SceneController (lógica, señales, FSPL, stats)
└─ ui/
├─ init.py
├─ canvas.py # CanvasWidget (pintado + arrastre + LOS)
├─ dialogs.py # AddFmDialog (crear emisoras 1 a 1)
├─ fm_list.py # FMListWidget (tabla editable)
├─ hud.py # HUDWidget (resumen Avión + “más cercana”)
├─ main_window.py # MainWindow (menús, docks, persistencia)
└─ stats.py # StatsWidget (resumen + FSPL Avión/Torre por emisora)

#Web and Desktop
h_simulador_ane/
├─ run_desktop.py          # Desktop PySide6
├─ web_api/
  ├─ main.py              # FastAPI app
  ├─ requirements.txt
  └─ app/
      ├─ __init__.py
      ├─ schemas.py       # Modelos Pydantic para requests/responses
      └─ api.py           # Endpoints de FastAPI
├─ __init__.py
├─ models.py
├─ controller.py
└─ utils.py
└─ ui/ (solo desktop)
    ├─ init.py
    └─ canvas.py # CanvasWidget (pintado + arrastre + LOS)
    ├─ dialogs.py # AddFmDialog (crear emisoras 1 a 1)
    ├─ fm_list.py # FMListWidget (tabla editable)
    ├─ hud.py # HUDWidget (resumen Avión + “más cercana”)
    ├─ main_window.py # MainWindow (menús, docks, persistencia)
    └─ stats.py # StatsWidget (resumen + FSPL Avión/Torre por emisora)

```


## 🛠 Requisitos

- Python **3.10+** (probado en 3.11).
- **PySide6**.

Instalación rápida:

```bash
# Windows / Linux / macOS
python -m pip install -r .\requirements.txt
# o bien
python -m pip install PySide6


▶️ Ejecución
Opción A (recomendada): run_desktop.py fuera del paquete

Desde la carpeta raíz del proyecto:

python run_desktop.py

Opción B: ejecutar como módulo (si run_desktop.py está dentro del paquete)

Desde la carpeta padre del paquete:

python -m h_simulador.run_desktop


Si usas VS Code, selecciona el intérprete correcto (el mismo donde instalaste PySide6).

⌨️ Atajos y menús

Archivo

Guardar escena… (Ctrl+S)

Cargar escena… (Ctrl+O)

Reiniciar (R)

Ver

Grilla (G)

Líneas de propagación (toggle)

Etiquetas en líneas (toggle)

Emisoras

Agregar emisora… (Ctrl+N)

Insertar

Torre de control (fija)

Tabla de emisoras (dock derecho)

Doble clic para editar Nombre, f (MHz) y P (kW).

Arrastre con mouse: Avión y Emisoras (la Torre no se arrastra).

💾 Formato de escena (JSON)
{
  "scene": { "ancho_km": 100.0, "alto_km": 60.0, "frecuencia_Hz": 100000000.0 },
  "entities": [
    {"type": "Aircraft", "id": "AVION1", "nombre": "Avión", "x_km": 50.0, "y_km": 30.0, "h_km": 2.0},
    {"type": "FMTransmitter", "id": "FM_1", "nombre": "FM_1",
     "x_km": 30.0, "y_km": 15.0, "h_km": 0.1, "potencia_W": 10000.0, "f_Hz": 100000000.0},
    {"type": "ControlTower", "id": "TWR1", "nombre": "Torre",
     "x_km": 5.0, "y_km": 5.0, "h_km": 0.05}
  ]
}

🎨 Personalización de colores rápidos

HUD (texto): h_simulador/ui/hud.py

en __init__: self.text.setStyleSheet("color:#ffd166;")

o versión HTML (colores por sección) en update_hud().

Estadísticas (texto): h_simulador/ui/stats.py

en __init__: self.label.setStyleSheet("color:#ffd166; font-family:monospace;")

o desde MainWindow:

self.stats.set_text_color("#ffd166")


Color de líneas LOS: h_simulador/ui/canvas.py (pen #ff6347).

🧮 Modelo de pérdidas (FSPL)

Se usa el modelo en espacio libre:

FSPL(dB) = 32.44 + 20 log10(d_km) + 20 log10(f_MHz)


Cálculo por emisora a Avión y, si existe, a Torre.

Valores se actualizan en tiempo real al mover entidades o editar parámetros.

🧪 Pruebas rápidas (manuales)

Ejecutar el simulador.

Arrastrar el Avión y ver cómo cambian distancias/FSPL.

Agregar emisoras desde el menú y verificar en la tabla y estadísticas.

Editar frecuencia/potencia por doble clic en la tabla y confirmar resultados.

Guardar escena, cerrar, cargar y validar persistencia.

🚀 Camino a Web (roadmap)

El diseño ya separa dominio (models/controller) de UI (PySide6).
Próximos pasos sugeridos:

Exponer SceneController vía FastAPI (endpoints: cargar/guardar escena, agregar FM, mover entidad, calcular FSPL).

Frontend (React/Vue) con canvas HTML para dibujar y arrastrar.

Reusar to_dict/from_dict para mensajes API.

Añadir tests unitarios para controller.py (FSPL, stats, validaciones).

🧪 Solución de problemas

ModuleNotFoundError: No module named 'h_simulador'
Asegúrate de:

Ejecutar desde la carpeta padre de h_simulador.

Tener __init__.py en h_simulador/ y h_simulador/ui/.

O, al inicio de run_desktop.py, añadir:

import os, sys
BASE = os.path.dirname(os.path.abspath(__file__))
if BASE not in sys.path:
    sys.path.insert(0, BASE)


No arranca PySide6
Instala en el mismo intérprete que usas para ejecutar:

python -m pip install PySide6


Cachés viejos
Borra __pycache__ y vuelve a correr.

🤝 Contribuir

Crea una rama: feat/mi-mejora.

Sigue la estructura modular del paquete.

Envía PR con descripción clara (capturas si aplica).

