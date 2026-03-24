from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os

from app.calculator import (
    calculate, DISTANCES, FRAMEWORKS,
    format_pace,
)
from app.models import (
    CalculateRequest, CalculateResponse,
    SplitOut, ZoneOut, ZoneLegendItem,
    DistanceInfo, FrameworkInfo, MetaResponse,
)

# ── App setup ─────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Pace Calculator API",
    description="Running pace calculator — estimate pace, speed, splits, and effort zone.",
    version="1.0.0",
)

ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "http://localhost:5173").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

# ── Helpers ───────────────────────────────────────────────────────────────────

def build_all_zones(framework_key: str, current_level: int) -> list[ZoneLegendItem]:
    """Build the full zone legend for the chosen framework, marking the current zone."""
    zones = FRAMEWORKS[framework_key]["zones"]
    result = []
    for i, zone in enumerate(reversed(zones)):
        # lower bound = previous zone's upper bound (or 0 for the slowest zone)
        prev_index = len(zones) - 1 - i - 1  # index in original (non-reversed) list
        min_sec = zones[prev_index].max_pace_sec if prev_index >= 0 else 0

        max_sec = zone.max_pace_sec
        if max_sec == float("inf"):
            pace_range = f"> {format_pace(min_sec)} /km"
        else:
            pace_range = f"{format_pace(min_sec)}–{format_pace(max_sec)} /km"

        result.append(ZoneLegendItem(
            level=zone.level,
            label=zone.label,
            pace_range=pace_range,
            is_current=(zone.level == current_level),
        ))
    return result

# ── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", tags=["health"])
def root():
    return {"status": "ok", "service": "pace-calculator-api"}

@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}

@app.get("/meta", response_model=MetaResponse, tags=["meta"])
def meta():
    """Return all supported distances and frameworks — useful for populating UI dropdowns."""
    return MetaResponse(
        distances=[
            DistanceInfo(key=k, label=v[1], km=v[0])
            for k, v in DISTANCES.items()
        ],
        frameworks=[
            FrameworkInfo(key=k, name=v["name"])
            for k, v in FRAMEWORKS.items()
        ],
    )

@app.post("/calculate", response_model=CalculateResponse, tags=["calculate"])
def calculate_pace(req: CalculateRequest):
    """
    Calculate running pace from a target distance and finish time.

    - **distance**: `5K`, `10K`, `HM`, or `FM`
    - **finish_time**: target finish time in `HH:MM:SS` format
    - **framework**: effort zone framework (`1`–`4`), defaults to `1` (General)
    """
    try:
        result = calculate(req.distance, req.finish_time, req.framework)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    all_zones = build_all_zones(req.framework, result.zone.level)

    return CalculateResponse(
        distance_key=result.distance_key,
        distance_label=result.distance_label,
        distance_km=result.distance_km,
        finish_time=result.finish_time,
        total_seconds=result.total_seconds,
        pace_sec_km=result.pace_sec_km,
        pace_sec_mile=result.pace_sec_mile,
        pace_fmt_km=result.pace_fmt_km,
        pace_fmt_mile=result.pace_fmt_mile,
        speed_kmh=result.speed_kmh,
        speed_mph=result.speed_mph,
        splits=[
            SplitOut(label=s.label, total_seconds=s.total_seconds, formatted=s.formatted)
            for s in result.splits
        ],
        zone=ZoneOut(
            level=result.zone.level,
            label=result.zone.label,
            framework_name=result.zone.framework_name,
        ),
        all_zones=all_zones,
    )
