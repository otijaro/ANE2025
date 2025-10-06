from dataclasses import dataclass, asdict
from typing import Optional

@dataclass
class Entity:
    id: str
    nombre: str
    x_km: float
    y_km: float
    h_km: float  # altura

    def to_dict(self):
        return asdict(self)

    def move_to(self, x_km: float, y_km: float):
        self.x_km = x_km
        self.y_km = y_km

@dataclass
class FMTransmitter(Entity):
    potencia_W: Optional[float] = None
    f_Hz: Optional[float] = None  # en S1 se usa frecuencia global de Scene

@dataclass
class Aircraft(Entity):
    pass