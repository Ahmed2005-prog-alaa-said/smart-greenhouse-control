from datetime import datetime, timezone

from controller import GreenhouseController


def reading(**overrides):
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


def pump_commands(decisions):
    """بترجّع أوامر المضخة بس (ON / OFF)."""
    return [d["action"] for d in decisions if d["actuator"] == "pump"]


def test_pump_keeps_running_above_minimum():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    # 45% فوق الحد الأدنى (40) بس تحت الهدف (55): لازم تكمّل
    result = c.step(reading(soil_moisture_percent=45), now=10)
    assert pump_commands(result) == []


def test_pump_stops_at_target():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    result = c.step(reading(soil_moisture_percent=56), now=10)
    assert pump_commands(result) == ["OFF"]


def test_pump_stops_if_tank_runs_empty():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    # الخزان فضي أثناء الري: لازم تقف
    result = c.step(reading(soil_moisture_percent=40,
                            water_level_percent=5), now=10)
    assert pump_commands(result) == ["OFF"]
