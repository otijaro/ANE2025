import os, math
from typing import List, Tuple
import httpx


# Caché mínima en memoria
_CACHE = {}


async def get_elevation_points(latlons: List[Tuple[float,float]]):
    provider = os.getenv("ELEV_PROVIDER", "open-elev").lower()
    if provider.startswith("open-topo"):
        elevs, src = await _opentopo(latlons)
    else:
        elevs, src = await _open_elevation(latlons)
    return elevs, src

async def _open_elevation(latlons: List[Tuple[float,float]]):
    # API: https://api.open-elevation.com/api/v1/lookup?locations=lat,lon|lat,lon
    elevs = []
    src = "open-elevation"
    async with httpx.AsyncClient(timeout=15) as client:
        # Lotes de hasta 100
        for i in range(0, len(latlons), 100):
            chunk = latlons[i:i+100]
            key = tuple(chunk)
            if key in _CACHE:
                elevs.extend(_CACHE[key])
                continue
            loc = "|".join(f"{lat:.6f},{lon:.6f}" for lat,lon in chunk)
            url = f"https://api.open-elevation.com/api/v1/lookup?locations={loc}"
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                vals = [float(pt["elevation"]) for pt in data.get("results", [])]
                if len(vals) != len(chunk):
                    # relleno simple si faltan
                    while len(vals) < len(chunk):
                        vals.append(vals[-1] if vals else 0.0)
                _CACHE[key] = vals
                elevs.extend(vals)
            except Exception:
                # fallback llano a 0 m si falla la red
                vals = [0.0]*len(chunk)
                _CACHE[key] = vals
                elevs.extend(vals)
                src = src+"|fallback"
    return elevs, src

async def _opentopo(latlons: List[Tuple[float,float]]):
    # API: https://api.opentopodata.org/v1/srtm90m?locations=lat,lon|lat,lon
    elevs = []
    src = "opentopodata-srtm90m"
    
    async with httpx.AsyncClient(timeout=15) as client:
        for i in range(0, len(latlons), 100):
            chunk = latlons[i:i+100]
            key = ("otd", tuple(chunk))
            if key in _CACHE:
                elevs.extend(_CACHE[key])
                continue
            loc = "|".join(f"{lat:.6f},{lon:.6f}" for lat,lon in chunk)
            url = f"https://api.opentopodata.org/v1/srtm90m?locations={loc}"
            try:
                r = await client.get(url)
                r.raise_for_status()
                data = r.json()
                vals = [float(x["elevation"]) if x and x.get("elevation") is not None else 0.0 for x in data.get("results", [])]
                if len(vals) != len(chunk):
                    while len(vals) < len(chunk):
                        vals.append(vals[-1] if vals else 0.0)
                _CACHE[key] = vals
                elevs.extend(vals)
            except Exception:
                vals = [0.0]*len(chunk)
                _CACHE[key] = vals
                elevs.extend(vals)
                src = src+"|fallback"
    return elevs, src
