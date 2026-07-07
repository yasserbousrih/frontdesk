# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Scheduled reminder job — fires hourly via Frappe scheduler.

Finds bookings starting ~2 hours from now that haven't had a reminder sent,
and pushes a WhatsApp message via Omnichat.
"""

from datetime import datetime, timedelta

import frappe
import requests
from frappe.utils import now_datetime


def send_2h_reminders():
    """Entry point for the hourly scheduler.

    Looks for bookings on today's date whose start_time falls in a 90-150 min
    window from now. Skips cancelled/no-show and those already flagged
    ``reminder_sent``. Marks the flag after a successful (or attempted) send
    so the same booking is never reminded twice.
    """
    bs = frappe.get_single("Business Settings")
    if not (bs.get("omnichat_api_url") and bs.get("omnichat_api_token")):
        return  # WhatsApp not configured

    now = now_datetime()
    window_start = now + timedelta(minutes=90)
    window_end = now + timedelta(minutes=150)

    bookings = frappe.get_all(
        "Booking",
        filters={
            "booking_date": now.date(),
            "status": ["not in", ["Cancelled", "No-Show"]],
            "reminder_sent": 0,
        },
        fields=["name", "customer", "staff", "service", "booking_date", "start_time"],
    )

    for b in bookings:
        start = _to_datetime(b["booking_date"], b["start_time"])
        if start is None:
            continue
        if window_start <= start <= window_end:
            if _send_reminder(b, bs):
                frappe.db.set_value("Booking", b["name"], "reminder_sent", 1, update_modified=False)


def _send_reminder(booking, bs):
    """Send a single WhatsApp reminder for a booking."""
    customer = frappe.get_doc("Customer Profile", booking["customer"])
    if not customer.phone:
        return

    staff_name = frappe.db.get_value("Staff Member", booking["staff"], "staff_name")
    service_name = frappe.db.get_value("Service", booking["service"], "service_name")
    time_str = str(booking["start_time"])[:5]

    message = (
        f"⏰ Reminder\n\n"
        f"{service_name} with {staff_name}\n"
        f"🕐 {time_str} today\n\n"
        f"See you soon! — {bs.business_name}"
    )

    payload = {"to": customer.phone, "message": message}
    if bs.get("omnichat_sender_id"):
        payload["sender"] = bs.omnichat_sender_id

    try:
        resp = requests.post(
            bs.omnichat_api_url.rstrip("/") + "/send",
            headers={"Authorization": f"Bearer {bs.omnichat_api_token}", "Content-Type": "application/json"},
            json=payload, timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception:
        frappe.log_error(f"FrontDesk: 2h reminder failed for booking {booking['name']}")
        return False


def _to_datetime(booking_date, start_time):
    """Combine a date + time (which may be str or datetime.time) into datetime."""
    if isinstance(start_time, str):
        try:
            start_time = datetime.strptime(start_time, "%H:%M:%S").time()
        except ValueError:
            try:
                start_time = datetime.strptime(start_time, "%H:%M").time()
            except ValueError:
                return None
    try:
        return datetime.combine(booking_date, start_time)
    except (TypeError, AttributeError):
        return None
