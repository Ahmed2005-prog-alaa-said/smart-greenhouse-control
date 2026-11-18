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


def test_no_notes_when_everything_normal():
    c = GreenhouseController()
    c.step(reading(), now=0)
    assert c.notes == []


def test_empty_tank_is_explained():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35, water_level_percent=5), now=0)
    assert any("tank" in n for n in c.notes)


def test_broken_sensor_is_explained():
    c = GreenhouseController()
    c.step(reading(temperature_c=200), now=0)
    assert any("temperature_c" in n for n in c.notes)


def test_cooldown_is_explained():
    c = GreenhouseController()
    c.step(reading(soil_moisture_percent=35), now=0)
    c.step(reading(soil_moisture_percent=35), now=30)  # وقفت بعد أقصى مدة
    c.step(reading(soil_moisture_percent=35), now=40)  # في الاستراحة
    assert any("cooldown" in n for n in c.notes)
