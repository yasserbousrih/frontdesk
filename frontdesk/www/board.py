# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Context builder for the desk-facing staff board page (`/board`).

The page is rendered server-side once with the initial board snapshot so the
tablet sees something immediately; after that the frontend polls
``frontdesk.api.board.get_board_data`` every 15s for live updates.
"""

import frappe
from frappe.utils import today

from ._branding import get_branding


def get_context(context):
    """Populate ``context`` for ``www/board.html``."""
    b = get_branding()

    context.business_name = b["brand_name"]
    context.primary_color = b["primary_color"]
    context.accent_color = b["accent_color"]
    context.currency = b["currency"]
    context.footer_powered = b["footer_powered"]
    context.copyright_text = b["copyright_text"]

    # --- Board snapshot: staff + today's non-cancelled bookings ---
    today_str = today()
    staff_rows = frappe.get_all(
        "Staff Member",
        filters={"active": 1},
        fields=["name", "staff_name", "photo"],
        order_by="staff_name",
    )

    all_bookings = frappe.get_all(
        "Booking",
        filters={
            "staff": ["in", [s.name for s in staff_rows]],
            "booking_date": today_str,
            "status": ["not in", ["Cancelled", "No-Show"]],
        },
        fields=["name", "customer", "start_time", "end_time", "service", "status", "price", "staff"],
        order_by="start_time",
    )

    # Batch-load names to avoid N+1
    customer_ids = {b["customer"] for b in all_bookings}
    service_ids = {b["service"] for b in all_bookings}
    customer_names = {
        r["name"]: r["customer_name"]
        for r in frappe.get_all("Customer Profile", filters={"name": ["in", list(customer_ids)]}, fields=["name", "customer_name"])
    }
    service_names = {
        r["name"]: r["service_name"]
        for r in frappe.get_all("Service", filters={"name": ["in", list(service_ids)]}, fields=["name", "service_name"])
    }

    # Group by staff
    bookings_by_staff = {}
    for b in all_bookings:
        b["customer_name"] = customer_names.get(b["customer"], "")
        b["service_name"] = service_names.get(b["service"], "")
        b["start_time"] = _fmt_time(b["start_time"])
        b["end_time"] = _fmt_time(b.get("end_time"))
        bookings_by_staff.setdefault(b["staff"], []).append(b)

    board_data = []
    for s in staff_rows:
        s["bookings"] = bookings_by_staff.get(s.name, [])
        board_data.append(s)

    context.board_data = board_data

    # --- Services for the per-column "Add Walk-in" form ---
    context.services = frappe.get_all(
        "Service",
        filters={"active": 1},
        fields=["name", "service_name", "duration_minutes", "price"],
        order_by="service_name",
    )

    context.today = today_str
    context.no_cache = 1


# ---------- helpers ----------

def _fmt_time(t):
    """Coerce a Frappe Time value to ``"HH:MM"``."""
    if not t:
        return ""
    if isinstance(t, str):
        return t[:5]
    return f"{t.hour:02d}:{t.minute:02d}"
