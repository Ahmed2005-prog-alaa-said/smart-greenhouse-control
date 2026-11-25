from datetime import datetime, timezone

from controller import GreenhouseController


def reading(**overrides):
    """قراءة سليمة نعدّل عليها في كل اختبار."""
    t = {
        "plant_type": "demo_plant",
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


def test_dry_soil_starts_pump():
    c = GreenhouseController()
    result = c.step(reading(soil_moisture_percent=35), now=0)
    assert pump_commands(result) == ["ON"]


def test_no_repeated_on_command():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    # التربة لسه جافة بعد 5 ثواني: ماينفعش يبعت ON تاني
    result = c.step(reading(soil_moisture_percent=35), now=5)
    assert pump_commands(result) == []


def test_pump_stops_after_max_run():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    result = c.step(reading(soil_moisture_percent=35), now=30)
    assert pump_commands(result) == ["OFF"]


def test_cooldown_blocks_restart():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    c.step(reading(soil_moisture_percent=35), now=30)
    # في الاستراحة والتربة جافة: ممنوع تشتغل
    result = c.step(reading(soil_moisture_percent=35), now=40)
    assert pump_commands(result) == []


def test_stale_data_gives_no_pump_decision():
    c = GreenhouseController()
    result = c.step(reading(timestamp="2020-01-01T00:00:00+00:00",
                            soil_moisture_percent=35), now=0)
    assert pump_commands(result) == []


def test_fan_still_works():
    c = GreenhouseController()
    result = c.step(reading(temperature_c=35), now=0)
    assert "fan" in [d["actuator"] for d in result]
