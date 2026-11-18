# ===== حالات المضخة =====
IDLE = "IDLE"              # واقفة وجاهزة
IRRIGATING = "IRRIGATING"  # شغالة
COOLDOWN = "COOLDOWN"      # استراحة عشان التربة تمتص المياه
ERROR = "ERROR"            # في مشكلة أمان

# أرقام تجريبية (بالثواني). هنجيبها من ملف النبات بعدين.
MAX_RUN_SECONDS = 30       # أقصى مدة تشغيل متواصل
COOLDOWN_SECONDS = 600     # مدة الاستراحة بعد كل ري


class PumpStateMachine:
    """
    بتتابع حالة المضخة وتقرر إيه الأمر اللي يتبعت.
    update() بترجّع "ON" أو "OFF" أو None (يعني مفيش أمر جديد).
    """

    def __init__(self):
        self.state = IDLE
        self.since = 0  # وقت دخول الحالة الحالية

    def update(self, now, wants_water, safe):
        """
        now:         الوقت الحالي بالثواني
        wants_water: هل التربة محتاجة ري؟
        safe:        هل القراءة آمنة؟
        """
        # لو مش آمن: ادخل ERROR، ولو المضخة شغالة اطفيها
        if not safe:
            was_running = self.state == IRRIGATING
            self.state = ERROR
            self.since = now
            return "OFF" if was_running else None

        # رجع الأمان: نرجع للانتظار
        if self.state == ERROR:
            self.state = IDLE
            self.since = now
            return None

        # واقفة: لو محتاجة مياه شغّلها
        if self.state == IDLE:
            if wants_water:
                self.state = IRRIGATING
                self.since = now
                return "ON"
            return None

        # شغالة: اطفيها لو التربة اترطبت أو عدّت أقصى مدة
        if self.state == IRRIGATING:
            if (not wants_water) or (now - self.since >= MAX_RUN_SECONDS):
                self.state = COOLDOWN
                self.since = now
                return "OFF"
            return None

        # استراحة: استنى لحد ما المدة تخلص
        if self.state == COOLDOWN:
            if now - self.since >= COOLDOWN_SECONDS:
                self.state = IDLE
                self.since = now
            return None
