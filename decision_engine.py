import json
from datetime import datetime, timezone
from pathlib import Path

PROFILES_PATH = Path(__file__).parent / "plant_profiles.json"


def load_profile(plant_type):
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)[plant_type]


def decide(telemetry):
    profile = load_profile(telemetry["plant_type"])

    # الخزان فاضي: ماينفعش نشغّل المضخة
    if telemetry["water_level_percent"] < 10:
        return None

    # التربة جافة: شغّل المضخة
    if telemetry["soil_moisture_percent"] < profile["soil_moisture_percent"]["min"]:
        return {
            "decision_id": "decision-001",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "actuator": "pump",
            "action": "ON",
            "mode": "AUTO",
            "reason": "Soil moisture below configured threshold",
            "source": "intelligent_control",
            "requires_safety_check": True,
        }

    return None
