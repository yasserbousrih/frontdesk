# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Context builder for the desk-facing checkout page (`/checkout`).

Renders the initial list of ``Completed`` bookings server-side so the cashier
sees the queue immediately, then refreshes via
``frontdesk.api.checkout.create_invoice`` once a payment is taken.
"""

import frappe

from ._branding import get_branding


def get_context(context):
    """Populate ``context`` for ``www/checkout.html``."""
    b = get_branding()

    context.business_name = b["brand_name"]
    context.primary_color = b["primary_color"]
    context.accent_color = b["accent_color"]
    context.currency = b["currency"]
    context.footer_powered = b["footer_powered"]
    context.copyright_text = b["copyright_text"]

    # --- Queue: completed bookings, most-recent first ---
    bookings = frappe.get_all(
        "Booking",
        filters={"status": "Completed"},
        fields=[
            "name", "customer", "staff", "service",
            "booking_date", "start_time", "price",
        ],
        order_by="booking_date desc, start_time desc",
        limit=50,
    )

    if bookings:
        customer_ids = {b["customer"] for b in bookings}
        service_ids = {b["service"] for b in bookings}
        staff_ids = {b["staff"] for b in bookings}
        customer_names = {
            r["name"]: r["customer_name"]
            for r in frappe.get_all("Customer Profile", filters={"name": ["in", list(customer_ids)]}, fields=["name", "customer_name"])
        }
        service_names = {
            r["name"]: r["service_name"]
            for r in frappe.get_all("Service", filters={"name": ["in", list(service_ids)]}, fields=["name", "service_name"])
        }
        staff_names = {
            r["name"]: r["staff_name"]
            for r in frappe.get_all("Staff Member", filters={"name": ["in", list(staff_ids)]}, fields=["name", "staff_name"])
        }
        for b in bookings:
            b["customer_name"] = customer_names.get(b["customer"], "")
            b["service_name"] = service_names.get(b["service"], "")
            b["staff_name"] = staff_names.get(b["staff"], "")
            b["start_time"] = _fmt_time(b.get("start_time"))

    context.bookings = bookings
    context.no_cache = 1


# ---------- helpers ----------

def _fmt_time(t):
    if not t:
        return ""
    if isinstance(t, str):
        return t[:5]
    return f"{t.hour:02d}:{t.minute:02d}"
