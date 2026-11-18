from datetime import datetime, timezone

# ===== الإعدادات (غيّرها هنا من غير ما تلمس باقي الكود) =====

# المدى المنطقي لكل قراءة (أقل قيمة، أعلى قيمة).
# أي قراءة برا المدى ده معناها إن الحساس غالبًا بايظ.
VALID_RANGES = {
    "temperature_c": (-10, 60),
    "humidity_percent": (0, 100),
    "soil_moisture_percent": (0, 100),
    "water_level_percent": (0, 100),
}

# أقصى عمر مسموح للقراءة بالثواني (5 دقايق).
# لو أقدم من كده ماننفذش قرار عليها.
MAX_DATA_AGE_SECONDS = 300

# أقل مستوى مياه في الخزان عشان نسمح بتشغيل المضخة.
MIN_WATER_LEVEL_PERCENT = 10


def check_telemetry(telemetry, now=None):
    """
    بتفحص القراءة وترجّع قائمة بالمشاكل.
    قائمة فاضية = القراءة سليمة.
    """
    problems = []

    # 1) كل حقل مطلوب موجود ورقمه منطقي؟
    for field, (low, high) in VALID_RANGES.items():
        value = telemetry.get(field)
        if value is None:
            problems.append(f"{field} is missing")
        elif not (low <= value <= high):
            problems.append(f"{field} out of range: {value}")

    # 2) القراءة حديثة ولا قديمة؟
    try:
        reading_time = datetime.fromisoformat(telemetry["timestamp"])
        now = now or datetime.now(timezone.utc)
        age = (now - reading_time).total_seconds()
        if age > MAX_DATA_AGE_SECONDS:
            problems.append(f"data is stale: {int(age)} seconds old")
    except (KeyError, ValueError, TypeError):
        problems.append("timestamp is missing or invalid")

    return problems


def can_run_pump(telemetry):
    """
    بترجّع True لو آمن نشغّل المضخة (الخزان فيه مياه كفاية).
    """
    level = telemetry.get("water_level_percent")
    return level is not None and level >= MIN_WATER_LEVEL_PERCENT
