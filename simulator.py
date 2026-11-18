from datetime import datetime, timezone

from controller import GreenhouseController


def run_scenario(name, soil, temp, water, steps=12, step_seconds=10):
    """بتشغّل سيناريو وهمي وتطبع القرارات وأسباب السكوت."""
    print(f"\n=== {name} ===")
    controller = GreenhouseController()
    pump_on = False

    for i in range(steps):
        now = i * step_seconds  # الوقت بالثواني

        # قراءة وهمية بنفس شكل الـ Data Contract
        reading = {
            "plant_type": "tomato",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "soil_moisture_percent": soil,
            "temperature_c": temp,
            "humidity_percent": 60,
            "water_level_percent": water,
        }

        decisions = controller.step(reading, now)
        commands = [f'{d["actuator"]} {d["action"]}' for d in decisions]

        # لو في أمر للمضخة، نحدّث حالتها الوهمية
        for d in decisions:
            if d["actuator"] == "pump":
                pump_on = d["action"] == "ON"

        print(f"t={now:>3}s  soil={soil:>3}%  "
              f"state={controller.pump.state:<11}  {commands}")
        for note in controller.notes:
            print(f"          note: {note}")

        # فيزياء مبسطة: المضخة شغالة = التربة بتترطب، غير كده بتنشف
        soil = min(100, soil + 10) if pump_on else max(0, soil - 1)


if __name__ == "__main__":
    run_scenario("Dry soil", soil=35, temp=24, water=70)
    run_scenario("Hot day", soil=55, temp=35, water=70)
    run_scenario("Empty tank", soil=35, temp=24, water=5)
    run_scenario("Broken sensor", soil=55, temp=200, water=70)
