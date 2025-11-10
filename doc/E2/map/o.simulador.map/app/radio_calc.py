import math
from typing import Iterable, List, Tuple


# --- Geodesia ---


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    R = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

# FSPL(dB) con d en km, f en MHz
_DEF_C = 3e8


def fspl_db(d_km: float, f_MHz: float) -> float:
    if d_km <= 0 or f_MHz <= 0:
        return 0.0
    return 32.44 + 20*math.log10(max(d_km, 1e-6)) + 20*math.log10(f_MHz)


def estimate_rx_power_dbm(tx_power_dbm: float, path_loss_db: float) -> float:
    return tx_power_dbm - path_loss_db


# --- Productos de intermodulación ---
# Genera productos de segundo y tercer orden (ampliable) para un conjunto de TX.
# Retorna: (f_Hz, [ids], order, est_level_dBm)


def intermod_products(transmitters: Iterable, max_order: int = 3) -> List[Tuple[float, List[str], int, float]]:
    tx_list = [t for t in transmitters if getattr(t, 'frecuencia_MHz', None) is not None]
    out = []
    factors = {2: 30.0, 3: 40.0}


    # 2º orden: armónicos 2f1; mezcla f1±f2
    if max_order >= 2:
        for i in range(len(tx_list)):
            f1 = tx_list[i].frecuencia_MHz * 1e6
            p1 = tx_list[i].potencia_dBm or -100.0
            out.append((2*f1, [tx_list[i].id], 2, p1 - factors[2]))
            for j in range(i+1, len(tx_list)):
                f2 = tx_list[j].frecuencia_MHz * 1e6
                p2 = tx_list[j].potencia_dBm or -100.0
                lvl = min(p1, p2) - factors[2]
                out.append((abs(f1 + f2), [tx_list[i].id, tx_list[j].id], 2, lvl))
                out.append((abs(f1 - f2), [tx_list[i].id, tx_list[j].id], 2, lvl))


    # 3º orden: 3f1; 2f1±f2, 2f2±f1
    if max_order >= 3:
        for i in range(len(tx_list)):
            f1 = tx_list[i].frecuencia_MHz * 1e6
            p1 = tx_list[i].potencia_dBm or -100.0
            out.append((3*f1, [tx_list[i].id], 3, p1 - factors[3]))
            for j in range(len(tx_list)):
                if i == j: continue
                f2 = tx_list[j].frecuencia_MHz * 1e6
                p2 = tx_list[j].potencia_dBm or -100.0
                lvl = min(p1, p2) - factors[3]
                out.append((abs(2*f1 + f2), [tx_list[i].id, tx_list[j].id], 3, lvl))
                out.append((abs(2*f1 - f2), [tx_list[i].id, tx_list[j].id], 3, lvl))

    # Si quisieras órdenes mayores, continuar generando combinaciones.
    return out