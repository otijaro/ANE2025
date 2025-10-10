# web_api/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app.api import router

app = FastAPI(title="H.SimuladorPythonANE API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # limita en prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# monta los endpoints del router en /api
app.include_router(router, prefix="/api")

# (opcional) healthz plano si quieres probar directo sin prefijo
@app.get("/healthz")
def healthz_root():
    return {"status": "ok"}
