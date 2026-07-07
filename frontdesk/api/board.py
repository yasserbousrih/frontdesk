# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoints powering the desk-facing staff board (`/board`).

The board page is a tablet-optimized live view of today's bookings, grouped
by staff member. These endpoints are auth-gated (default Desk behavior);
walk-in customers hitting the public site don't reach this view.
"""

import frappe
from frappe.utils import today, nowtime


@frappe.whitelist()
def get_board_data():
    """Return today's bookings grouped by staff for the board view.

    Returns:
        list[dict]: one entry per active staff member, each with an extra
        ``bookings`` list of today's non-cancelled bookings (sorted by
        ``start_time``) augmented with ``customer_name`` and ``service_name``
        so the frontend can render without N+1 round-trips.
    """
    staff_list = frappe.get_all(
        "Staff Member",
        filters={"active": 1},
        fields=["name", "staff_name", "photo"],
        order_by="staff_name",
    )
    bookings = frappe.get_all(
        "Booking",
        filters={
            "staff": ["in", [s.name for s in staff_list]],
            "booking_date": today(),
            "status": ["not in", ["Cancelled", "No-Show"]],
        },
        fields=[
            "name", "customer", "start_time", "end_time",
            "service", "status", "price", "staff",
        ],
        order_by="start_time",
    )
    # Batch-load names to avoid N+1 queries
    customer_ids = {b["customer"] for b in bookings}
    service_ids = {b["service"] for b in bookings}
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
    for b in bookings:
        bookings_by_staff.setdefault(b["staff"], []).append(b)
    for s in staff_list:
        s.bookings = bookings_by_staff.get(s.name, [])
        for b in s.bookings:
            b["customer_name"] = customer_names.get(b["customer"], "")
            b["service_name"] = service_names.get(b["service"], "")
    return staff_list


@frappe.whitelist()
def add_walkin(staff, service):
    """Create a walk-in booking starting now.

    The Booking controller snapshots duration + price from the Service and
    enforces overlap rules, so a walk-in that collides with an existing
    booking will raise a ``ValidationError`` to the caller.

    Args:
        staff: Staff Member name.
        service: Service name.

    Returns:
        str: name of the newly-created Booking.
    """
    # Validate inputs early for clearer error messages than the doc-level checks.
    if not frappe.db.exists("Staff Member", staff):
        frappe.throw(f"Staff Member not found: {staff}")
    if not frappe.db.exists("Service", service):
        frappe.throw(f"Service not found: {service}")

    booking = frappe.get_doc({
        "doctype": "Booking",
        "customer": _ensure_walkin_customer(),
        "staff": staff,
        "service": service,
        "booking_date": today(),
        "start_time": nowtime(),
        "status": "Booked",
        "source": "Walk-in",
    })
    booking.insert(ignore_permissions=True)
    return booking.name


@frappe.whitelist()
def update_status(booking_name, status):
    """Update a booking's status from the board (Booked→Seated→In Progress→Completed).

    Args:
        booking_name: target Booking name.
        status: new status value (must be one of the Booking DocType's allowed options).

    Returns:
        str: the new status, echoed back for client convenience.
    """
    allowed = {"Booked", "Seated", "In Progress", "Completed", "Cancelled", "No-Show"}
    if status not in allowed:
        frappe.throw(f"Invalid status: {status}")

    booking = frappe.get_doc("Booking", booking_name)
    booking.status = status
    booking.save(ignore_permissions=True)
    return status


def _ensure_walkin_customer():
    """Get or create a generic walk-in customer record.

    A single shared ``Customer Profile`` named ``Walk-in Customer`` is used
    for all anonymous desk walk-ins so the Booking link stays valid. Identified
    by the sentinel phone value ``"walk-in"``.
    """
    name = frappe.db.get_value("Customer Profile", {"phone": "walk-in"}, "name")
    if name:
        return name
    return frappe.get_doc({
        "doctype": "Customer Profile",
        "customer_name": "Walk-in Customer",
        "phone": "walk-in",
    }).insert(ignore_permissions=True).name