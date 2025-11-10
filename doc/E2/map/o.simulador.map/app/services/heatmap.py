from __future__ import annotations
from typing import List
import math
from app.models.schemas import HeatmapRequest, HeatmapResponse, HeatPoint, Component
from app.services.rf import haversine_km, fspl_db, estimate_rx_power_dbm, filter_rejection_at, compute_offset_kHz

def _ring_points(center_lat: float, center_lon: float, r_m: float, step_m: int) -> List[tuple]:
    """
    Muestreo pseudo-cuadricula: barrido en círculos concéntricos (rápido, uniforme).
    """
    pts: List[tuple] = []
    if r_m <= 0: 
        return [(center_lat, center_lon)]
    # densidad angular proporcional al radio para mantener área ~constante
    circumference = 2*math.pi*r_m
    n = max(6, int(circumference / max(step_m, 50)))
    for k in range(n):
        ang = (2*math.pi*k)/n
        dlat = (r_m*math.cos(ang))/111_000.0
        dlon = (r_m*math.sin(ang))/(111_000.0*math.cos(math.radians(center_lat)))
        pts.append((center_lat + dlat, center_lon + dlon))
    return pts

def _grid(center_lat: float, center_lon: float, radius_km: float, step_m: int) -> List[tuple]:
    """
    Espiral de anillos desde 0 hasta radius_km.
    """
    pts = [(center_lat, center_lon)]
    Rm = radius_km*1000.0
    r = step_m
    while r <= Rm:
        pts.extend(_ring_points(center_lat, center_lon, r, step_m))
        r += step_m
    return pts

def _score_point(lat: float, lon: float, f_rx: float, window_kHz: float, curve, txs: List[Component]) -> float:
    """
    Suma de potencias tras filtro (solo portadoras cercanas al canal RX).
    MVP Heatmap: carriers; IM se calcula en /radio/interference por eficiencia.
    """
    levels_lin = 0.0
    for t in txs:
        if t.potencia_dBm is None or t.frecuencia_MHz is None: 
            continue
        d_km = haversine_km(lat, lon, t.lat, t.lon)
        L = fspl_db(d_km, t.frecuencia_MHz)
        prx_dbm = estimate_rx_power_dbm(t.potencia_dBm, L)
        # ventana respecto a RX
        if abs((t.frecuencia_MHz - f_rx)*1e3) > window_kHz:
            continue
        off_kHz = compute_offset_kHz(f_rx, t.frecuencia_MHz, curve)
        rej = filter_rejection_at(off_kHz, curve)
        after_dbm = prx_dbm - rej
        levels_lin += 10**(after_dbm/10.0)
    return -200.0 if levels_lin <= 0 else 10*math.log10(levels_lin)

def build_heatmap(req: HeatmapRequest) -> HeatmapResponse:
    pts = _grid(req.center_lat, req.center_lon, req.radius_km, req.step_m)
    out: List[HeatPoint] = []
    for (la, lo) in pts:
        s = _score_point(la, lo, req.f_rx_MHz, req.window_kHz, req.filter_rejection_dB, req.transmitters)
        out.append(HeatPoint(lat=la, lon=lo, score_dBm=s))
    return HeatmapResponse(points=out, grid_step_m=req.step_m)
