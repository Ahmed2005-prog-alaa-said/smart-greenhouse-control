# Intelligent Control Module (Smart Greenhouse)

Decides when to switch the pump, fan and heater on or off from sensor readings.
Pure Python with no cloud dependency. The cloud side calls
`GreenhouseController.step(telemetry, now)` for every new reading.

## Files

- `plant_profiles.json`: limits per plant, with a source for every number
- `safety_rules.py`: reading validation (ranges, stale data, tank level)
- `decision_engine.py`: profile loading and the basic temperature/irrigation rules
- `control_state_machine.py`: pump states (IDLE, IRRIGATING, COOLDOWN, ERROR)
- `controller.py`: combines everything; this is the entry point for integration
- `simulator.py`: fake readings and scenarios
- `tests/`: automated tests (pytest)
- `ai_ml_integration.py`: placeholder, not implemented yet

## Run

    pip install pytest
    pytest
    python3 simulator.py

## How a decision is made

1. The reading is validated. Out-of-range values, missing fields and data older
   than 5 minutes are rejected.
2. An unknown plant type is rejected.
3. Pump: starts when soil moisture is below the plant minimum, stops at the
   midpoint between minimum and maximum, then rests (COOLDOWN). A maximum run
   time stops it if the sensor gets stuck.
4. Fan and heater: switch on beyond the plant limits and switch off with a
   2 degree C hysteresis. A command is sent only when the state changes.
5. `controller.notes` lists the reason when no action is taken
   (tank low, reading rejected, irrigation disabled, cooldown).

## Decision format

    decision_id, timestamp, actuator, action, mode, reason, source,
    requires_safety_check

`actuator` is pump, fan or heater. `action` is ON or OFF. `mode` is AUTO.
`requires_safety_check` is always true: the cloud must verify before sending
anything to the device, and the ESP32 keeps its own local safety checks.

## Adding a plant

Edit `plant_profiles.json` and add a block with `temperature_c`,
`humidity_percent`, `soil_moisture_percent` and `co2_ppm`.

- Every non-null number needs a `source`. `pytest` fails if one is missing.
- Use `null` when a value is unknown. The related feature is disabled instead
  of guessing.

## Current limits

- Soil moisture limits are `null` for tomato, cucumber and potato until the
  sensor is calibrated, so irrigation is disabled for them.
- Humidity, `mean_daily_c` and CO2 are stored but not used yet.
- Pump timings and the tank and stale-data limits are placeholders to tune.
- The controller assumes commands were executed. ACK handling is not done yet.
- AI/ML integration is not implemented.
- Temperature uses one band for day and night.
