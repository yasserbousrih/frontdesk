# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Context builder for the desk-facing checkout page (`/checkout`).

Renders the initial list of ``Completed`` bookings server-side so the cashier
sees the queue immediately, then refreshes via
``frontdesk.api.checkout.create_invoice`` once a payment is taken.
"""

import frappe


def get_context(context):
    """Populate ``context`` for ``www/checkout.html``.

    Pulls:
      * branding from the ``Business Settings`` single
      * the 50 most recent ``Completed`` bookings awaiting checkout
    """
    # --- Branding (same fallbacks as the board page) ---
    settings = _safe_single("Business Settings") or {}
    context.business_name = settings.get("business_name") or "FrontDesk"
    context.primary_color = settings.get("primary_color") or "#1f2937"
    context.accent_color = settings.get("accent_color") or "#f59e0b"
    context.currency = settings.get("currency") or "QAR"

    # --- Queue: completed bookings, most-recent first ---
    bookings = frappe.get_all(
        "Booking",
        filters={"status": "Completed"},
        fields=[
            "name",
            "customer",
            "staff",
            "service",
            "booking_date",
            "start_time",
            "price",
        ],
        order_by="booking_date desc, start_time desc",
        limit=50,
    )

    for b in bookings:
        b["customer_name"] = frappe.db.get_value(
            "Customer Profile", b["customer"], "customer_name"
        )
        b["service_name"] = frappe.db.get_value(
            "Service", b["service"], "service_name"
        )
        b["staff_name"] = frappe.db.get_value(
            "Staff Member", b["staff"], "staff_name"
        )
        b["start_time"] = _fmt_time(b.get("start_time"))

    context.bookings = bookings
    context.no_cache = 1


# ---------- helpers ----------

def _safe_single(doctype):
    """Return the single DocType as a dict, or ``None`` if not installed."""
    try:
        return frappe.get_single(doctype).as_dict()
    except Exception:
        return None


def _fmt_time(t):
    """Coerce a Frappe Time value to ``"HH:MM"`` (empty string if missing)."""
    if not t:
        return ""
    if isinstance(t, str):
        return t[:5]
    return f"{t.hour:02d}:{t.minute:02d}"