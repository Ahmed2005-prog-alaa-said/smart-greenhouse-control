import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

PROFILES_PATH = Path(__file__).parent / "plant_profiles.json"


def load_profile(plant_type):
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)[plant_type]


def make_decision(actuator, action, reason):
    return {
        "decision_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actuator": actuator,
        "action": action,
        "mode": "AUTO",
        "reason": reason,
        "source": "intelligent_control",
        "requires_safety_check": True,
    }


def decide(telemetry):
    profile = load_profile(telemetry["plant_type"])
    decisions = []

    # الري
    if telemetry["water_level_percent"] >= 10:
        if telemetry["soil_moisture_percent"] < profile["soil_moisture_percent"]["min"]:
            decisions.append(make_decision(
                "pump", "ON", "Soil moisture below configured threshold"))

    # الحرارة
    if telemetry["temperature_c"] > profile["temperature_c"]["max"]:
        decisions.append(make_decision(
            "fan", "ON", "Temperature above configured maximum"))
    elif telemetry["temperature_c"] < profile["temperature_c"]["min"]:
        decisions.append(make_decision(
            "heater", "ON", "Temperature below configured minimum"))

    return decisions
