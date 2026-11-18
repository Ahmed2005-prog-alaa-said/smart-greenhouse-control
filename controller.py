from decision_engine import decide, make_decision, load_profile
from safety_rules import check_telemetry, can_run_pump
from control_state_machine import PumpStateMachine

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
    step() بتتنادى مع كل قراءة جديدة وبترجّع قائمة القرارات النهائية.
    """

    def __init__(self):
        self.pump = PumpStateMachine()             # حالة المضخة
        self.last = {"fan": None, "heater": None}  # آخر أمر اتبعت لكل جهاز

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
        safe = not check_telemetry(telemetry)
        wants_water = False
        reached_target = False
        decisions = []

        if safe:
            profile = load_profile(telemetry["plant_type"])
            limits = profile["soil_moisture_percent"]
            soil = telemetry["soil_moisture_percent"]
            tank_ok = can_run_pump(telemetry)

            # الهدف: نص المدى بين الحد الأدنى والأقصى (للطماطم 55%)
            target = (limits["min"] + limits["max"]) / 2

            # نبدأ الري تحت الحد الأدنى، ونوقف عند الهدف أو لو الخزان فضي
            wants_water = soil < limits["min"] and tank_ok
            reached_target = soil >= target or not tank_ok

            # decide() بتقولنا مين محتاج يشتغل من ناحية الحرارة
            wanted = {d["actuator"] for d in decide(telemetry)}
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

        return decisions
