import json
from datetime import datetime, timezone
from pathlib import Path

from controller import GreenhouseController
from decision_engine import decide, get_limits

PROFILES = json.loads(
    (Path(__file__).parent.parent / "plant_profiles.json")
    .read_text(encoding="utf-8"))


def reading(**overrides):
    """قراءة سليمة بنبات حقيقي نعدّل عليها في كل اختبار."""
    t = dict(
        plant_type="tomato",
        timestamp=datetime.now(timezone.utc).isoformat(),
        soil_moisture_percent=55,
        temperature_c=24,
        humidity_percent=60,
        water_level_percent=70,
    )
    t.update(overrides)
    return t


def actuators(decisions):
    """أسماء الأجهزة اللي في القرارات."""
    return [d["actuator"] for d in decisions]


def test_real_plants_exist():
    assert "tomato" in PROFILES
    assert "cucumber" in PROFILES


def test_every_number_has_a_source():
    # أي رقم مش null لازم يكون له مصدر (ما عدا الـ demo)
    for plant, sections in PROFILES.items():
        if plant == "demo_plant":
            continue
        for section, data in sections.items():
            has_number = any(data.get(k) is not None for k in ("min", "max"))
            if has_number:
                assert data.get("source"), f"{plant}.{section} has no source"


def test_get_limits_handles_null_and_missing():
    assert get_limits({"temperature_c": {"min": None, "max": None}},
                      "temperature_c") == (None, None)
    assert get_limits({}, "temperature_c") == (None, None)
    assert get_limits(None, "temperature_c") == (None, None)


def test_tomato_hot_turns_fan_on():
    assert "fan" in actuators(decide(reading(temperature_c=33)))


def test_tomato_cold_turns_heater_on():
    assert "heater" in actuators(decide(reading(temperature_c=10)))


def test_cucumber_hot_and_cold():
    assert "fan" in actuators(decide(reading(plant_type="cucumber", temperature_c=32)))
    assert "heater" in actuators(decide(reading(plant_type="cucumber", temperature_c=15)))


def test_potato_temperature_rules():
    assert "fan" in actuators(decide(reading(plant_type="potato", temperature_c=30)))
    assert "heater" in actuators(decide(reading(plant_type="potato", temperature_c=10)))


def test_tomato_without_soil_limits_never_irrigates():
    c = GreenhouseController()
    result = c.step(reading(soil_moisture_percent=5), now=0)
    assert "pump" not in actuators(result)
    assert any("Irrigation disabled" in n for n in c.notes)


def test_unknown_plant_does_not_crash():
    c = GreenhouseController()
    result = c.step(reading(plant_type="banana"), now=0)
    assert result == []
    assert any("unknown plant" in n for n in c.notes)
