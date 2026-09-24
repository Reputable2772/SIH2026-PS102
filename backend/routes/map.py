"""
Map Spatial Indicators & GeoJSON Endpoints.
"""

import json
from pathlib import Path
from typing import Any, Dict, List
from fastapi import APIRouter, HTTPException, Query

from fastapi.responses import FileResponse

from backend.services.data_service import DataService

router = APIRouter(prefix="/map", tags=["Geospatial & Map"])

GEOJSON_FILE = Path(__file__).resolve().parent.parent / "data" / "india_states.geojson"


@router.get("/states", response_model=List[Dict[str, Any]])
def get_state_map_metrics():
    """Returns choropleth indicators across all 36 States/UTs."""
    ds = DataService.get_instance()
    return ds.get_state_choropleth_data()


@router.get("/districts", response_model=List[Dict[str, Any]])
def get_state_districts(state: str = Query(..., description="Target State Name")):
    """Returns district breakdowns with bottleneck and overload metrics for a specific state."""
    ds = DataService.get_instance()
    return ds.get_districts_for_state(state)


@router.get("/geojson")
def get_india_states_geojson():
    """Returns local offline GeoJSON boundary geometry for India's 36 States & UTs."""
    if not GEOJSON_FILE.exists():
        raise HTTPException(status_code=404, detail="GeoJSON boundary file not found")
    return FileResponse(GEOJSON_FILE, media_type="application/json")
