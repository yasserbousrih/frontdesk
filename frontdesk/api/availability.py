# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoints for the availability engine.

Every booking channel — web, WhatsApp, voice, walk-in — calls `get_available_slots`
first, so the same correctness guarantees apply to all of them. Guest-allowed
because the public website calls it before the customer has logged in.
"""

from datetime import datetime, time, timedelta
import json

import frappe
from frappe import _

from frontdesk.frontdesk.doctype.booking.overlap import (
    CANCELLED_STATES,
    compute_available_slots,
)


@frappe.whitelist(allow_guest=True)
def get_available_slots(
    staff: str = "",
    service: str = "",
    date: str = "",
    services=None,
    duration_minutes=None,
) -> list:
    """Return a list of free slot start times for the given staff + service(s) + date.

    Args:
        staff: name of the Staff Member DocType record. If empty/blank, slots
            are aggregated across ALL active staff members: a start time is
            available if at least one active staff member can serve it.
        service: name of single Item record (for backwards compatibility).
        date: ISO date string (YYYY-MM-DD).
        services: JSON string, comma-separated string, or list of Item records for multi-service.
        duration_minutes: explicit duration override in minutes.

    Returns:
        List of {"start": "HH:MM", "start_iso": "<ISO datetime>"} dicts, sorted
        ascending. Empty list if no staff can serve the slot (staff off, service
        too long for the working window, or the day fully booked).
    """
    if staff and staff.strip():
        if not frappe.db.exists("Staff Member", staff):
            frappe.throw(_("Staff member not found: {0}").format(staff))

    try:
        day = datetime.strptime(date, "%Y-%m-%d").date()
    except (ValueError, TypeError):
        frappe.throw(_("Invalid date format. Use YYYY-MM-DD."))

    weekday = day.strftime("%A")

    # Determine services list & total duration
    service_list = []
    if services:
        if isinstance(services, str):
            services_str = services.strip()
            if services_str.startswith("[") and services_str.endswith("]"):
                try:
                    service_list = json.loads(services_str)
                except Exception:
                    service_list = [s.strip().strip("'\"") for s in services_str.strip("[]").split(",") if s.strip()]
            elif "," in services_str:
                service_list = [s.strip() for s in services_str.split(",") if s.strip()]
            else:
                service_list = [services_str]
        elif isinstance(services, (list, tuple)):
            service_list = list(services)
    elif service and service.strip():
        service_list = [service.strip()]

    total_duration = 0
    if duration_minutes:
        try:
            total_duration = int(duration_minutes)
        except (ValueError, TypeError):
            total_duration = 0

    if total_duration <= 0 and service_list:
        for s in service_list:
            if not frappe.db.exists("Item", s):
                frappe.throw(_("Service not found: {0}").format(s))
            svc_doc = frappe.get_doc("Item", s)
            if svc_doc.disabled:
                return []
            total_duration += int(svc_doc.duration_minutes or 0)
    elif total_duration <= 0 and not service_list:
        frappe.throw(_("Please provide a service, services list, or duration."))

    if total_duration <= 0:
        total_duration = 15  # Fallback minimum duration

    slot_buffer = 0
    if frappe.db.exists("DocType", "Business Settings"):
        bs = frappe.get_single("Business Settings")
        slot_buffer = int(bs.slot_buffer_minutes or 0)

    if staff and staff.strip():
        starts = _slots_for_staff(staff, total_duration, day, weekday, slot_buffer)
    else:
        active_staff = frappe.get_all(
            "Staff Member", filters={"active": 1}, pluck="name"
        )
        starts = sorted({
            m
            for s in active_staff
            for m in _slots_for_staff(s, total_duration, day, weekday, slot_buffer)
        })

    out = []
    for m in starts:
        h, mm = divmod(m, 60)
        out.append({
            "start": f"{h:02d}:{mm:02d}",
            "start_iso": datetime.combine(day, time(hour=h, minute=mm)).isoformat(),
        })
    return out


# ---------- internal helpers ----------

def _slots_for_staff(staff_name: str, duration_min: int, day, weekday: str, slot_buffer: int) -> list:
    """Compute the available slot start-minutes for ONE staff member with a specified duration."""
    staff_doc = frappe.get_doc("Staff Member", staff_name)
    if not staff_doc.active:
        return []

    working_hours = [
        (row.weekday, _time_to_minutes(row.start_time), _time_to_minutes(row.end_time))
        for row in staff_doc.working_hours
        if row.weekday == weekday
    ]
    if not working_hours:
        return []

    existing = frappe.get_all(
        "Booking",
        filters={
            "staff": staff_name,
            "booking_date": day,
            "status": ["not in", list(CANCELLED_STATES)],
        },
        fields=["start_time", "end_time"],
    )
    busy = [(_time_to_minutes(b.start_time), _time_to_minutes(b.end_time)) for b in existing]

    return compute_available_slots(
        working_hours=working_hours,
        service_duration_min=duration_min,
        existing_bookings=busy,
        slot_buffer_min=slot_buffer,
    )


def _time_to_minutes(t) -> int:
    """Frappe `Time` value comes in as a `datetime.time`, `datetime.timedelta`
    (hours since midnight, as newer frappe returns for Time columns), or a
    string 'HH:MM:SS'. Normalize all three to minutes since midnight."""
    if isinstance(t, str):
        parts = t.split(":")
        return int(parts[0]) * 60 + int(parts[1])
    if isinstance(t, timedelta):
        return int(t.total_seconds() // 60)
    return t.hour * 60 + t.minute
