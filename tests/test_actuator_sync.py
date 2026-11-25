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


def commands(decisions, actuator):
    """بترجّع أوامر جهاز معين (ON / OFF)."""
    return [d["action"] for d in decisions if d["actuator"] == actuator]


def test_fan_on_is_sent_only_once():
    c = GreenhouseController()
    first = c.step(reading(temperature_c=35), now=0)
    second = c.step(reading(temperature_c=35), now=10)
    assert commands(first, "fan") == ["ON"]
    assert commands(second, "fan") == []


def test_fan_turns_off_when_temperature_normal():
    c = GreenhouseController()
    c.step(reading(temperature_c=35), now=0)
    result = c.step(reading(temperature_c=24), now=10)
    assert commands(result, "fan") == ["OFF"]


def test_no_commands_when_always_normal():
    c = GreenhouseController()
    result = c.step(reading(), now=0)
    assert commands(result, "fan") == []
    assert commands(result, "heater") == []


def test_heater_on_then_off():
    c = GreenhouseController()
    on = c.step(reading(temperature_c=10), now=0)
    off = c.step(reading(temperature_c=24), now=10)
    assert commands(on, "heater") == ["ON"]
    assert commands(off, "heater") == ["OFF"]
