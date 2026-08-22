# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import add_days, today

from ._branding import get_branding


def get_context(context):
    context.no_cache = 1
    b = get_branding()
    context.business = b

    staff = None
    staff_param = frappe.form_dict.get("staff")

    # 1. If staff param provided and exists
    if staff_param and frappe.db.exists("Staff Member", staff_param):
        staff = staff_param
    # 2. If logged in as a user linked to a Staff Member
    elif frappe.session.user != "Guest":
        staff = frappe.db.get_value("Staff Member", {"user": frappe.session.user}, "name")

    # 3. Fallback: if no staff identified, pick first active staff or allow picker
    all_staff = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name", "staff_name", "photo"], order_by="staff_name")
    context.all_staff = all_staff

    if not staff and all_staff:
        staff = all_staff[0].name

    if not staff:
        context.staff_name = "Staff Member"
        context.today_bookings = []
        context.upcoming_bookings = []
        return context

    context.current_staff_id = staff
    context.staff_name = frappe.db.get_value("Staff Member", staff, "staff_name")
    context.staff_photo = frappe.db.get_value("Staff Member", staff, "photo")

    # Today's bookings
    context.today_bookings = _get_bookings(staff, today(), today())
    # Upcoming (next 7 days, excluding today)
    context.upcoming_bookings = _get_bookings(staff, add_days(today(), 1), add_days(today(), 7))
    return context


def _get_bookings(staff, from_date, to_date):
    bookings = frappe.get_all(
        "Booking",
        filters={
            "staff": staff,
            "booking_date": ["between", [from_date, to_date]],
            "status": ["not in", ["Cancelled", "No-Show"]],
        },
        fields=["name", "customer", "service", "booking_date", "start_time", "end_time", "status", "station", "price", "deposit_amount", "deposit_paid"],
        order_by="booking_date asc, start_time asc",
    )
    if not bookings:
        return []

    # Batch-load customer data & tech notes
    customer_ids = {b["customer"] for b in bookings}
    customers = {
        r["name"]: r
        for r in frappe.get_all(
            "Customer Profile",
            filters={"name": ["in", list(customer_ids)]},
            fields=["name", "customer_name", "phone", "technical_notes"],
        )
    }

    # Batch-load child services
    child_services = frappe.get_all(
        "Booking Service",
        filters={"parent": ["in", [b["name"] for b in bookings]]},
        fields=["parent", "service_name", "service", "price", "duration_minutes"],
    )
    cs_map = {}
    for cs in child_services:
        cs_map.setdefault(cs["parent"], []).append(cs)

    # Batch-load service items
    service_ids = {b["service"] for b in bookings if b.get("service")}
    service_names = {
        r["name"]: r["item_name"]
        for r in frappe.get_all("Item", filters={"name": ["in", list(service_ids)]}, fields=["name", "item_name"])
    }

    for b in bookings:
        c_info = customers.get(b.customer, {})
        b.customer_name = c_info.get("customer_name") or b.customer
        b.customer_phone = c_info.get("phone") or ""
        b.technical_notes = c_info.get("technical_notes") or ""

        children = cs_map.get(b.name, [])
        if children:
            b.service_name = " + ".join(cs["service_name"] for cs in children)
            b.services_list = children
        else:
            b.service_name = service_names.get(b.service, "")
            b.services_list = []

    return bookings
