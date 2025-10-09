import os
DATA_DIR = os.getenv("DATA_DIR", "/app/data")
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")


from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .app.api import router

app = FastAPI(title="H.SimuladorPythonANE API")

# CORS abierto para desarrollo (ajusta en prod)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(router)
