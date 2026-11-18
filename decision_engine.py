import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from safety_rules import check_telemetry, can_run_pump

# مسار ملف النباتات (جنب الكود)
PROFILES_PATH = Path(__file__).parent / "plant_profiles.json"


def load_profile(plant_type):
    """بتفتح ملف JSON وترجّع حدود النبات المطلوب."""
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f)[plant_type]


def make_decision(actuator, action, reason):
    """بتبني قرار واحد بالشكل المتفق عليه في الـ Data Contract."""
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
    """بتاخد القراءة وترجّع قائمة قرارات (فاضية = مفيش حاجة تتعمل)."""
    # 1) افحص القراءة الأول
    if check_telemetry(telemetry):
        return []

    profile = load_profile(telemetry["plant_type"])
    decisions = []

    # 2) الري: التربة جافة + الخزان آمن
    if can_run_pump(telemetry):
        if telemetry["soil_moisture_percent"] < profile["soil_moisture_percent"]["min"]:
            decisions.append(make_decision(
                "pump", "ON", "Soil moisture below configured threshold"))

    # 3) الحرارة: عالية = مروحة، واطية = سخان
    if telemetry["temperature_c"] > profile["temperature_c"]["max"]:
        decisions.append(make_decision(
            "fan", "ON", "Temperature above configured maximum"))
    elif telemetry["temperature_c"] < profile["temperature_c"]["min"]:
        decisions.append(make_decision(
            "heater", "ON", "Temperature below configured minimum"))

    return decisions
