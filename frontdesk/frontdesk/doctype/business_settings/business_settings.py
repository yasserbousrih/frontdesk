# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BusinessSettings(Document):
    """Single DocType holding the per-tenant site config.

    Branding fields drive the public booking website (Phase 1).
    booking_rules (slot buffer, cancellation window) drive the availability
    engine and the cancellation flow.
    """

    def is_open_now(self):
        """True if the current time falls within the configured Operating
        Hours for today. No operating_hours rows configured = always open.
        Mirrors back_house's BackHouseSettings.is_open_now so both apps
        enforce business hours the same way."""
        from frappe.utils import now_datetime

        rows = self.get("operating_hours") or []
        if not rows:
            return True
        now = now_datetime()
        # datetime.weekday(): Monday=0 .. Sunday=6
        day_map = {0: "Monday", 1: "Tuesday", 2: "Wednesday", 3: "Thursday", 4: "Friday", 5: "Saturday", 6: "Sunday"}
        today_name = day_map.get(now.weekday(), "Sunday")
        now_sec = float(now.hour * 3600 + now.minute * 60 + now.second)

        for row in rows:
            if row.get("day") == today_name and row.get("is_open"):
                ot = row.get("open_time") or "09:00:00"
                ct = row.get("close_time") or "23:00:00"

                def _sec(v):
                    if isinstance(v, str):
                        from frappe.utils import to_timedelta
                        return float(to_timedelta(v).total_seconds())
                    if hasattr(v, "total_seconds"):
                        return float(v.total_seconds())
                    return float(v.hour * 3600 + v.minute * 60 + v.second)

                o = _sec(ot)
                c = _sec(ct)
                # Overnight ranges (close < open) wrap past midnight.
                if o <= c:
                    if o <= now_sec <= c:
                        return True
                else:
                    if now_sec >= o or now_sec <= c:
                        return True
        return False
