from decision_engine import decide


def test_dry_soil_turns_pump_on():
    t = {"plant_type": "tomato", "soil_moisture_percent": 35,
         "water_level_percent": 70}
    result = decide(t)
    assert result["actuator"] == "pump"
    assert result["action"] == "ON"


def test_empty_tank_no_decision():
    t = {"plant_type": "tomato", "soil_moisture_percent": 35,
         "water_level_percent": 5}
    assert decide(t) is None


def test_wet_soil_no_decision():
    t = {"plant_type": "tomato", "soil_moisture_percent": 60,
         "water_level_percent": 70}
    assert decide(t) is None
