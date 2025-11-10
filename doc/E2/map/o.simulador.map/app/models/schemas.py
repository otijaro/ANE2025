from __future__ import annotations
from typing import List, Optional, Dict
from pydantic import BaseModel, Field

# --------- Componentes ---------
class Component(BaseModel):
    id: str
    nombre: str
    tipo: str                 # 'torre' | 'antena' | 'avion' | 'receptor'
    lat: float
    lon: float
    alt_terreno_m: float = 0.0
    alt_sobre_terreno_m: float = 0.0
    frecuencia_MHz: Optional[float] = None
    potencia_dBm: Optional[float] = None
    heading_deg: Optional[float] = None

# --------- LOS ---------
class LOSRequest(BaseModel):
    tx: Component
    rx: Component
    frecuencia_MHz: float = 118.1
    k_factor: float = 1.33
    samples: int = 128

class LOSProfilePoint(BaseModel):
    d_m: float
    elev_m: float
    ray_h_m: float
    f1_m: float

class LOSResponse(BaseModel):
    has_los: bool
    distance_m: float
    fspl_dB: float
    profile: List[LOSProfilePoint]
    source: str = "flat"
    fresnel_clearance_min_pct: float
    clearance_worst_point_m: float

# --------- Interferencias ---------
class InterferenceItem(BaseModel):
    kind: str                 # 'carrier' | 'im2' | 'im3'
    f_MHz: float
    contributor_ids: List[str]
    raw_level_dBm: float
    after_filter_dBm: float
    offset_kHz: float

class InterferenceRequest(BaseModel):
    receiver: Component
    transmitters: List[Component]
    window_kHz: float = 500.0
    max_order: int = 3
    filter_rejection_dB: Optional[Dict] = None  # curva preset o notch

class InterferenceResponse(BaseModel):
    fspl_tx_rx: List[float] = []
    rx_power_sum_dBm: float
    items: List[InterferenceItem]

# --------- Heatmap ---------
class HeatPoint(BaseModel):
    lat: float
    lon: float
    score_dBm: float

class HeatmapRequest(BaseModel):
    center_lat: float
    center_lon: float
    radius_km: float = 3.0
    step_m: int = 200
    f_rx_MHz: float = 118.1
    window_kHz: float = 150.0
    transmitters: List[Component]
    filter_rejection_dB: Optional[Dict] = None

class HeatmapResponse(BaseModel):
    points: List[HeatPoint]
    grid_step_m: int
