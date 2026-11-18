from decision_engine import decide, make_decision, load_profile
from safety_rules import check_telemetry, can_run_pump
from control_state_machine import PumpStateMachine


class GreenhouseController:
    """
    بتجمع: فحص الأمان + قرارات الحرارة + State Machine بتاعة المضخة.
    step() بتتنادى مع كل قراءة جديدة وبترجّع قائمة القرارات النهائية.
    """

    def __init__(self):
        self.pump = PumpStateMachine()  # بتفتكر حالة المضخة بين القراءات

    def step(self, telemetry, now):
        """now = الوقت الحالي بالثواني."""
        safe = not check_telemetry(telemetry)
        wants_water = False
        decisions = []

        if safe:
            profile = load_profile(telemetry["plant_type"])
            dry = (telemetry["soil_moisture_percent"]
                   < profile["soil_moisture_percent"]["min"])
            wants_water = dry and can_run_pump(telemetry)

            # قرارات الحرارة بس (المضخة بتاعة الـ State Machine)
            decisions = [d for d in decide(telemetry)
                         if d["actuator"] != "pump"]

        # الـ State Machine هي اللي تقرر أمر المضخة
        command = self.pump.update(now, wants_water, safe)
        if command == "ON":
            decisions.append(make_decision(
                "pump", "ON", "Soil moisture below configured threshold"))
        elif command == "OFF":
            decisions.append(make_decision(
                "pump", "OFF", "Irrigation finished or conditions unsafe"))

        return decisions
