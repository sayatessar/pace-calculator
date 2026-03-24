"""
Vercel serverless function — POST /api/calculate
Vercel automatically exposes /api/*.py files as HTTP endpoints.
"""

import json
import sys
import os
from http.server import BaseHTTPRequestHandler

# Make backend calculator importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from backend.app.calculator import calculate, FRAMEWORKS, format_pace

def build_all_zones(framework_key: str, current_level: int) -> list:
    zones = FRAMEWORKS[framework_key]["zones"]
    result = []
    for i, zone in enumerate(reversed(zones)):
        prev_index = len(zones) - 1 - i - 1
        min_sec = zones[prev_index].max_pace_sec if prev_index >= 0 else 0
        max_sec = zone.max_pace_sec
        pace_range = (
            f"{format_pace(min_sec)}–{format_pace(max_sec)} /km"
            if max_sec != float("inf")
            else f"> {format_pace(min_sec)} /km"
        )
        result.append({
            "level":      zone.level,
            "label":      zone.label,
            "pace_range": pace_range,
            "is_current": zone.level == current_level,
        })
    return result


class handler(BaseHTTPRequestHandler):

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def do_POST(self):
        try:
            length = int(self.headers.get("Content-Length", 0))
            body   = json.loads(self.rfile.read(length))

            distance    = body.get("distance", "")
            finish_time = body.get("finish_time", "")
            framework   = body.get("framework", "1")

            result    = calculate(distance, finish_time, framework)
            all_zones = build_all_zones(framework, result.zone.level)

            payload = {
                "distance_key":   result.distance_key,
                "distance_label": result.distance_label,
                "distance_km":    result.distance_km,
                "finish_time":    result.finish_time,
                "total_seconds":  result.total_seconds,
                "pace_sec_km":    result.pace_sec_km,
                "pace_sec_mile":  result.pace_sec_mile,
                "pace_fmt_km":    result.pace_fmt_km,
                "pace_fmt_mile":  result.pace_fmt_mile,
                "speed_kmh":      result.speed_kmh,
                "speed_mph":      result.speed_mph,
                "splits": [
                    {"label": s.label, "total_seconds": s.total_seconds, "formatted": s.formatted}
                    for s in result.splits
                ],
                "zone": {
                    "level":          result.zone.level,
                    "label":          result.zone.label,
                    "framework_name": result.zone.framework_name,
                },
                "all_zones": all_zones,
            }
            self._respond(200, payload)

        except ValueError as e:
            self._respond(422, {"detail": str(e)})
        except Exception as e:
            self._respond(500, {"detail": "Internal server error"})

    def _respond(self, status: int, data: dict):
        body = json.dumps(data).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self._send_cors_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_cors_headers(self):
        self.send_header("Access-Control-Allow-Origin",  "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
