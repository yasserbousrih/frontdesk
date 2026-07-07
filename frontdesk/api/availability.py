# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoints for the availability engine.

Every booking channel — web, WhatsApp, voice, walk-in — calls `get_available_slots`
first, so the same correctness guarantees apply to all of them. Guest-allowed
because the public website calls it before the customer has logged in.
"""

from datetime import datetime, time

import frappe
from frappe import _

from frontdesk.frontdesk.doctype.booking.overlap import (
    CANCELLED_STATES,
    compute_available_slots,
)


@frappe.whitelist(allow_guest=True)
def get_available_slots(staff: str, service: str, date: str) -> list:
    """Return a list of free slot start times for the given staff + service + date.

    Args:
        staff: name of the Staff Member DocType record.
        service: name of the Service DocType record.
        date: ISO date string (YYYY-MM-DD).

    Returns:
        List of {"start": "HH:MM", "start_iso": "<ISO datetime>"} dicts, sorted
        ascending. Empty list if the staff is off, the service is too long for
        the working window, or the day is fully booked.

    Raises:
        frappe.ValidationError: if staff or service is missing, inactive, or
        the date string is malformed.
    """
    if not frappe.db.exists("Staff Member", staff):
        frappe.throw(_("Staff member not found: {0}").format(staff))

    if not frappe.db.exists("Service", service):
        frappe.throw(_("Service not found: {0}").format(service))

    try:
        day = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        frappe.throw(_("Invalid date format. Use YYYY-MM-DD."))

    staff_doc = frappe.get_doc("Staff Member", staff)
    if not staff_doc.active:
        return []

    service_doc = frappe.get_doc("Service", service)
    if not service_doc.active:
        return []

    weekday = day.strftime("%A")
    working_hours = [
        (row.weekday, _time_to_minutes(row.start_time), _time_to_minutes(row.end_time))
        for row in staff_doc.working_hours
        if row.weekday == weekday
    ]
    if not working_hours:
        return []

    slot_buffer = 0
    if frappe.db.exists("DocType", "Business Settings"):
        bs = frappe.get_single("Business Settings")
        slot_buffer = int(bs.slot_buffer_minutes or 0)

    existing = frappe.get_all(
        "Booking",
        filters={
            "staff": staff,
            "booking_date": day,
            "status": ["not in", list(CANCELLED_STATES)],
        },
        fields=["start_time", "end_time"],
    )
    busy = [(_time_to_minutes(b.start_time), _time_to_minutes(b.end_time)) for b in existing]

    starts = compute_available_slots(
        working_hours=working_hours,
        service_duration_min=int(service_doc.duration_minutes),
        existing_bookings=busy,
        slot_buffer_min=slot_buffer,
    )

    # Format for the wire: HH:MM string + full ISO datetime.
    out = []
    for m in starts:
        h, mm = divmod(m, 60)
        out.append({
            "start": f"{h:02d}:{mm:02d}",
            "start_iso": datetime.combine(day, time(hour=h, minute=mm)).isoformat(),
        })
    return out


# ---------- internal helpers ----------

def _time_to_minutes(t) -> int:
    """Frappe `Time` value comes in as a `datetime.time` or string 'HH:MM:SS'."""
    if isinstance(t, str):
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    return t.hour * 60 + t.minute
