from pathlib import Path

# Ruta de destino para el nuevo archivo controller.py
output_path = Path("h_simulador/core/controller.py")

# Contenido de la clase SceneController extraído del archivo original
controller_code = '''
from PySide6 import QtCore
from typing import Optional
import math
from .entities import Entity, FMTransmitter, Aircraft
from .scene import Scene

class SceneController(QtCore.QObject):
    sceneChanged = QtCore.Signal()
    hudChanged = QtCore.Signal()

    def __init__(self, scene: Scene):
        super().__init__()
        self.scene = scene

    def reset_scene(self):
        # Posiciones por defecto S1
        for e in self.scene.entities:
            if isinstance(e, FMTransmitter) and e.id == "FM_1":
                e.move_to(30.0, 15.0)
                e.h_km = 0.1
            if isinstance(e, Aircraft) and e.id == "AVION1":
                e.move_to(70.0, 30.0)
                e.h_km = 2.0
        self.sceneChanged.emit()
        self.hudChanged.emit()

    def clamp_entity(self, e: Entity):
        e.x_km = max(0.0, min(self.scene.ancho_km, e.x_km))
        e.y_km = max(0.0, min(self.scene.alto_km, e.y_km))

    def set_position(self, entity_id: str, x_km: float, y_km: float):
        for e in self.scene.entities:
            if e.id == entity_id:
                e.move_to(x_km, y_km)
                self.clamp_entity(e)
                self.sceneChanged.emit()
                self.hudChanged.emit()
                break

    def get_entity(self, entity_id: str) -> Optional[Entity]:
        for e in self.scene.entities:
            if e.id == entity_id:
                return e
        return None

    def distance_km(self, a_id: str, b_id: str) -> float:
        a = self.get_entity(a_id)
        b = self.get_entity(b_id)
        if not a or not b:
            return 0.0
        dx = a.x_km - b.x_km
        dy = a.y_km - b.y_km
        return math.hypot(dx, dy)

    @staticmethod
    def fspl_db(d_km: float, f_Hz: float) -> float:
        # FSPL (dB) = 32.44 + 20log10(d_km) + 20log10(f_MHz)
        # Evitar log10(0): si d=0, forzamos a un mínimo pequeño
        d_km = max(d_km, 1e-6)
        f_MHz = f_Hz / 1e6
        return 32.44 + 20.0 * math.log10(d_km) + 20.0 * math.log10(f_MHz)
'''

# Guardar el contenido en el archivo controller.py
output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(controller_code, encoding='utf-8')

# Confirmación
print(f"Archivo creado: {output_path}")