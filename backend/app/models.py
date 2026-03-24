from pydantic import BaseModel
from typing import Literal

class CalculateRequest(BaseModel):
    distance: str
    finish_time: str
    framework: Literal["1", "2", "3", "4"] = "1"

    model_config = {"json_schema_extra": {
        "example": {
            "distance": "HM",
            "finish_time": "1:45:00",
            "framework": "2",
        }
    }}

class SplitOut(BaseModel):
    label:         str
    total_seconds: float
    formatted:     str

class ZoneOut(BaseModel):
    level:          int
    label:          str
    framework_name: str

class ZoneLegendItem(BaseModel):
    level:      int
    label:      str
    pace_range: str
    is_current: bool

class CalculateResponse(BaseModel):
    distance_key:   str
    distance_label: str
    distance_km:    float
    finish_time:    str
    total_seconds:  int
    pace_sec_km:    float
    pace_sec_mile:  float
    pace_fmt_km:    str
    pace_fmt_mile:  str
    speed_kmh:      float
    speed_mph:      float
    splits:         list[SplitOut]
    zone:           ZoneOut
    all_zones:      list[ZoneLegendItem]

class DistanceInfo(BaseModel):
    key:   str
    label: str
    km:    float

class FrameworkInfo(BaseModel):
    key:  str
    name: str

class MetaResponse(BaseModel):
    distances:  list[DistanceInfo]
    frameworks: list[FrameworkInfo]
