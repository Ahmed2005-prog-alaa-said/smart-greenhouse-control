from decision_engine import decide


def base(**overrides):
    t = {"plant_type": "tomato", "soil_moisture_percent": 55,
         "temperature_c": 24, "water_level_percent": 70}
    t.update(overrides)
    return t


def actuators(decisions):
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
