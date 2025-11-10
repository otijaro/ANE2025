from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Tuple
import math
import sqlite3, os, json


from .radio_calc import fspl_db, intermod_products, estimate_rx_power_dbm, haversine_km
from .providers import get_elevation_points
from typing import Dict

DB_PATH = os.getenv("OSIM_DB", "osim.db")

def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        id TEXT PRIMARY KEY, name TEXT
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS scenarios(
        id TEXT PRIMARY KEY, name TEXT, owner_id TEXT, data TEXT
    );""")
    cur.execute("""CREATE TABLE IF NOT EXISTS components(
        id TEXT PRIMARY KEY, scenario_id TEXT, data TEXT
    );""")
    conn.commit(); conn.close()



app = FastAPI(title="O.simulador_map API", version="0.2.0")


app.add_middleware(
                CORSMiddleware,
                allow_origins=["*"],
                allow_credentials=True,
                allow_methods=["*"],
                allow_headers=["*"],
                )


ComponentType = Literal["torre", "antena", "avion", "receptor"]

@app.on_event("startup")
def _startup():
    init_db()

class Component(BaseModel):
    id: str
    nombre: str
    tipo: ComponentType
    lat: float
    lon: float
    alt_terreno_m: float = 0.0
    alt_sobre_terreno_m: float = 0.0
    frecuencia_MHz: Optional[float] = None
    potencia_dBm: Optional[float] = None


class InterferenceRequest(BaseModel):
    receiver: Component
    transmitters: List[Component]
    max_order: int = Field(3, ge=2, le=5)
    window_kHz: float = 500.0
    filter_rejection_dB: dict = Field(default_factory=lambda: {
    "0": 0.0,"50": 10.0,"100": 20.0,"200": 40.0,"300": 60.0,"500": 80.0
    })


class InterferenceItem(BaseModel):
    kind: Literal["carrier", "im2", "im3", "imN"]
    f_MHz: float
    contributor_ids: List[str]
    raw_level_dBm: float
    after_filter_dBm: float
    offset_kHz: float


class InterferenceResponse(BaseModel):
    fspl_tx_rx: List[float]
    rx_power_sum_dBm: float
    items: List[InterferenceItem]


class ProfileRequest(BaseModel):
    lat1: float; lon1: float
    lat2: float; lon2: float
    samples: int = Field(128, ge=2, le=2048)


class ProfilePoint(BaseModel):
    d_m: float
    elev_m: float


class ProfileResponse(BaseModel):
    samples: List[ProfilePoint]
    distance_m: float
    source: str


class LOSRequest(BaseModel):
    tx: Component
    rx: Component
    frecuencia_MHz: float
    k_factor: float = 1.33
    samples: int = Field(128, ge=2, le=2048)


class LOSItem(BaseModel):
    d_m: float
    elev_m: float
    ray_h_m: float
    f1_m: float
    clearance_m: float


class LOSResponse(BaseModel):
    distance_m: float
    has_los: bool
    fresnel_clearance_min_pct: float
    clearance_worst_point_m: float
    fspl_dB: float
    source: str
    profile: List[LOSItem]
    
class ScenarioIn(BaseModel):
    id: str
    name: str
    owner_id: str = "demo"
    objetos: List[Component]

class ScenarioOut(BaseModel):
    id: str
    name: str
    owner_id: str
    objetos: List[Component]
    

@app.get("/health")
def health():
    return {"ok": True}
   
@app.post("/elevation/profile", response_model=ProfileResponse)
async def elevation_profile(req: ProfileRequest):
    latlons = _linspace_latlon(req.lat1, req.lon1, req.lat2, req.lon2, req.samples)
    elevs, src = await get_elevation_points(latlons)
    dist_m = haversine_km(req.lat1, req.lon1, req.lat2, req.lon2) * 1000.0
    pts = [ProfilePoint(d_m=dist_m * i/(req.samples-1), elev_m=e) for i,e in enumerate(elevs)]
    return ProfileResponse(samples=pts, distance_m=dist_m, source=src)


@app.post("/radio/los", response_model=LOSResponse)
async def radio_los(req: LOSRequest):
    # perfil de elevación
    prof = await elevation_profile(ProfileRequest(
    lat1=req.tx.lat, lon1=req.tx.lon,
    lat2=req.rx.lat, lon2=req.rx.lon,
    samples=req.samples
    ))
    # parámetros
    D = prof.distance_m
    h_tx = req.tx.alt_terreno_m + req.tx.alt_sobre_terreno_m
    h_rx = req.rx.alt_terreno_m + req.rx.alt_sobre_terreno_m
    lam = 3e8 / (req.frecuencia_MHz * 1e6)
    Re = 6371000.0 * req.k_factor


    worst_clear = 1e9
    worst_pct = 100.0
    items: List[LOSItem] = []
    for i,p in enumerate(prof.samples):
        d = p.d_m
        # altura del rayo (recta entre h_tx y h_rx) sobre el nivel del mar local
        ray = _interp(h_tx, h_rx, d, D)
        # curvatura/abultamiento terrestre (m)
        bulge = d*(D - d) / (2*Re)
        # radio 1er Fresnel
        d1 = max(d, 1e-6); d2 = max(D - d, 1e-6)
        f1 = math.sqrt(lam * d1 * d2 / D)
        # clearance = (ray - bulge) - elevacion terreno
        clearance = (ray - bulge) - p.elev_m
        items.append(LOSItem(d_m=d, elev_m=p.elev_m, ray_h_m=ray - bulge, f1_m=f1, clearance_m=clearance))
        if f1 > 0:
            pct = 100.0 * (clearance / f1)
            if pct < worst_pct:
                worst_pct = pct
        if clearance < worst_clear:
            worst_clear = clearance


    has_los = worst_clear > 0.6 * (min(it.f1_m for it in items) if items else 0)
    fspl = fspl_db(D/1000.0, req.frecuencia_MHz)


    return LOSResponse(
    distance_m=D,
    has_los=bool(has_los),
    fresnel_clearance_min_pct=worst_pct,
    clearance_worst_point_m=worst_clear,
    fspl_dB=fspl,
    source=prof.source,
    profile=items
    )

from typing import Dict

class HeatmapRequest(BaseModel):
    # Centro/área a evaluar
    center_lat: float
    center_lon: float
    radius_km: float = Field(3.0, ge=0.2, le=30.0)   # radio del área
    step_m: int = Field(200, ge=50, le=2000)         # malla (cuanto menor, más denso)
    # Banda de interés del receptor (ej. COM VHF ~118–137 MHz)
    f_rx_MHz: float = 118.0
    window_kHz: float = 150.0
    max_order: int = 3
    filter_rejection_dB: dict = Field(
        default_factory=lambda: {"0":0,"25":8,"50":15,"100":30,"200":50,"500":80}
    )
    # Transmisores candidatos (antenas/torres)
    transmitters: List[Component]

class HeatPoint(BaseModel):
    lat: float
    lon: float
    score_dBm: float  # suma (lineal) de contribuciones en ventana (portadoras + IM)

class HeatmapResponse(BaseModel):
    points: List[HeatPoint]
    grid_rows: int
    grid_cols: int
    step_m: int
    radius_km: float
    f_rx_MHz: float
    window_kHz: float

@app.post("/radio/heatmap", response_model=HeatmapResponse)
def radio_heatmap(req: HeatmapRequest):
    # Prepara TX válidos
    txs = [t for t in req.transmitters if t.frecuencia_MHz is not None and t.potencia_dBm is not None]
    if not txs:
        return HeatmapResponse(points=[], grid_rows=0, grid_cols=0, step_m=req.step_m,
                                radius_km=req.radius_km, f_rx_MHz=req.f_rx_MHz, window_kHz=req.window_kHz)

    # IM precomputados a partir de todos los TX
    im_freqs = intermod_products(txs, max_order=req.max_order)  # (f_Hz, [ids], order, est_dBm)

    # Define malla (cuadrado circunscrito al círculo de radio_km)
    # Aproximación: 1° lat ~ 111 km, 1° lon ~ 111 km * cos(lat)
    import math
    km_per_deg_lat = 111.0
    km_per_deg_lon = 111.0 * math.cos(math.radians(req.center_lat))
    half_km = req.radius_km
    # pasos en grados
    step_km = req.step_m / 1000.0
    n_steps = int((2*half_km) / step_km) + 1
    points: List[HeatPoint] = []

    for r in range(n_steps):
        for c in range(n_steps):
            # coordenada local (−half_km .. +half_km)
            off_km_x = -half_km + c*step_km
            off_km_y = -half_km + r*step_km
            # descarta puntos fuera del círculo (opcional para alivianar)
            if (off_km_x**2 + off_km_y**2) > (req.radius_km**2):
                continue
            lat = req.center_lat + (off_km_y / km_per_deg_lat)
            lon = req.center_lon + (off_km_x / km_per_deg_lon)

            # suma lineal mW de:
            #  - portadoras dentro de ventana ±window_kHz en torno a f_rx
            #  - productos IM que caigan en la ventana
            prx_lin_mW = 0.0

            # portadoras
            for tx in txs:
                d_km = haversine_km(lat, lon, tx.lat, tx.lon)
                Lfspl = fspl_db(d_km, tx.frecuencia_MHz)
                prx = estimate_rx_power_dbm(tx.potencia_dBm, Lfspl)
                off_kHz = abs((tx.frecuencia_MHz - req.f_rx_MHz)*1e3)
                if off_kHz <= req.window_kHz:
                    rej = _filter_rejection_at(off_kHz, req.filter_rejection_dB)
                    prx_after = prx - rej
                    prx_lin_mW += 10**(prx_after/10)

            # IM
            for fHz, _, order, est_dBm in im_freqs:
                f_MHz = fHz/1e6
                off_kHz = abs((f_MHz - req.f_rx_MHz)*1e3)
                if off_kHz <= req.window_kHz:
                    rej = _filter_rejection_at(off_kHz, req.filter_rejection_dB)
                    prx_lin_mW += 10**((est_dBm - rej)/10)

            score = 10*math.log10(prx_lin_mW) if prx_lin_mW>0 else -200.0
            points.append(HeatPoint(lat=lat, lon=lon, score_dBm=score))

    return HeatmapResponse(points=points, grid_rows=n_steps, grid_cols=n_steps,
                            step_m=req.step_m, radius_km=req.radius_km,
                            f_rx_MHz=req.f_rx_MHz, window_kHz=req.window_kHz)

 
@app.post("/scenario", response_model=ScenarioOut)
def save_scenario(s: ScenarioIn):
    conn = db(); cur = conn.cursor()
    # guarda JSON completo en scenarios y componentes planos (opcional)
    data = json.dumps({"objetos":[o.model_dump() for o in s.objetos]}, ensure_ascii=False)
    cur.execute("REPLACE INTO scenarios(id, name, owner_id, data) VALUES (?,?,?,?)",
                (s.id, s.name, s.owner_id, data))
    # opcional: guarda individuales
    for o in s.objetos:
        cur.execute("REPLACE INTO components(id, scenario_id, data) VALUES (?,?,?)",
                    (o.id, s.id, json.dumps(o.model_dump(), ensure_ascii=False)))
    conn.commit(); conn.close()
    return ScenarioOut(id=s.id, name=s.name, owner_id=s.owner_id, objetos=s.objetos)

@app.get("/scenario/{sid}", response_model=ScenarioOut)
def get_scenario(sid: str):
    conn = db(); cur = conn.cursor()
    row = cur.execute("SELECT * FROM scenarios WHERE id=?", (sid,)).fetchone()
    if not row:
        raise HTTPException(404, "Scenario not found")
    data = json.loads(row["data"])
    objetos = [Component(**x) for x in data.get("objetos",[])]
    out = ScenarioOut(id=row["id"], name=row["name"], owner_id=row["owner_id"], objetos=objetos)
    conn.close()
    return out

@app.get("/scenario", response_model=List[ScenarioOut])
def list_scenarios():
    conn = db(); cur = conn.cursor()
    rows = cur.execute("SELECT * FROM scenarios ORDER BY name").fetchall()
    out = []
    for r in rows:
        data = json.loads(r["data"]); objs = [Component(**x) for x in data.get("objetos",[])]
        out.append(ScenarioOut(id=r["id"], name=r["name"], owner_id=r["owner_id"], objetos=objs))
    conn.close()
    return out

@app.delete("/scenario/{sid}")
def delete_scenario(sid: str):
    conn = db(); cur = conn.cursor()
    cur.execute("DELETE FROM components WHERE scenario_id=?", (sid,))
    cur.execute("DELETE FROM scenarios WHERE id=?", (sid,))
    conn.commit(); conn.close()
    return {"ok": True}



def _filter_rejection_at(offset_kHz: float, curve: Dict) -> float:
    """
    Devuelve el rechazo del filtro (dB) para un offset dado (kHz).
    Acepta dos formatos:
    - {"0":0,"50":10,"100":20,...}
    - {"center_MHz": X, "curve": {"0":80,"50":60,...}}  (el centro lo usarás luego si quieres notch real)
    """
    # si vino en formato notch con 'curve'
    if isinstance(curve, dict) and "curve" in curve:
        curve = curve.get("curve", {})
    # normaliza claves -> float
    try:
        pts = sorted((float(k), float(v)) for k, v in curve.items())
    except Exception:
        return 0.0
    if not pts:
        return 0.0
    # extremos
    if offset_kHz <= pts[0][0]:
        return pts[0][1]
    if offset_kHz >= pts[-1][0]:
        return pts[-1][1]
    # interp lineal
    for i in range(len(pts) - 1):
        x1, y1 = pts[i]
        x2, y2 = pts[i + 1]
        if x1 <= offset_kHz <= x2:
            t = (offset_kHz - x1) / max(1e-9, (x2 - x1))
            return y1 + t * (y2 - y1)
    return 0.0

@app.post("/radio/interference", response_model=InterferenceResponse)
def radio_interference(req: InterferenceRequest):
    """
    Calcula portadoras cercanas a la f_RX e IM2/IM3, aplica la curva de filtro (si viene),
    estima FSPL simple para el sumatorio de potencias en RX.
    """
    rx = req.receiver
    txs = [t for t in req.transmitters if t.frecuencia_MHz is not None and t.potencia_dBm is not None]

    # FSPL por TX y suma de potencias en banda (no filtrada)
    fspls = []
    total_lin = 0.0
    for t in txs:
        d_km = haversine_km(rx.lat, rx.lon, t.lat, t.lon)
        L = fspl_db(d_km, t.frecuencia_MHz)
        prx = estimate_rx_power_dbm(t.potencia_dBm, L)
        fspls.append(L)
        total_lin += 10 ** (prx / 10.0)
    rx_sum_dbm = 10 * math.log10(total_lin) if total_lin > 0 else -200.0

    # Curva de filtro
    curve = req.filter_rejection_dB or {}

    items: List[InterferenceItem] = []

    # Portadoras cerca de f_RX
    for t in txs:
        off_kHz = abs((t.frecuencia_MHz - (rx.frecuencia_MHz or 0.0)) * 1e3)
        L = fspl_db(haversine_km(rx.lat, rx.lon, t.lat, t.lon), t.frecuencia_MHz)
        raw = estimate_rx_power_dbm(t.potencia_dBm, L)
        rej = _filter_rejection_at(off_kHz, curve)
        items.append(InterferenceItem(
            kind="carrier",
            f_MHz=float(t.frecuencia_MHz),
            contributor_ids=[t.id],
            raw_level_dBm=raw,
            after_filter_dBm=raw - rej,
            offset_kHz=off_kHz
        ))

    # IM2 / IM3
    ims = intermod_products(txs, max_order=req.max_order)
    for fHz, ids, order, est_dbm in ims:
        f_MHz = fHz / 1e6
        off_kHz = abs((f_MHz - (rx.frecuencia_MHz or 0.0)) * 1e3)
        rej = _filter_rejection_at(off_kHz, curve)
        items.append(InterferenceItem(
            kind="im2" if order == 2 else "im3" if order == 3 else "imN",
            f_MHz=f_MHz,
            contributor_ids=ids,
            raw_level_dBm=est_dbm,
            after_filter_dBm=est_dbm - rej,
            offset_kHz=off_kHz
        ))

    return InterferenceResponse(
        fspl_tx_rx=fspls,
        rx_power_sum_dBm=rx_sum_dbm,
        items=items
    )

# --- helpers ---
def _linspace_latlon(lat1: float, lon1: float, lat2: float, lon2: float, n: int) -> List[Tuple[float,float]]:
    out = []
    for i in range(n):
        t = i/(n-1)
        out.append((lat1 + t*(lat2 - lat1), lon1 + t*(lon2 - lon1)))
    return out


def _interp(a: float, b: float, d: float, D: float) -> float:
    if D <= 0: return a
    return a + (b - a) * (d / D)