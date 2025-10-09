from fastapi import APIRouter
from h_simulador.models import Scene, FMTransmitter, Aircraft
from h_simulador.controller_core import SceneController
# Usa import relativo (recomendado dentro del paquete)
from .schemas import MoveEntityRequest, AddFMRequest, AddTowerRequest

router = APIRouter()

# Instancia global para demo; en prod podrías usar una factory o dependencia
scene = Scene(ancho_km=100.0, alto_km=60.0)
controller = SceneController(scene)

# Semilla de datos (una vez)
avion = Aircraft(id="AVION1", nombre="Avión", x_km=50.0, y_km=30.0, h_km=2.0)
controller.scene.entities.append(avion)
fm1 = FMTransmitter(id="FM_1", nombre="FM_1", x_km=30.0, y_km=15.0, h_km=0.1, potencia_W=10e3, f_Hz=100e6)
controller.scene.entities.append(fm1)
controller.add_control_tower(60.0, 50.0, 0.05)

@router.get("/scene")
def get_scene():
    return controller.scene.to_dict()

@router.get("/stats")
def get_stats():
    return controller.stats_overview()

@router.post("/entity/move")
def move_entity(req: MoveEntityRequest):
    controller.set_position(req.id, req.x_km, req.y_km)
    return {"status": "ok"}

@router.post("/entity/add/fm")
def add_fm(req: AddFMRequest):
    fm = controller.add_fm(req.nombre, req.x_km, req.y_km, req.h_km, req.f_MHz, req.p_kW)
    return {"status": "ok", "id": fm.id}

@router.post("/entity/add/tower")
def add_tower(req: AddTowerRequest):
    tower = controller.add_control_tower(req.x_km, req.y_km, req.h_km or 0.05)
    if tower:
        return {"status": "ok", "id": tower.id}
    return {"status": "exists"}



# Funciones para guardar/cargar escena desde JSON en disco
import os, json
from fastapi import HTTPException
from fastapi import Depends
from fastapi.responses import JSONResponse

# Usa el mismo DATA_DIR de main.py
try:
    from ..main import DATA_DIR
except Exception:
    DATA_DIR = "/app/data"

SCENE_PATH = os.path.join(DATA_DIR, "scene.json")

@router.get("/healthz")
def healthz():
    return {"status": "ok"}

@router.delete("/entity/{entity_id}")
def delete_entity(entity_id: str):
    e = controller.get_entity(entity_id)
    if not e:
        raise HTTPException(status_code=404, detail="Entity not found")
    controller.scene.entities = [x for x in controller.scene.entities if x.id != entity_id]
    return {"status": "ok", "deleted": entity_id}

@router.post("/scene/save")
def save_scene():
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SCENE_PATH, "w", encoding="utf-8") as f:
        json.dump(controller.scene.to_dict(), f, ensure_ascii=False, indent=2)
    return {"status": "ok", "path": SCENE_PATH}

@router.post("/scene/load")
def load_scene():
    if not os.path.exists(SCENE_PATH):
        raise HTTPException(status_code=404, detail="No saved scene")
    with open(SCENE_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    # reconstruir escena desde dict
    scene_new = Scene.from_dict(data) if hasattr(Scene, "from_dict") else None
    if scene_new is None:
        # fallback por si no tienes from_dict: reasignar campos básicos
        controller.scene.ancho_km = data.get("scene", {}).get("ancho_km", controller.scene.ancho_km)
        controller.scene.alto_km  = data.get("scene", {}).get("alto_km", controller.scene.alto_km)
        controller.scene.entities = []  # limpia y rehidrata
        for it in data.get("entities", []):
            t = it.get("type")
            if t == "Aircraft":
                controller.scene.entities.append(Aircraft(**{k:v for k,v in it.items() if k!="type"}))
            elif t == "FMTransmitter":
                controller.scene.entities.append(FMTransmitter(**{k:v for k,v in it.items() if k!="type"}))
            elif t == "ControlTower":
                from h_simulador.models import ControlTower
                controller.scene.entities.append(ControlTower(**{k:v for k,v in it.items() if k!="type"}))
    else:
        controller.scene = scene_new
    return {"status": "ok", "loaded": True}
