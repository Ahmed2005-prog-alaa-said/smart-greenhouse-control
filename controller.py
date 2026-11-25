from decision_engine import decide, make_decision, load_profile, get_limits
from safety_rules import check_telemetry, can_run_pump
from control_state_machine import PumpStateMachine, COOLDOWN

# الفرق بين نقطة التشغيل ونقطة الإيقاف (بالدرجات).
# Harel et al. 2014: التبريد بدأ فوق 30 ووقف عند 28.
HYSTERESIS_C = 2

# سبب كل قرار لأجهزة الحرارة
REASONS = {
    ("fan", "ON"): "Temperature above configured maximum",
    ("fan", "OFF"): "Temperature back within range",
    ("heater", "ON"): "Temperature below configured minimum",
    ("heater", "OFF"): "Temperature back within range",
}


class GreenhouseController:
    """
    بتجمع: فحص الأمان + قرارات الحرارة + State Machine بتاعة المضخة.
    step() بترجّع قائمة القرارات، وself.notes فيها أسباب السكوت.
    """

    def __init__(self):
        self.pump = PumpStateMachine()             # حالة المضخة
        self.last = {"fan": None, "heater": None}  # آخر أمر اتبعت لكل جهاز
        self.notes = []                            # ملاحظات للـ Dashboard

    def _sync(self, actuator, want_on):
        """بتبعت أمر بس لو الحالة المطلوبة اختلفت عن آخر أمر."""
        last = self.last[actuator]
        if want_on and last != "ON":
            self.last[actuator] = "ON"
            return make_decision(actuator, "ON", REASONS[(actuator, "ON")])
        if not want_on and last == "ON":
            self.last[actuator] = "OFF"
            return make_decision(actuator, "OFF", REASONS[(actuator, "OFF")])
        return None

    def step(self, telemetry, now):
        """now = الوقت الحالي بالثواني."""
        self.notes = []  # نبدأ كل قراءة بملاحظات فاضية

        # فحص القراءة، وبعدها نتأكد إن النبات موجود في الملف
        problems = check_telemetry(telemetry)
        profile = None
        if not problems:
            profile = load_profile(telemetry.get("plant_type"))
            if profile is None:
                problems = [f"unknown plant type: {telemetry.get('plant_type')}"]

        safe = not problems
        wants_water = False
        reached_target = False
        decisions = []

        if not safe:
            self.notes = [f"Reading rejected: {p}" for p in problems]
        else:
            soil_min, soil_max = get_limits(profile, "soil_moisture_percent")
            soil = telemetry["soil_moisture_percent"]
            tank_ok = can_run_pump(telemetry)

            if soil_min is None or soil_max is None:
                # الأرقام null: الري متعطّل ومش هنخمّن
                reached_target = True
                self.notes.append(
                    "Irrigation disabled: no soil moisture limits set for this plant")
            else:
                # الهدف: نص المدى بين الحد الأدنى والأقصى
                target = (soil_min + soil_max) / 2
                wants_water = soil < soil_min and tank_ok
                reached_target = soil >= target or not tank_ok
                if soil < soil_min and not tank_ok:
                    self.notes.append("Pump blocked: water tank too low")

            # decide() بتقولنا مين محتاج يشتغل من ناحية الحرارة
            wanted = {d["actuator"] for d in decide(telemetry)}

            # hysteresis: لو الجهاز شغال، يفضل شغال لحد ما الحرارة ترجع
            # جوه المدى بفرق HYSTERESIS_C (عشان مايدقش ON/OFF)
            temp_min, temp_max = get_limits(profile, "temperature_c")
            temp = telemetry["temperature_c"]
            if (self.last["fan"] == "ON" and temp_max is not None
                    and temp > temp_max - HYSTERESIS_C):
                wanted.add("fan")
            if (self.last["heater"] == "ON" and temp_min is not None
                    and temp < temp_min + HYSTERESIS_C):
                wanted.add("heater")

            for actuator in ("fan", "heater"):
                decision = self._sync(actuator, actuator in wanted)
                if decision:
                    decisions.append(decision)

        # الـ State Machine هي اللي تقرر أمر المضخة
        command = self.pump.update(now, wants_water, safe, reached_target)
        if command == "ON":
            decisions.append(make_decision(
                "pump", "ON", "Soil moisture below configured threshold"))
        elif command == "OFF":
            decisions.append(make_decision(
                "pump", "OFF", "Irrigation finished or conditions unsafe"))

        # محتاجة مياه بس في استراحة
        if wants_water and self.pump.state == COOLDOWN:
            self.notes.append("Pump waiting: cooldown in progress")

        return decisions
