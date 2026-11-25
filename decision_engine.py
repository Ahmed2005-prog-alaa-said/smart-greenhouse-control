import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

from safety_rules import check_telemetry, can_run_pump

# مسار ملف النباتات (جنب الكود)
PROFILES_PATH = Path(__file__).parent / "plant_profiles.json"


def load_profile(plant_type):
    """بترجّع بيانات النبات، أو None لو النبات مش موجود في الملف."""
    with open(PROFILES_PATH, encoding="utf-8") as f:
        return json.load(f).get(plant_type)


def get_limits(profile, section):
    """
    بترجّع (min, max) للقسم المطلوب (زي temperature_c).
    لو الأرقام null أو القسم مش موجود: بترجّع (None, None).
    """
    limits = (profile or {}).get(section) or {}
    return limits.get("min"), limits.get("max")


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

    # 2) نبات مش معروف: ماتقررش حاجة
    profile = load_profile(telemetry.get("plant_type"))
    if profile is None:
        return []

    decisions = []

    # 3) الري: بس لو حد الرطوبة معروف (مش null)
    soil_min, _ = get_limits(profile, "soil_moisture_percent")
    if soil_min is not None and can_run_pump(telemetry):
        if telemetry["soil_moisture_percent"] < soil_min:
            decisions.append(make_decision(
                "pump", "ON", "Soil moisture below configured threshold"))

    # 4) الحرارة: كل حد بيتفحص لو مش null
    temp_min, temp_max = get_limits(profile, "temperature_c")
    temp = telemetry["temperature_c"]
    if temp_max is not None and temp > temp_max:
        decisions.append(make_decision(
            "fan", "ON", "Temperature above configured maximum"))
    elif temp_min is not None and temp < temp_min:
        decisions.append(make_decision(
            "heater", "ON", "Temperature below configured minimum"))

    return decisions
