from __future__ import annotations
import math
from typing import Optional, List, Dict
from PySide6 import QtCore

from .models import Scene, Entity, FMTransmitter, Aircraft, ControlTower

class SceneController(QtCore.QObject):
    sceneChanged = QtCore.Signal()
    hudChanged = QtCore.Signal()

    def __init__(self, scene: Scene):
        super().__init__()
        self.scene = scene

    # --- consulta entidades ---
    def get_entity(self, entity_id: str) -> Optional[Entity]:
        for e in self.scene.entities:
            if e.id == entity_id:
                return e
        return None
    
    def move_control_tower(self, x_km: float, y_km: float):
        """Permite mover la torre de control."""
        tower = self.get_control_tower()
        if tower:
            tower.move_to(x_km, y_km)
            self.sceneChanged.emit()
            self.hudChanged.emit()



    def get_aircraft(self) -> Optional[Aircraft]:
        for e in self.scene.entities:
            if isinstance(e, Aircraft): return e
        return None

    def get_control_tower(self) -> Optional[ControlTower]:
        for e in self.scene.entities:
            if isinstance(e, ControlTower): return e
        return None

    def get_all_fms(self) -> List[FMTransmitter]:
        return [e for e in self.scene.entities if isinstance(e, FMTransmitter)]

    def has_control_tower(self) -> bool:
        return self.get_control_tower() is not None

    # --- mutaciones ---
    def add_control_tower(self, x_km: float, y_km: float, h_km: float = 0.05) -> Optional[ControlTower]:
        if self.has_control_tower(): return None
        t = ControlTower(id="TWR1", nombre="Torre", x_km=x_km, y_km=y_km, h_km=h_km)
        self._clamp_entity(t); self.scene.entities.append(t)
        self.sceneChanged.emit(); self.hudChanged.emit()
        return t

    def _unique_fm_name(self, desired: str) -> str:
        names = {e.nombre for e in self.get_all_fms()}
        if desired not in names: return desired
        base = desired; i = 2
        while f"{base}_{i}" in names: i += 1
        return f"{base}_{i}"

    def add_fm(self, nombre: str, x_km: float, y_km: float, h_km: float, f_MHz: float, p_kW: float) -> FMTransmitter:
        nombre = self._unique_fm_name(nombre or "FM")
        fm = FMTransmitter(id=nombre, nombre=nombre, x_km=x_km, y_km=y_km, h_km=h_km,
                           f_Hz=f_MHz*1e6, potencia_W=p_kW*1e3)
        self._clamp_entity(fm); self.scene.entities.append(fm)
        self.sceneChanged.emit(); self.hudChanged.emit()
        return fm

    def update_fm_params(self, fm_id: str, nombre: Optional[str]=None,
                         f_MHz: Optional[float]=None, p_kW: Optional[float]=None):
        e = self.get_entity(fm_id)
        if not isinstance(e, FMTransmitter): return
        if nombre and nombre.strip():
            new_name = nombre.strip()
            if new_name != e.nombre:
                new_name = self._unique_fm_name(new_name)
                e.nombre = new_name; e.id = new_name
        if f_MHz and f_MHz > 0: e.f_Hz = f_MHz*1e6
        if p_kW and p_kW > 0:   e.potencia_W = p_kW*1e3
        self.sceneChanged.emit(); self.hudChanged.emit()

    def set_position(self, entity_id: str, x_km: float, y_km: float):
        e = self.get_entity(entity_id)
        if not e: return
        e.move_to(x_km, y_km); self._clamp_entity(e)
        self.sceneChanged.emit(); self.hudChanged.emit()

    def _clamp_entity(self, e: Entity):
        e.x_km = max(0.0, min(self.scene.ancho_km, e.x_km))
        e.y_km = max(0.0, min(self.scene.alto_km, e.y_km))

    # --- métricas ---
    @staticmethod
    def compute_fspl_db(d_km: float, f_MHz: float) -> float:
        d_km = max(d_km, 1e-9)
        return 32.44 + 20.0*math.log10(d_km) + 20.0*math.log10(max(f_MHz,1e-9))

    def fspl_all_to_aircraft(self) -> List[Dict]:
        av = self.get_aircraft()
        if not av: return []
        return self.fspl_all_to_target(av)

    def fspl_all_to_target(self, target: Entity) -> List[Dict]:
        out = []
        if not target: return out
        for fm in self.get_all_fms():
            d_km = math.hypot(fm.x_km - target.x_km, fm.y_km - target.y_km)
            f_MHz = fm.f_Hz/1e6
            fspl  = self.compute_fspl_db(d_km, f_MHz)
            out.append({"id": fm.id, "nombre": fm.nombre, "f_MHz": f_MHz,
                        "p_kW": fm.potencia_W/1e3, "d_km": d_km, "fspl_dB": fspl})
        return out

    def stats_overview(self) -> Dict:
        rows = self.fspl_all_to_aircraft()
        if not rows:
            return {"count":0,"p_total_kW":0.0,"fspl_min":None,"fspl_max":None,"fspl_avg":None,"best_fm":None}
        count = len(rows)
        p_total = sum(r["p_kW"] for r in rows)
        fspls = [r["fspl_dB"] for r in rows]
        best = min(rows, key=lambda r: r["fspl_dB"])
        return {"count":count, "p_total_kW":p_total,
                "fspl_min":min(fspls), "fspl_max":max(fspls),
                "fspl_avg":sum(fspls)/count, "best_fm":best}

    def reset_scene(self):
        for e in self.scene.entities:
            if isinstance(e, Aircraft):
                e.move_to(self.scene.ancho_km*0.5, self.scene.alto_km*0.5)
        self.sceneChanged.emit(); self.hudChanged.emit()
