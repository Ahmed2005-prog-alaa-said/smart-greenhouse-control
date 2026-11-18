from datetime import datetime, timezone, timedelta

from safety_rules import check_telemetry, can_run_pump


def good_reading(**overrides):
    """قراءة سليمة نعدّل عليها في كل اختبار."""
    t = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "temperature_c": 24,
        "humidity_percent": 60,
        "soil_moisture_percent": 55,
        "water_level_percent": 70,
    }
    t.update(overrides)
    return t


def test_good_reading_has_no_problems():
    assert check_telemetry(good_reading()) == []


def test_out_of_range_value_is_flagged():
    # رطوبة تربة 150% مستحيلة، يعني الحساس بايظ
    problems = check_telemetry(good_reading(soil_moisture_percent=150))
    assert len(problems) == 1


def test_missing_field_is_flagged():
    t = good_reading()
    del t["temperature_c"]
    assert len(check_telemetry(t)) == 1


def test_stale_reading_is_flagged():
    old = datetime.now(timezone.utc) - timedelta(hours=1)
    problems = check_telemetry(good_reading(timestamp=old.isoformat()))
    assert any("stale" in p for p in problems)


def test_pump_blocked_when_tank_empty():
    assert can_run_pump(good_reading(water_level_percent=5)) is False


def test_pump_allowed_when_tank_has_water():
    assert can_run_pump(good_reading(water_level_percent=70)) is True
