# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoint powering the desk-facing checkout screen.

Checkout takes a completed booking, adds it plus any extras to an ERPNext
Sales Invoice, applies optional discount / tip, submits, and marks the booking
Paid. Intended for the Frontdesk role on the bench / POS machine.
"""

import json

import frappe
from frappe.utils import flt


@frappe.whitelist()
def create_invoice(
    booking_name,
    payment_method="Cash",
    extra_items="[]",
    discount_pct=0,
    tip=0,
):
    """Create an ERPNext Sales Invoice for a booking and mark it Paid.

    Args:
        booking_name: target Booking name.
        payment_method: ``Cash``, ``Card``, or ``Transfer``.
        extra_items: JSON list of ``{"item_code", "qty", "rate"}`` dicts
            for add‑on products / extra services.
        discount_pct: percentage discount applied to the invoice total
            via ERPNext's ``additional_discount_percentage``.
        tip: monetary tip amount added as a non‑stock charge item.

    Returns:
        dict: ``{"sales_invoice": "<name>", "booking": "<name>"}``.
    """
    # ---- validate ----
    if payment_method not in {"Cash", "Card", "Transfer"}:
        frappe.throw(f"Unsupported payment method: {payment_method}")

    if not frappe.db.exists("DocType", "Sales Invoice"):
        frappe.throw(
            "ERPNext is required for checkout. Install the 'erpnext' app first."
        )

    booking = frappe.get_doc("Booking", booking_name)
    if booking.status == "Paid":
        frappe.throw(
            f"Booking {booking_name} already has a Sales Invoice — "
            "duplicate checkout prevented."
        )
    if booking.status != "Completed":
        frappe.throw(
            f"Booking {booking_name} is in status '{booking.status}'; "
            "only Completed bookings can be checked out."
        )

    extra_items = _parse_json(extra_items, default=[])
    discount_pct = flt(discount_pct)
    tip = flt(tip)

    # ---- ensure ERPNext records exist ----
    customer = _ensure_customer(booking.customer)
    staff_member = booking.staff

    # ---- build Sales Invoice ----
    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "company": frappe.db.get_single_value(
            "Global Defaults", "default_company"
        ),
        "items": _build_items(
            booking.service, booking.price, staff_member,
            extra_items, tip,
        ),
        "additional_discount_percentage": discount_pct,
        "remarks": (
            f"Booking {booking_name} — Payment method: {payment_method}"
        ),
    })

    _attach_loyalty(si)
    si.insert(ignore_permissions=True)

    # Payment details for receipt printing (epson_middleware reads this table)
    mode_map = {"Cash": "Cash", "Card": "Credit Card", "Transfer": "Bank Transfer"}
    si.append("payments", {
        "mode_of_payment": mode_map.get(payment_method, "Cash"),
        "amount": si.grand_total,
    })

    si.submit()

    booking.status = "Paid"
    booking.save(ignore_permissions=True)
    return {"sales_invoice": si.name, "booking": booking.name}


# ---------- item builder ----------

def _build_items(service_name, service_price, staff_member, extra_items, tip):
    """Return the list of Sales Invoice Item dicts."""
    items = []

    # 1. Primary service from the booking — the Item code IS the service name
    items.append({
        "item_code": service_name,
        "qty": 1,
        "rate": service_price,
        "staff_member": staff_member,
    })

    # 2. Extra items (add‑on products, additional services)
    for ei in extra_items:
        code = ei.get("item_code", "").strip()
        if not code:
            continue
        qty = flt(ei.get("qty", 1))
        rate = flt(ei.get("rate", 0))
        if rate <= 0:
            rate = flt(frappe.db.get_value("Item", code, "standard_rate") or 0)
        items.append({
            "item_code": code,
            "qty": qty,
            "rate": rate,
            "staff_member": staff_member,
        })

    # 3. Tip — non‑stock charge item (create if it doesn't exist)
    if tip > 0:
        tip_item = _ensure_tip_item()
        items.append({
            "item_code": tip_item,
            "qty": 1,
            "rate": tip,
        })

    return items


# ---------- ERPNext record helpers ----------

def _ensure_customer(customer_profile):
    """Get or create an ERPNext Customer linked to a Customer Profile."""
    cp = frappe.get_doc("Customer Profile", customer_profile)
    if cp.erpnext_customer and frappe.db.exists(
        "Customer", cp.erpnext_customer
    ):
        return cp.erpnext_customer

    cust = frappe.get_doc({
        "doctype": "Customer",
        "customer_name": cp.customer_name,
        "customer_group": "All Customer Groups",
        "territory": "All Territories",
    }).insert(ignore_permissions=True)
    cp.db_set("erpnext_customer", cust.name)
    _enroll_loyalty(cust.name)
    return cust.name


def _ensure_tip_item():
    """Get or create a non‑stock 'Tip' Item for gratuity line items."""
    if frappe.db.exists("Item", "Tip"):
        return "Tip"
    frappe.get_doc({
        "doctype": "Item",
        "item_code": "Tip",
        "item_name": "Tip / Gratuity",
        "stock_uom": "Nos",
        "is_stock_item": 0,
        "item_group": "Services",
    }).insert(ignore_permissions=True)
    return "Tip"


def _enroll_loyalty(customer_name):
    """Enroll an ERPNext Customer in the FrontDesk Rewards loyalty program."""
    if not frappe.db.exists("DocType", "Loyalty Program"):
        return
    if not frappe.db.exists("Loyalty Program", "FrontDesk Rewards"):
        return
    frappe.db.set_value(
        "Customer", customer_name, "loyalty_program", "FrontDesk Rewards"
    )


def _attach_loyalty(si):
    """Attach FrontDesk Rewards to a Sales Invoice if loyalty is available."""
    if frappe.db.exists("DocType", "Loyalty Program") and frappe.db.exists(
        "Loyalty Program", "FrontDesk Rewards"
    ):
        si.loyalty_program = "FrontDesk Rewards"


# ---------- util ----------

def _parse_json(raw, default):
    """Safely parse a JSON string; return *default* on failure."""
    if not raw:
        return default
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return default
