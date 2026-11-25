from datetime import datetime, timezone

from controller import GreenhouseController


def reading(**overrides):
    """قراءة سليمة بنبات demo (الحد الأدنى 18 والأقصى 30) نعدّل عليها."""
    t = dict(
        plant_type="demo_plant",
        timestamp=datetime.now(timezone.utc).isoformat(),
        soil_moisture_percent=55,
        temperature_c=24,
        humidity_percent=60,
        water_level_percent=70,
    )
    t.update(overrides)
    return t


def commands(decisions, actuator):
    """أوامر جهاز معين (ON / OFF)."""
    return [d["action"] for d in decisions if d["actuator"] == actuator]


def test_fan_does_not_start_inside_band():
    c = GreenhouseController()
    # 29 تحت الحد الأقصى (30): المروحة ماتبدأش
    assert commands(c.step(reading(temperature_c=29), now=0), "fan") == []


def test_fan_keeps_running_until_28():
    c = GreenhouseController()
    c.step(reading(temperature_c=33), now=0)                 # ON
    result = c.step(reading(temperature_c=29), now=10)       # لسه فوق 28
    assert commands(result, "fan") == []                     # ماتقفلش


def test_fan_stops_below_28():
    c = GreenhouseController()
    c.step(reading(temperature_c=33), now=0)
    result = c.step(reading(temperature_c=27), now=10)
    assert commands(result, "fan") == ["OFF"]


def test_heater_keeps_running_until_20():
    c = GreenhouseController()
    c.step(reading(temperature_c=10), now=0)                 # ON
    held = c.step(reading(temperature_c=19), now=10)         # لسه تحت 20
    off = c.step(reading(temperature_c=21), now=20)
    assert commands(held, "heater") == []
    assert commands(off, "heater") == ["OFF"]
