from __future__ import annotations
from dataclasses import dataclass, asdict, field
from typing import List, Dict

@dataclass
class Entity:
    id: str
    nombre: str
    x_km: float
    y_km: float
    h_km: float
    def to_dict(self) -> dict: return asdict(self)
    def move_to(self, x_km: float, y_km: float):
        self.x_km = x_km; self.y_km = y_km

@dataclass
class FMTransmitter(Entity):
    potencia_W: float = 10e3
    f_Hz: float = 100e6
    def to_dict(self) -> dict:
        d = super().to_dict()
        d["potencia_W"] = self.potencia_W
        d["f_Hz"] = self.f_Hz
        return d

@dataclass
class Aircraft(Entity): ...
@dataclass
class ControlTower(Entity): ...

@dataclass
class Scene:
    ancho_km: float = 100.0
    alto_km: float = 60.0
    frecuencia_Hz: float = 100e6  # compat
    entities: List[Entity] = field(default_factory=list)

    def to_dict(self) -> dict:
        ents = []
        for e in self.entities:
            if isinstance(e, FMTransmitter): etype = "FMTransmitter"
            elif isinstance(e, Aircraft):    etype = "Aircraft"
            elif isinstance(e, ControlTower): etype = "ControlTower"
            else:                             etype = "Entity"
            d = e.to_dict(); d["type"] = etype
            ents.append(d)
        return {"scene": {"ancho_km": self.ancho_km, "alto_km": self.alto_km, "frecuencia_Hz": self.frecuencia_Hz},
                "entities": ents}

    @staticmethod
    def from_dict(data: dict) -> "Scene":
        s = data.get("scene", {})
        ancho_km = float(s.get("ancho_km", 100.0))
        alto_km = float(s.get("alto_km", 60.0))
        frecuencia_Hz = float(s.get("frecuencia_Hz", 100e6))
        ents: List[Entity] = []
        for ej in data.get("entities", []):
            etype = ej.get("type", "Entity")
            base = dict(
                id=str(ej.get("id","")),
                nombre=str(ej.get("nombre","")),
                x_km=float(ej.get("x_km",0.0)),
                y_km=float(ej.get("y_km",0.0)),
                h_km=float(ej.get("h_km",0.0)),
            )
            if etype == "FMTransmitter":
                ents.append(FMTransmitter(**base,
                    potencia_W=float(ej.get("potencia_W",10e3)),
                    f_Hz=float(ej.get("f_Hz",frecuencia_Hz))))
            elif etype == "Aircraft":
                ents.append(Aircraft(**base))
            elif etype == "ControlTower":
                ents.append(ControlTower(**base))
            else:
                ents.append(Entity(**base))
        return Scene(ancho_km=ancho_km, alto_km=alto_km, frecuencia_Hz=frecuencia_Hz, entities=ents)
