from __future__ import annotations
from fastapi import APIRouter
from app.models.schemas import (
    LOSRequest, LOSResponse,
    HeatmapRequest, HeatmapResponse,
    InterferenceRequest, InterferenceResponse,
)
from app.services.elevation import compute_los_profile
from app.services.heatmap import build_heatmap
from app.services.rf import radio_interference_core

router = APIRouter()

@router.post("/radio/los", response_model=LOSResponse)
def los(req: LOSRequest):
    return compute_los_profile(req)

@router.post("/radio/heatmap", response_model=HeatmapResponse)
def heatmap(req: HeatmapRequest):
    return build_heatmap(req)

@router.post("/radio/interference", response_model=InterferenceResponse)
def interference(req: InterferenceRequest):
    return radio_interference_core(req)
    