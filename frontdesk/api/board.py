# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Whitelisted REST endpoints powering the desk-facing staff board (`/board`).

The board page is a tablet-optimized live view of today's bookings, grouped
by staff member. Supports fast walk-in seating, customer technical notes,
past visit lookup, and daily cash-out reporting.
"""

import json
import frappe
from frappe.utils import flt, nowtime, today


@frappe.whitelist()
def get_board_data():
    """Return today's bookings grouped by staff for the board view."""
    staff_list = frappe.get_all(
        "Staff Member",
        filters={"active": 1},
        fields=["name", "staff_name", "photo", "commission_pct"],
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
            "service", "status", "price", "staff", "duration_minutes", "station",
        ],
        order_by="start_time",
    )
    customer_ids = {b["customer"] for b in bookings}
    service_ids = {b["service"] for b in bookings}

    customers = {
        r["name"]: r
        for r in frappe.get_all(
            "Customer Profile",
            filters={"name": ["in", list(customer_ids)]},
            fields=["name", "customer_name", "phone", "technical_notes"],
        )
    }
    service_names = {
        r["name"]: r["item_name"]
        for r in frappe.get_all("Item", filters={"name": ["in", list(service_ids)]}, fields=["name", "item_name"])
    }
    service_names_ar = {
        r["name"]: r["item_name_ar"] or ""
        for r in frappe.get_all("Item", filters={"name": ["in", list(service_ids)]}, fields=["name", "item_name_ar"])
    }

    # Also load child services if any
    child_services = frappe.get_all(
        "Booking Service",
        filters={"parent": ["in", [b["name"] for b in bookings]]},
        fields=["parent", "service", "service_name", "price", "duration_minutes"],
    )
    child_services_by_booking = {}
    for cs in child_services:
        child_services_by_booking.setdefault(cs["parent"], []).append(cs)

    bookings_by_staff = {}
    for b in bookings:
        c_info = customers.get(b["customer"], {})
        b["customer_name"] = c_info.get("customer_name") or b["customer"]
        b["customer_phone"] = c_info.get("phone") or ""
        b["technical_notes"] = c_info.get("technical_notes") or ""

        b_children = child_services_by_booking.get(b["name"], [])
        if b_children:
            b["service_name"] = " + ".join(cs["service_name"] for cs in b_children)
            b["services_list"] = b_children
        else:
            b["service_name"] = service_names.get(b["service"], "")
            b["service_name_ar"] = service_names_ar.get(b["service"], "")
            b["services_list"] = []

        bookings_by_staff.setdefault(b["staff"], []).append(b)

    for s in staff_list:
        s.bookings = bookings_by_staff.get(s.name, [])

    return staff_list


@frappe.whitelist()
def get_stations():
    """Return active stations/rooms for selection."""
    return frappe.get_all(
        "Service Station",
        filters={"active": 1},
        fields=["name", "station_name", "station_type", "description"],
        order_by="station_name",
    )


@frappe.whitelist()
def add_walkin(staff, service=None, services=None, customer_name=None, phone=None, status="In Progress", start_time=None, station=None):
    """Create a walk-in booking starting now or at a specified time."""
    if not frappe.db.exists("Staff Member", staff):
        frappe.throw(f"Staff Member not found: {staff}")

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
    elif service:
        service_list = [service]

    if not service_list:
        frappe.throw("Please select at least one service.")

    for s in service_list:
        if not frappe.db.exists("Item", s):
            frappe.throw(f"Service not found: {s}")

    # Resolve or create customer
    if phone and phone.strip():
        clean_phone = phone.strip()
        existing = frappe.db.get_value("Customer Profile", {"phone": clean_phone}, "name")
        if existing:
            customer = existing
            if customer_name and not frappe.db.get_value("Customer Profile", existing, "customer_name"):
                frappe.db.set_value("Customer Profile", existing, "customer_name", customer_name.strip())
        else:
            customer = frappe.get_doc({
                "doctype": "Customer Profile",
                "customer_name": customer_name.strip() if customer_name else "Walk-in",
                "phone": clean_phone,
            }).insert(ignore_permissions=True).name
    elif customer_name and customer_name.strip():
        customer = frappe.get_doc({
            "doctype": "Customer Profile",
            "customer_name": customer_name.strip(),
            "phone": f"walkin-{frappe.generate_hash(length=8)}",
        }).insert(ignore_permissions=True).name
    else:
        customer = _ensure_walkin_customer()

    total_duration = sum(int(frappe.db.get_value("Item", s, "duration_minutes") or 0) for s in service_list)
    if total_duration <= 0:
        total_duration = 15
    total_rate = sum(flt(frappe.db.get_value("Item", s, "standard_rate") or 0) for s in service_list)

    child_services = [
        {
            "service": s,
            "service_name": frappe.db.get_value("Item", s, "item_name") or s,
            "duration_minutes": int(frappe.db.get_value("Item", s, "duration_minutes") or 0),
            "price": flt(frappe.db.get_value("Item", s, "standard_rate") or 0),
        }
        for s in service_list
    ]

    valid_statuses = {"Booked", "Seated", "In Progress"}
    booking_status = status if status in valid_statuses else "In Progress"

    booking = frappe.get_doc({
        "doctype": "Booking",
        "customer": customer,
        "staff": staff,
        "station": station or "",
        "service": service_list[0],
        "booking_date": today(),
        "start_time": start_time or nowtime(),
        "status": booking_status,
        "source": "Walk-in",
        "duration_minutes": total_duration,
        "price": total_rate,
        "services": child_services,
    })
    booking.insert(ignore_permissions=True)
    return {
        "name": booking.name,
        "status": booking.status,
        "customer": customer,
        "customer_name": frappe.db.get_value("Customer Profile", customer, "customer_name"),
        "service": " + ".join(s["service_name"] for s in child_services),
        "price": total_rate,
        "duration_minutes": total_duration,
    }


@frappe.whitelist()
def update_status(booking_name, status):
    """Update a booking's status from the board."""
    allowed = {"Booked", "Seated", "In Progress", "Completed", "Cancelled", "No-Show"}
    if status not in allowed:
        frappe.throw(f"Invalid status: {status}")

    booking = frappe.get_doc("Booking", booking_name)
    booking.status = status
    booking.save(ignore_permissions=True)
    return status


@frappe.whitelist()
def get_customer_card(customer_id):
    """Return customer profile details, technical notes, and past visits history."""
    if not frappe.db.exists("Customer Profile", customer_id):
        frappe.throw(f"Customer Profile not found: {customer_id}")

    cp = frappe.get_doc("Customer Profile", customer_id)
    pref_staff_name = frappe.db.get_value("Staff Member", cp.preferred_staff, "staff_name") if cp.preferred_staff else ""

    past_bookings = frappe.get_all(
        "Booking",
        filters={
            "customer": customer_id,
            "status": ["in", ["Completed", "Paid"]],
        },
        fields=["name", "booking_date", "start_time", "service", "staff", "price", "status"],
        order_by="booking_date desc, start_time desc",
        limit=6,
    )
    for b in past_bookings:
        b["staff_name"] = frappe.db.get_value("Staff Member", b["staff"], "staff_name") or b["staff"]
        b["service_name"] = frappe.db.get_value("Item", b["service"], "item_name") or b["service"]
        b["date"] = str(b["booking_date"])
        b["time"] = str(b["start_time"])[:5]

    total_completed = frappe.db.count("Booking", filters={"customer": customer_id, "status": ["in", ["Completed", "Paid"]]})

    return {
        "name": cp.name,
        "customer_name": cp.customer_name,
        "phone": cp.phone,
        "email": cp.email,
        "preferred_staff": cp.preferred_staff,
        "preferred_staff_name": pref_staff_name,
        "technical_notes": cp.technical_notes or "",
        "notes": cp.notes or "",
        "total_visits": total_completed,
        "past_visits": past_bookings,
    }


@frappe.whitelist()
def update_customer_technical_notes(customer_id, technical_notes):
    """Save formula / technical notes (e.g. hair fade, beard style, allergy) on Customer Profile."""
    if not frappe.db.exists("Customer Profile", customer_id):
        frappe.throw(f"Customer Profile not found: {customer_id}")

    frappe.db.set_value("Customer Profile", customer_id, "technical_notes", technical_notes)
    return {"ok": True, "technical_notes": technical_notes}


@frappe.whitelist()
def get_daily_summary(date=None):
    """Return daily closing summary with revenue, tickets, and staff commissions."""
    target_date = date or today()

    staff_members = frappe.get_all(
        "Staff Member",
        filters={"active": 1},
        fields=["name", "staff_name", "photo", "commission_pct"],
        order_by="staff_name",
    )

    bookings = frappe.get_all(
        "Booking",
        filters={"booking_date": target_date},
        fields=["name", "staff", "service", "status", "price", "source"],
    )

    total_tickets = len(bookings)
    completed_tickets = [b for b in bookings if b.status in ("Completed", "Paid")]
    cancelled_tickets = [b for b in bookings if b.status == "Cancelled"]
    noshow_tickets = [b for b in bookings if b.status == "No-Show"]

    gross_revenue = sum(flt(b.price or 0) for b in completed_tickets)

    staff_summary = []
    for s in staff_members:
        s_completed = [b for b in completed_tickets if b.staff == s.name]
        s_gross = sum(flt(b.price or 0) for b in s_completed)
        comm_pct = flt(s.commission_pct or 0)
        comm_amount = (s_gross * comm_pct) / 100.0 if comm_pct > 0 else 0.0

        staff_summary.append({
            "staff_id": s.name,
            "staff_name": s.staff_name,
            "photo": s.photo,
            "completed_count": len(s_completed),
            "gross_revenue": s_gross,
            "commission_pct": comm_pct,
            "commission_amount": comm_amount,
        })

    # Payment modes breakdown from Sales Invoices on that date
    si_payments = []
    if frappe.db.exists("DocType", "Sales Invoice"):
        si_list = frappe.get_all(
            "Sales Invoice",
            filters={"posting_date": target_date, "docstatus": 1},
            pluck="name",
        )
        if si_list:
            payments_data = frappe.get_all(
                "Sales Invoice Payment",
                filters={"parent": ["in", si_list]},
                fields=["mode_of_payment", "amount"],
            )
            mode_totals = {}
            for p in payments_data:
                mop = p.mode_of_payment or "Cash"
                mode_totals[mop] = mode_totals.get(mop, 0.0) + flt(p.amount)
            for mop, amt in mode_totals.items():
                si_payments.append({"mode_of_payment": mop, "amount": amt})

    return {
        "date": str(target_date),
        "total_tickets": total_tickets,
        "completed_tickets": len(completed_tickets),
        "cancelled_tickets": len(cancelled_tickets),
        "noshow_tickets": len(noshow_tickets),
        "gross_revenue": gross_revenue,
        "staff_summary": staff_summary,
        "payment_breakdown": si_payments,
    }


def _ensure_walkin_customer():
    """Get or create a generic walk-in customer record."""
    name = frappe.db.get_value("Customer Profile", {"phone": "walk-in"}, "name")
    if name:
        return name
    return frappe.get_doc({
        "doctype": "Customer Profile",
        "customer_name": "Walk-in Customer",
        "phone": "walk-in",
    }).insert(ignore_permissions=True).name
