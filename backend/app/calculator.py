"""
Core pace calculation logic.
Pure functions — no FastAPI dependency, fully testable in isolation.
"""

from dataclasses import dataclass
from typing import Optional

# ── Distance registry ─────────────────────────────────────────────────────────

DISTANCES: dict[str, tuple[float, str]] = {
    "5K":  (5.0,     "5K"),
    "10K": (10.0,    "10K"),
    "HM":  (21.0975, "Half Marathon"),
    "FM":  (42.195,  "Full Marathon"),
}

DISTANCE_ALIASES: dict[str, str] = {
    "HALFMARATHON": "HM",
    "HALF":         "HM",
    "FULLMARATHON": "FM",
    "FULL":         "FM",
    "MARATHON":     "FM",
}

# ── Effort zone frameworks ────────────────────────────────────────────────────

@dataclass
class Zone:
    level: int
    label: str
    max_pace_sec: float   # upper boundary in seconds/km (inclusive)

FRAMEWORKS: dict[str, dict] = {
    "1": {
        "name": "General / Fixed Thresholds",
        "zones": [
            Zone(5, "Elite / Race Pace",       210),
            Zone(4, "Fast / Threshold",         270),
            Zone(3, "Moderate / Tempo",         330),
            Zone(2, "Easy / Aerobic",           420),
            Zone(1, "Recovery / Walk-Run",      float("inf")),
        ],
    },
    "2": {
        "name": "Jack Daniels' VDOT Zones",
        "zones": [
            Zone(5, "R – Repetition (Speed/Economy)", 180),
            Zone(4, "I – Interval (VO2max)",           228),
            Zone(4, "T – Threshold (Lactate)",         270),
            Zone(3, "M – Marathon Pace",               330),
            Zone(2, "E – Easy / Long Run",             420),
            Zone(1, "Recovery",                        float("inf")),
        ],
    },
    "3": {
        "name": "Heart Rate Zone Model (5-Zone, pace proxy)",
        "zones": [
            Zone(5, "Zone 5 – Max / Anaerobic (90–100% HRmax)", 210),
            Zone(4, "Zone 4 – Hard / Threshold (80–90% HRmax)", 252),
            Zone(3, "Zone 3 – Moderate / Aerobic (70–80% HRmax)", 312),
            Zone(2, "Zone 2 – Easy / Fat Burn (60–70% HRmax)",   390),
            Zone(1, "Zone 1 – Recovery (<60% HRmax)",            float("inf")),
        ],
    },
    "4": {
        "name": "RPE – Rate of Perceived Exertion (1–10)",
        "zones": [
            Zone(5, "RPE 9–10 – Maximum / All-out effort",            210),
            Zone(4, "RPE 7–8 – Very hard, limited speech",            255),
            Zone(3, "RPE 5–6 – Challenging but sustainable",          315),
            Zone(2, "RPE 3–4 – Comfortable, conversational",          405),
            Zone(1, "RPE 1–2 – Very light, warm-up/recovery",         float("inf")),
        ],
    },
}

# ── Result dataclasses ────────────────────────────────────────────────────────

@dataclass
class Split:
    label: str
    total_seconds: float
    formatted: str

@dataclass
class ZoneResult:
    level: int
    label: str
    framework_name: str

@dataclass
class PaceResult:
    distance_key:    str
    distance_label:  str
    distance_km:     float
    finish_time:     str
    total_seconds:   int
    pace_sec_km:     float
    pace_sec_mile:   float
    pace_fmt_km:     str
    pace_fmt_mile:   str
    speed_kmh:       float
    speed_mph:       float
    splits:          list[Split]
    zone:            ZoneResult

# ── Helpers ───────────────────────────────────────────────────────────────────

def time_to_seconds(h: int, m: int, s: int) -> int:
    return h * 3600 + m * 60 + s

def seconds_to_hms(total: float) -> tuple[int, int, int]:
    total = int(total)
    return total // 3600, (total % 3600) // 60, total % 60

def format_time(total_sec: float) -> str:
    h, m, s = seconds_to_hms(total_sec)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"

def format_pace(pace_sec: float) -> str:
    m = int(pace_sec // 60)
    s = int(pace_sec % 60)
    return f"{m}:{s:02d}"

def resolve_distance(raw: str) -> tuple[str, float, str]:
    """Return (canonical_key, km, label) or raise ValueError."""
    key = raw.strip().upper().replace(" ", "")
    key = DISTANCE_ALIASES.get(key, key)
    if key not in DISTANCES:
        raise ValueError(
            f"Unknown distance '{raw}'. Supported: {', '.join(DISTANCES)}"
        )
    km, label = DISTANCES[key]
    return key, km, label

def parse_finish_time(time_str: str) -> int:
    """Parse HH:MM:SS → total seconds, or raise ValueError."""
    import re
    if not re.match(r"^\d{1,2}:[0-5]\d:[0-5]\d$", time_str):
        raise ValueError(
            f"Invalid time format '{time_str}'. Expected HH:MM:SS (e.g. 1:45:00)"
        )
    h, m, s = (int(x) for x in time_str.split(":"))
    total = time_to_seconds(h, m, s)
    if total <= 0:
        raise ValueError("Finish time must be greater than 00:00:00")
    return total

def get_zone(pace_sec_km: float, framework_key: str) -> ZoneResult:
    if framework_key not in FRAMEWORKS:
        raise ValueError(
            f"Unknown framework '{framework_key}'. Supported: {', '.join(FRAMEWORKS)}"
        )
    fw = FRAMEWORKS[framework_key]
    for zone in fw["zones"]:
        if pace_sec_km <= zone.max_pace_sec:
            return ZoneResult(
                level=zone.level,
                label=zone.label,
                framework_name=fw["name"],
            )
    last = fw["zones"][-1]
    return ZoneResult(level=last.level, label=last.label, framework_name=fw["name"])

# ── Main calculation ──────────────────────────────────────────────────────────

SPLIT_DEFINITIONS = [
    ("1 km",       1.0),
    ("5K",         5.0),
    ("10K",        10.0),
    ("Half (21K)", 21.0975),
    ("Full (42K)", 42.195),
]

def calculate(distance_raw: str, finish_time: str, framework_key: str = "1") -> PaceResult:
    dist_key, dist_km, dist_label = resolve_distance(distance_raw)
    total_sec = parse_finish_time(finish_time)

    pace_sec_km   = total_sec / dist_km
    pace_sec_mile = total_sec / (dist_km / 1.60934)
    speed_kmh     = (dist_km / total_sec) * 3600
    speed_mph     = (dist_km / 1.60934 / total_sec) * 3600

    splits = [
        Split(
            label=label,
            total_seconds=pace_sec_km * km,
            formatted=format_time(pace_sec_km * km),
        )
        for label, km in SPLIT_DEFINITIONS
    ]

    zone = get_zone(pace_sec_km, framework_key)

    return PaceResult(
        distance_key=dist_key,
        distance_label=dist_label,
        distance_km=dist_km,
        finish_time=finish_time,
        total_seconds=total_sec,
        pace_sec_km=round(pace_sec_km, 4),
        pace_sec_mile=round(pace_sec_mile, 4),
        pace_fmt_km=format_pace(pace_sec_km),
        pace_fmt_mile=format_pace(pace_sec_mile),
        speed_kmh=round(speed_kmh, 4),
        speed_mph=round(speed_mph, 4),
        splits=splits,
        zone=zone,
    )
