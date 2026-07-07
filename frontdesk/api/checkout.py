# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoint powering the desk-facing checkout screen (`/checkout`).

Checkout takes a completed booking, ensures an ERPNext ``Customer`` and ``Item``
exist for the relevant entities, submits a ``Sales Invoice``, and marks the
booking ``Paid``. Intended for the Frontdesk role on the bench / POS machine.
"""

import frappe


@frappe.whitelist()
def create_invoice(booking_name, payment_method="Cash"):
    """Create an ERPNext Sales Invoice for a completed booking and mark it Paid.

    Args:
        booking_name: target Booking name.
        payment_method: one of ``Cash``, ``Card``, ``Transfer`` (informational
            only here — payment recording happens in the ERPNext Payment Entry
            when the cashier settles the Sales Invoice; we accept the hint so
            the frontend can stamp it for the receipt).

    Returns:
        dict: ``{"sales_invoice": "<name>", "booking": "<name>"}`` so the
        frontend can show a confirmation and refresh the queue.

    Raises:
        frappe.ValidationError: if the booking isn't in a ``Completed`` state
            or ERPNext rejects the invoice (e.g. missing default accounts).
    """
    if payment_method not in {"Cash", "Card", "Transfer"}:
        frappe.throw(f"Unsupported payment method: {payment_method}")

    booking = frappe.get_doc("Booking", booking_name)
    if booking.status not in {"Completed", "Paid"}:
        frappe.throw(
            f"Booking {booking_name} is in status '{booking.status}'; "
            "only Completed bookings can be checked out."
        )

    # Ensure ERPNext Customer exists
    customer = _ensure_customer(booking.customer)
    # Ensure Item exists for the service
    item = _ensure_item(booking.service)

    si = frappe.get_doc({
        "doctype": "Sales Invoice",
        "customer": customer,
        "items": [{"item_code": item, "qty": 1, "rate": booking.price}],
        # Stash the payment method on the invoice's remarks so the cashier
        # sees it when posting payment (a richer integration would create a
        # Payment Entry here, but that's out of scope for the desk screen).
        "remarks": f"Booking {booking_name} — Payment method: {payment_method}",
    })
    # Attach loyalty program so ERPNext auto-calculates points on submit
    if frappe.db.exists("DocType", "Loyalty Program") and frappe.db.exists("Loyalty Program", "FrontDesk Rewards"):
        si.loyalty_program = "FrontDesk Rewards"
    si.insert(ignore_permissions=True)
    si.submit()

    # Mark booking as Paid
    booking.status = "Paid"
    booking.save(ignore_permissions=True)
    return {"sales_invoice": si.name, "booking": booking.name}


def _ensure_customer(customer_profile):
    """Get or create an ERPNext Customer linked to a Customer Profile.

    Mirrors the link on the Customer Profile DocType (``erpnext_customer``)
    so subsequent checkouts skip the create step.
    """
    cp = frappe.get_doc("Customer Profile", customer_profile)
    if cp.erpnext_customer and frappe.db.exists("Customer", cp.erpnext_customer):
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


def _enroll_loyalty(customer_name):
    """Enroll an ERPNext Customer in the FrontDesk Rewards loyalty program."""
    # Guard: Loyalty Program is an ERPNext doctype — skip if ERPNext not installed
    if not frappe.db.exists("DocType", "Loyalty Program"):
        return
    if not frappe.db.exists("Loyalty Program", "FrontDesk Rewards"):
        return
    frappe.db.set_value("Customer", customer_name, "loyalty_program", "FrontDesk Rewards")


def _ensure_item(service_name):
    """Get or create an ERPNext Item for a Frontdesk Service.

    Uses the Service name as the item code (Service names are unique on the
    DocType, so this is stable across calls). Items are non-stock and seeded
    with the Service's price as the standard rate.
    """
    if frappe.db.exists("Item", service_name):
        return service_name

    svc = frappe.get_doc("Service", service_name)
    item = frappe.get_doc({
        "doctype": "Item",
        "item_code": service_name,
        "item_name": svc.service_name,
        "stock_uom": "Nos",
        "is_stock_item": 0,
        "item_group": "Services",
        "standard_rate": svc.price,
    }).insert(ignore_permissions=True)
    return item.name