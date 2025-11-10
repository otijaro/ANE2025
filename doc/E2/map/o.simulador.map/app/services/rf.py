from __future__ import annotations
import math
from typing import Dict, Iterable, List, Optional, Tuple
from app.models.schemas import (
    Component,
    InterferenceItem,
    InterferenceRequest,
    InterferenceResponse,
)

# =========================
# Constantes y utilitarios
# =========================

EARTH_R_M = 6371000.0  # radio medio terrestre

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia (km) sobre esfera."""
    p = math.pi / 180.0
    dlat = (lat2 - lat1) * p
    dlon = (lon2 - lon1) * p
    a = math.sin(dlat/2)**2 + math.cos(lat1*p)*math.cos(lat2*p)*math.sin(dlon/2)**2
    return (2 * EARTH_R_M * math.asin(math.sqrt(a))) / 1000.0

def fspl_db(d_km: float, f_MHz: float) -> float:
    """FSPL (dB) con distancia en km y frecuencia en MHz."""
    if d_km <= 0 or f_MHz <= 0:
        return 0.0
    return 32.44 + 20*math.log10(max(d_km, 1e-9)) + 20*math.log10(max(f_MHz, 1e-9))

def estimate_rx_power_dbm(ptx_dbm: float, pathloss_db: float) -> float:
    """Prx = Ptx − L (sin ganancias/pérdidas adicionales)."""
    return (ptx_dbm or 0.0) - (pathloss_db or 0.0)

def lin_sum_dbm(levels_dbm: Iterable[float]) -> float:
    """Suma en potencia y devuelve dBm. Si lista vacía, −200 dBm."""
    acc = 0.0
    for v in levels_dbm:
        acc += 10 ** (v / 10.0)
    return -200.0 if acc <= 0 else 10 * math.log10(acc)

# =========================
# Filtros (curvas de rechazo)
# =========================

def _curve_points(curve_dict: Dict) -> List[Tuple[float, float]]:
    """
    Convierte dict {"0":0,"25":8,...} a puntos ordenados [(0,0),(25,8),...].
    Si viene formato notch {"center_MHz":X,"curve":{...}}, devuelve puntos de "curve".
    """
    if not isinstance(curve_dict, dict):
        return []
    if "curve" in curve_dict:  # caso notch centrado
        curve_dict = curve_dict.get("curve", {})
    try:
        pts = sorted((float(k), float(v)) for k, v in curve_dict.items())
    except Exception:
        pts = []
    return pts

def filter_rejection_at(offset_kHz: float, curve_dict: Optional[Dict]) -> float:
    """
    Interpola rechazo (dB) para un offset en kHz según curva dict.
    Acepta formato estándar o notch con {"center_MHz":X,"curve":{...}}.
    """
    if not curve_dict:
        return 0.0
    pts = _curve_points(curve_dict)
    if not pts:
        return 0.0
    if offset_kHz <= pts[0][0]:
        return pts[0][1]
    if offset_kHz >= pts[-1][0]:
        return pts[-1][1]
    for (x1, y1), (x2, y2) in zip(pts[:-1], pts[1:]):
        if x1 <= offset_kHz <= x2:
            t = (offset_kHz - x1) / max(1e-9, (x2 - x1))
            return y1 + t * (y2 - y1)
    return 0.0

def compute_offset_kHz(f_rx_MHz: float, f_tx_MHz: float, curve_dict: Optional[Dict]) -> float:
    """
    Para curvas notch con center_MHz usamos ese centro; si no, offset vs f_RX.
    """
    if curve_dict and isinstance(curve_dict, dict) and "center_MHz" in curve_dict:
        center = float(curve_dict.get("center_MHz", f_rx_MHz))
        return abs((f_tx_MHz - center) * 1e3)
    return abs((f_tx_MHz - f_rx_MHz) * 1e3)

# =========================
# Núcleo de interferencias
# =========================

# Penalizaciones empíricas para IM (puedes ajustar luego)
IM2_PENALTY_DB = 40.0   # típicamente 30–50 dB por debajo
IM3_PENALTY_DB = 60.0   # típicamente 50–80 dB por debajo

def _tx_levels_at_receiver(receiver: Component, txs: List[Component]) -> Dict[str, Tuple[float,float]]:
    """
    Devuelve dict id -> (Prx_dBm, fspl_dB) de cada transmisor en la ubicación del RX.
    Ignora transmisores sin potencia/frecuencia.
    """
    out: Dict[str, Tuple[float,float]] = {}
    for t in txs:
        if t.potencia_dBm is None or t.frecuencia_MHz is None:
            continue
        d_km = haversine_km(receiver.lat, receiver.lon, t.lat, t.lon)
        L = fspl_db(d_km, t.frecuencia_MHz)
        prx = estimate_rx_power_dbm(t.potencia_dBm, L)
        out[t.id] = (prx, L)
    return out

def _carrier_items(receiver: Component,
                   txs: List[Component],
                   levels: Dict[str, Tuple[float,float]],
                   window_kHz: float,
                   curve_dict: Optional[Dict]) -> List[InterferenceItem]:
    items: List[InterferenceItem] = []
    for t in txs:
        if t.id not in levels or t.frecuencia_MHz is None:
            continue
        prx, _L = levels[t.id]
        off_kHz = compute_offset_kHz(receiver.frecuencia_MHz or 0.0, t.frecuencia_MHz, curve_dict)
        if receiver.frecuencia_MHz is None:
            # si RX no tiene f, igual la reportamos (offset vs RX=0 no tiene sentido de ventana)
            in_window = True
        else:
            in_window = (abs((t.frecuencia_MHz - receiver.frecuencia_MHz) * 1e3) <= window_kHz)
        if not in_window:
            continue
        rej = filter_rejection_at(off_kHz, curve_dict)
        items.append(InterferenceItem(
            kind="carrier",
            f_MHz=float(t.frecuencia_MHz),
            contributor_ids=[t.id],
            raw_level_dBm=prx,
            after_filter_dBm=prx - rej,
            offset_kHz=off_kHz
        ))
    return items

def _im2_items(receiver: Component,
               txs: List[Component],
               levels: Dict[str, Tuple[float,float]],
               window_kHz: float,
               curve_dict: Optional[Dict]) -> List[InterferenceItem]:
    """
    IM2: f = |f1 ± f2|
    Nivel bruto: suma lineal de Prx(f1) y Prx(f2) con penalización IM2_PENALTY_DB.
    """
    items: List[InterferenceItem] = []
    n = len(txs)
    f_rx = receiver.frecuencia_MHz or 0.0
    for i in range(n):
        t1 = txs[i]
        if t1.id not in levels or t1.frecuencia_MHz is None: continue
        prx1, _ = levels[t1.id]
        for j in range(i + 1, n):
            t2 = txs[j]
            if t2.id not in levels or t2.frecuencia_MHz is None: continue
            prx2, _ = levels[t2.id]

            for f_prod in (abs(t1.frecuencia_MHz + t2.frecuencia_MHz),
                           abs(t1.frecuencia_MHz - t2.frecuencia_MHz)):
                if f_rx:  # filtra por ventana alrededor de f_RX
                    if abs((f_prod - f_rx) * 1e3) > window_kHz:
                        continue
                # potencia IM2 (muy simplificada)
                raw_lin = (10**(prx1/10.0) + 10**(prx2/10.0))
                raw_dbm = -200.0 if raw_lin <= 0 else 10*math.log10(raw_lin) - IM2_PENALTY_DB

                off_kHz = compute_offset_kHz(f_rx, f_prod, curve_dict)
                rej = filter_rejection_at(off_kHz, curve_dict)
                items.append(InterferenceItem(
                    kind="im2",
                    f_MHz=float(f_prod),
                    contributor_ids=[t1.id, t2.id],
                    raw_level_dBm=raw_dbm,
                    after_filter_dBm=raw_dbm - rej,
                    offset_kHz=off_kHz
                ))
    return items

def _im3_items(receiver: Component,
               txs: List[Component],
               levels: Dict[str, Tuple[float,float]],
               window_kHz: float,
               curve_dict: Optional[Dict]) -> List[InterferenceItem]:
    """
    IM3 típicos: 2f1−f2 y 2f2−f1 (los más cercanos al canal deseado).
    Nivel bruto: combinación de potencias con penalización IM3_PENALTY_DB.
    """
    items: List[InterferenceItem] = []
    n = len(txs)
    f_rx = receiver.frecuencia_MHz or 0.0
    for i in range(n):
        t1 = txs[i]
        if t1.id not in levels or t1.frecuencia_MHz is None: continue
        prx1, _ = levels[t1.id]
        for j in range(n):
            if j == i: continue
            t2 = txs[j]
            if t2.id not in levels or t2.frecuencia_MHz is None: continue
            prx2, _ = levels[t2.id]

            for f_prod in (2*t1.frecuencia_MHz - t2.frecuencia_MHz, 2*t2.frecuencia_MHz - t1.frecuencia_MHz):
                if f_rx:
                    if abs((f_prod - f_rx) * 1e3) > window_kHz:
                        continue
                # potencia IM3 (muy simplificada y simétrica)
                raw_lin = (10**(prx1/10.0) + 10**(prx2/10.0))
                raw_dbm = -200.0 if raw_lin <= 0 else 10*math.log10(raw_lin) - IM3_PENALTY_DB

                off_kHz = compute_offset_kHz(f_rx, f_prod, curve_dict)
                rej = filter_rejection_at(off_kHz, curve_dict)
                items.append(InterferenceItem(
                    kind="im3",
                    f_MHz=float(f_prod),
                    contributor_ids=[t1.id, t2.id],
                    raw_level_dBm=raw_dbm,
                    after_filter_dBm=raw_dbm - rej,
                    offset_kHz=off_kHz
                ))
    return items

def radio_interference_core(req: InterferenceRequest) -> InterferenceResponse:
    """
    Núcleo de cálculo de interferencias:
      - Portadoras dentro de ventana
      - Productos IM2 (f1±f2) dentro de ventana
      - Productos IM3 (2f1−f2, 2f2−f1) dentro de ventana
    Aplica curva de filtro (BPF/notch). Devuelve top ordenados por after_filter_dBm (desc).
    """
    rx = req.receiver
    txs = [t for t in req.transmitters if t.frecuencia_MHz is not None and t.potencia_dBm is not None]
    curve = req.filter_rejection_dB or {}
    window_kHz = float(req.window_kHz)
    max_order = int(req.max_order)

    # Niveles en antena del receptor
    levels = _tx_levels_at_receiver(rx, txs)
    fspl_list = []
    for t in txs:
        if t.id in levels:
            _prx, L = levels[t.id]
            fspl_list.append(L)

    items: List[InterferenceItem] = []
    # Carriers
    items += _carrier_items(rx, txs, levels, window_kHz, curve)
    # IM2
    if max_order >= 2:
        items += _im2_items(rx, txs, levels, window_kHz, curve)
    # IM3
    if max_order >= 3:
        items += _im3_items(rx, txs, levels, window_kHz, curve)

    # Ordena por potencia post-filtro
    items.sort(key=lambda x: x.after_filter_dBm, reverse=True)

    # Suma de potencia post-filtro (de TODO lo que quedó en ventana)
    rx_sum_dbm = lin_sum_dbm(it.after_filter_dBm for it in items)

    return InterferenceResponse(
        fspl_tx_rx=fspl_list,
        rx_power_sum_dBm=rx_sum_dbm,
        items=items[:500]  # recorta por seguridad
    )
