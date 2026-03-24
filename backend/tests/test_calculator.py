"""
Unit tests for the core calculator logic.
Run with: pytest backend/tests/
"""

import pytest
from app.calculator import (
    calculate,
    resolve_distance,
    parse_finish_time,
    get_zone,
    format_pace,
    format_time,
    time_to_seconds,
)

# ── Helpers ───────────────────────────────────────────────────────────────────

class TestFormatPace:
    def test_round_minutes(self):
        assert format_pace(300) == "5:00"

    def test_pad_seconds(self):
        assert format_pace(298) == "4:58"

    def test_single_digit_seconds(self):
        assert format_pace(301) == "5:01"


class TestFormatTime:
    def test_under_one_hour(self):
        assert format_time(25 * 60) == "25:00"

    def test_over_one_hour(self):
        assert format_time(3600 + 45 * 60) == "1:45:00"

    def test_zero_seconds(self):
        assert format_time(0) == "0:00"


class TestTimeToSeconds:
    def test_basic(self):
        assert time_to_seconds(1, 45, 0) == 6300

    def test_zero(self):
        assert time_to_seconds(0, 0, 0) == 0

    def test_seconds_only(self):
        assert time_to_seconds(0, 0, 30) == 30


# ── Distance resolution ───────────────────────────────────────────────────────

class TestResolveDistance:
    def test_canonical_keys(self):
        for key in ("5K", "10K", "HM", "FM"):
            k, km, label = resolve_distance(key)
            assert k == key

    def test_aliases(self):
        assert resolve_distance("HALF")[0] == "HM"
        assert resolve_distance("half")[0] == "HM"
        assert resolve_distance("marathon")[0] == "FM"
        assert resolve_distance("Full")[0] == "FM"

    def test_invalid(self):
        with pytest.raises(ValueError, match="Unknown distance"):
            resolve_distance("100K")

    def test_hm_km(self):
        _, km, _ = resolve_distance("HM")
        assert km == pytest.approx(21.0975)

    def test_fm_km(self):
        _, km, _ = resolve_distance("FM")
        assert km == pytest.approx(42.195)


# ── Finish time parsing ───────────────────────────────────────────────────────

class TestParseFinishTime:
    def test_valid(self):
        assert parse_finish_time("1:45:00") == 6300

    def test_zero_hours(self):
        assert parse_finish_time("0:25:00") == 1500

    def test_invalid_format(self):
        with pytest.raises(ValueError, match="Invalid time format"):
            parse_finish_time("25:00")

    def test_zero_time(self):
        with pytest.raises(ValueError, match="greater than 00:00:00"):
            parse_finish_time("0:00:00")

    def test_invalid_minutes(self):
        with pytest.raises(ValueError):
            parse_finish_time("1:60:00")


# ── Zone classification ───────────────────────────────────────────────────────

class TestGetZone:
    def test_general_elite(self):
        zone = get_zone(200, "1")
        assert zone.level == 5

    def test_general_recovery(self):
        zone = get_zone(500, "1")
        assert zone.level == 1

    def test_jack_daniels_marathon_pace(self):
        zone = get_zone(298, "2")   # 4:58/km → M zone
        assert "Marathon" in zone.label

    def test_hr_zone_5(self):
        zone = get_zone(180, "3")
        assert zone.level == 5
        assert "Zone 5" in zone.label

    def test_rpe_moderate(self):
        zone = get_zone(300, "4")
        assert "RPE 5" in zone.label

    def test_invalid_framework(self):
        with pytest.raises(ValueError, match="Unknown framework"):
            get_zone(300, "99")


# ── End-to-end calculate ──────────────────────────────────────────────────────

class TestCalculate:
    def test_hm_1h45(self):
        r = calculate("HM", "1:45:00", "1")
        assert r.pace_fmt_km == "4:58"
        assert r.distance_km == pytest.approx(21.0975)
        assert r.speed_kmh == pytest.approx(12.054, rel=1e-2)

    def test_5k_pace(self):
        r = calculate("5K", "0:25:00", "1")
        assert r.pace_fmt_km == "5:00"

    def test_fm_splits_present(self):
        r = calculate("FM", "3:30:00", "1")
        labels = [s.label for s in r.splits]
        assert "1 km" in labels
        assert "Full (42K)" in labels

    def test_framework_selection(self):
        r1 = calculate("HM", "1:45:00", "1")
        r2 = calculate("HM", "1:45:00", "2")
        assert r1.zone.framework_name != r2.zone.framework_name

    def test_alias_distance(self):
        r = calculate("half", "1:45:00")
        assert r.distance_key == "HM"

    def test_invalid_distance_raises(self):
        with pytest.raises(ValueError):
            calculate("100K", "1:00:00")

    def test_invalid_time_raises(self):
        with pytest.raises(ValueError):
            calculate("HM", "invalid")

    def test_speed_units_consistent(self):
        r = calculate("10K", "0:50:00")
        assert r.speed_kmh == pytest.approx(r.speed_mph * 1.60934, rel=1e-3)
