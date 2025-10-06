from dataclasses import dataclass
from typing import List, Optional
from .entities import Entity, FMTransmitter, Aircraft
import math

@dataclass
class Scene:
    ancho_km: float = 100.0
    alto_km: float = 60.0
    frecuencia_Hz: float = 100e6
    entities: List[Entity] = None

    def __post_init__(self):
        if self.entities is None:
            self.entities = []

    def to_dict(self):
        ents = []
        for e in self.entities:
            etype = "FMTransmitter" if isinstance(e, FMTransmitter) else "Aircraft"
            d = e.to_dict()
            d["type"] = etype
            ents.append(d)
        return {
            "scene": {
                "ancho_km": self.ancho_km,
                "alto_km": self.alto_km,
                "frecuencia_Hz": self.frecuencia_Hz
            },
            "entities": ents
        }

    @staticmethod
    def from_dict(data: dict) -> "Scene":
        s = data.get("scene", {})
        ancho_km = float(s.get("ancho_km", 100.0))
        alto_km = float(s.get("alto_km", 60.0))
        frecuencia_Hz = float(s.get("frecuencia_Hz", 100e6))
        entities_json = data.get("entities", [])

        ents: List[Entity] = []
        for ej in entities_json:
            etype = ej.get("type", "Entity")
            base_kwargs = dict(
                id=str(ej.get("id", "")),
                nombre=str(ej.get("nombre", "")),
                x_km=float(ej.get("x_km", 0.0)),
                y_km=float(ej.get("y_km", 0.0)),
                h_km=float(ej.get("h_km", 0.0)),
            )
            if etype == "FMTransmitter":
                fm = FMTransmitter(**base_kwargs,
                                   potencia_W=ej.get("potencia_W", None),
                                   f_Hz=ej.get("f_Hz", None))
                ents.append(fm)
            elif etype == "Aircraft":
                ac = Aircraft(**base_kwargs)
                ents.append(ac)
            else:
                ents.append(Entity(**base_kwargs))
        return Scene(ancho_km=ancho_km, alto_km=alto_km, frecuencia_Hz=frecuencia_Hz, entities=ents)

def create_multiple_fms(n_fms: int, scene: Scene) -> None:
    for i in range(1, n_fms + 1):
        fm = FMTransmitter(
            id=f"FM_{i}",
            nombre=f"FM_{i}",
            x_km=30.0 + (i * 1.0),
            y_km=15.0,
            h_km=0.1,
            potencia_W=10e3,
            f_Hz=scene.frecuencia_Hz
        )
        scene.entities.append(fm)

def create_bordered_fms(n_fms: int, scene: Scene) -> None:
    perimeter = 2 * (scene.ancho_km + scene.alto_km)
    step = perimeter / n_fms

    for i in range(n_fms):
        position = i * step
        if position < scene.ancho_km:
            x = position
            y = 0.0
        elif position < scene.ancho_km + scene.alto_km:
            x = scene.ancho_km
            y = position - scene.ancho_km
        elif position < 2 * scene.ancho_km + scene.alto_km:
            x = 2 * scene.ancho_km + scene.alto_km - position
            y = scene.alto_km
        else:
            x = 0.0
            y = perimeter - position

        fm = FMTransmitter(
            id=f"FM_{i+1}",
            nombre=f"FM_{i+1}",
            x_km=x,
            y_km=y,
            h_km=0.1,
            potencia_W=10e3,
            f_Hz=scene.frecuencia_Hz
        )
        scene.entities.append(fm)

def create_fms_around_aircraft(n_fms: int, scene: Scene, avion: Aircraft) -> None:
    max_radius = min(scene.ancho_km, scene.alto_km) / 2 - 2
    angle_step = 2 * math.pi / n_fms

    for i in range(n_fms):
        angle = i * angle_step
        x = avion.x_km + max_radius * math.cos(angle)
        y = avion.y_km + max_radius * math.sin(angle)

        fm = FMTransmitter(
            id=f"FM_{i+1}",
            nombre=f"FM_{i+1}",
            x_km=x,
            y_km=y,
            h_km=0.1,
            potencia_W=10e3,
            f_Hz=scene.frecuencia_Hz
        )
        scene.entities.append(fm)