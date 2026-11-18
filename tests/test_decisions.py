from datetime import datetime, timezone, timedelta

from decision_engine import decide


def base(**overrides):
    """قراءة سليمة نعدّل عليها في كل اختبار."""
    t = {
        "plant_type": "tomato",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "soil_moisture_percent": 55,
        "temperature_c": 24,
        "humidity_percent": 60,
        "water_level_percent": 70,
    }
    t.update(overrides)
    return t


def actuators(decisions):
    """بترجّع أسماء الأجهزة اللي في القرارات بس."""
    return [d["actuator"] for d in decisions]


def test_dry_soil_turns_pump_on():
    assert "pump" in actuators(decide(base(soil_moisture_percent=35)))


def test_empty_tank_no_pump():
    result = decide(base(soil_moisture_percent=35, water_level_percent=5))
    assert "pump" not in actuators(result)


def test_normal_conditions_no_decision():
    assert decide(base()) == []


def test_hot_turns_fan_on():
    assert "fan" in actuators(decide(base(temperature_c=35)))


def test_cold_turns_heater_on():
    assert "heater" in actuators(decide(base(temperature_c=10)))


def test_stale_data_gives_no_decision():
    old = datetime.now(timezone.utc) - timedelta(hours=1)
    result = decide(base(timestamp=old.isoformat(), soil_moisture_percent=35))
    assert result == []


def test_broken_sensor_gives_no_decision():
    assert decide(base(temperature_c=200)) == []
