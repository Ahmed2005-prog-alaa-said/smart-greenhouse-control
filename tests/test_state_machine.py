from control_state_machine import (
    PumpStateMachine, IDLE, IRRIGATING, COOLDOWN, ERROR,
)


def test_starts_idle():
    assert PumpStateMachine().state == IDLE


def test_dry_soil_starts_irrigation():
    sm = PumpStateMachine()
    assert sm.update(0, True, True) == "ON"
    assert sm.state == IRRIGATING


def test_pump_stops_after_max_run():
    sm = PumpStateMachine()
    sm.update(0, True, True)
    assert sm.update(10, True, True) is None   # لسه شغالة
    assert sm.update(30, True, True) == "OFF"  # عدّت 30 ثانية
    assert sm.state == COOLDOWN


def test_cooldown_blocks_restart():
    sm = PumpStateMachine()
    sm.update(0, True, True)
    sm.update(30, True, True)
    # التربة لسه جافة، بس إحنا في استراحة: ممنوع تشتغل
    assert sm.update(40, True, True) is None
    assert sm.state == COOLDOWN


def test_back_to_idle_after_cooldown():
    sm = PumpStateMachine()
    sm.update(0, True, True)
    sm.update(30, True, True)
    sm.update(630, True, True)                 # خلصت الاستراحة
    assert sm.state == IDLE
    assert sm.update(631, True, True) == "ON"  # تقدر تشتغل تاني


def test_unsafe_stops_running_pump():
    sm = PumpStateMachine()
    sm.update(0, True, True)
    assert sm.update(5, True, False) == "OFF"
    assert sm.state == ERROR


def test_recovers_from_error():
    sm = PumpStateMachine()
    sm.update(0, True, False)
    sm.update(1, True, True)
    assert sm.state == IDLE
