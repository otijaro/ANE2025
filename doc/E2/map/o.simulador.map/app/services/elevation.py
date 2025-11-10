from __future__ import annotations
import math
from typing import List
from app.models.schemas import LOSRequest, LOSResponse, LOSProfilePoint
from app.services.rf import EARTH_R_M, haversine_km, fspl_db


# ==========================================================
# Helpers locales
# ==========================================================

def _interp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t

def _terrain_elev_m(lat: float, lon: float) -> float:
    """
    DEM placeholder.
    TODO: conectar a SRTM/Mapbox/Google Elevation según config.
    """
    return 0.0

def fresnel_f1_radius_m(lambda_m: float, d1_m: float, d2_m: float, D_m: float) -> float:
    if D_m <= 0:
        return 0.0
    return math.sqrt(max(0.0, lambda_m * d1_m * d2_m / D_m))

def curvature_bulge_m(d_m: float, D_m: float, k_factor: float) -> float:
    """
    Bulto por curvatura terrestre entre TX y punto a distancia d.
    h = d*(D-d)/(2*R_eff), con R_eff = k * R_tierra.
    """
    R_eff = EARTH_R_M * (k_factor if k_factor > 0 else 1.33)
    return (d_m * (D_m - d_m)) / (2.0 * R_eff)


# ==========================================================
# Perfil LOS
# ==========================================================

def compute_los_profile(req: LOSRequest) -> LOSResponse:
    """
    Calcula perfil entre TX y RX:
    - ray_h_m: altura del rayo directo (línea entre alturas de TX y RX) + curvatura
    - elev_m: elevación del terreno (DEM)
    - f1_m: 1ª Fresnel
    Determina LOS, clearance mínimo y FSPL.
    """
    tx, rx = req.tx, req.rx
    D_km = haversine_km(tx.lat, tx.lon, rx.lat, rx.lon)
    D_m = D_km * 1000.0
    f_Hz = req.frecuencia_MHz * 1e6
    lambda_m = 3e8 / max(f_Hz, 1e-9)

    n = max(16, min(2048, req.samples))
    profile: List[LOSProfilePoint] = []

    h_tx = (tx.alt_terreno_m or 0.0) + (tx.alt_sobre_terreno_m or 0.0)
    h_rx = (rx.alt_terreno_m or 0.0) + (rx.alt_sobre_terreno_m or 0.0)

    min_clearance = float('inf')
    min_clearance_f1_pct = float('inf')

    for i in range(n + 1):
        t = i / n
        lat_i = _interp(tx.lat, rx.lat, t)
        lon_i = _interp(tx.lon, rx.lon, t)
        d_i = t * D_m

        elev = _terrain_elev_m(lat_i, lon_i)

        # rayo directo lineal (alturas absolutas)
        ray_h = _interp(h_tx, h_rx, t)

        # curvatura terrestre
        bulge = curvature_bulge_m(d_i, D_m, req.k_factor)
        ray_h_eff = ray_h - bulge

        # Fresnel 1
        f1 = fresnel_f1_radius_m(lambda_m, d_i, D_m - d_i, D_m)

        # Clearances
        clearance_m = ray_h_eff - elev
        clearance_f1_pct = (clearance_m / max(1e-6, f1)) * 100.0 if f1 > 0 else 999.0

        if clearance_m < min_clearance:
            min_clearance = clearance_m
        if clearance_f1_pct < min_clearance_f1_pct:
            min_clearance_f1_pct = clearance_f1_pct

        profile.append(LOSProfilePoint(
            d_m=d_i, elev_m=elev, ray_h_m=ray_h_eff, f1_m=f1
        ))

    # Criterio: despeje > 0 m y > 60% F1
    has_los = (min_clearance > 0.0) and (min_clearance_f1_pct > 60.0)
    fspl = fspl_db(D_km, req.frecuencia_MHz)

    return LOSResponse(
        has_los=has_los,
        distance_m=D_m,
        fspl_dB=fspl,
        profile=profile,
        source="flat",  # TODO: cambiar cuando conectemos DEM real
        fresnel_clearance_min_pct=min_clearance_f1_pct,
        clearance_worst_point_m=min_clearance
    )

