from pydantic import BaseModel
from typing import Optional

class MoveEntityRequest(BaseModel):
    id: str
    x_km: float
    y_km: float

class AddFMRequest(BaseModel):
    nombre: str
    x_km: float
    y_km: float
    h_km: float
    f_MHz: float
    p_kW: float

class AddTowerRequest(BaseModel):
    x_km: float
    y_km: float
    h_km: Optional[float] = 0.05

__all__ = ["MoveEntityRequest", "AddFMRequest", "AddTowerRequest"]
