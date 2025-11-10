from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.radio import router as radio_router
from app.api.scenarios import router as scenarios_router

app = FastAPI(title="O.simulador_map API")

# CORS para front local
origins = os.getenv("OSIM_CORS", "http://127.0.0.1:8000,http://localhost:8000,http://10.1.51.193:8000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in origins],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rutas API
app.include_router(radio_router)
app.include_router(scenarios_router)

# Static (sirve /public)
app.mount("/", StaticFiles(directory="public", html=True), name="public")

