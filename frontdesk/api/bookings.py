# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Public booking creation endpoint, called by /book.

Guest-allowed so unauthenticated website visitors can create a booking.
Finds-or-creates the Customer Profile by phone, then writes a Booking
with status Booked and source Web. Supports multi-service cart bookings.
"""

import json
import frappe
from frappe.utils import cint, flt, getdate, today as today_date


@frappe.whitelist(allow_guest=True)
def create_web_booking(
    staff=None,
    service=None,
    booking_date=None,
    start_time=None,
    phone=None,
    customer_name=None,
    pay_online=None,
    email=None,
    services=None,
):
    """Create a booking from the public website (supports single or multi-service).

    Find-or-create Customer Profile by phone, then create a Booking with status Booked, source Web.
    If online payment is enabled/requested, creates a Payment Request and returns the payment_url.
    Returns dict with booking name + details.
    """
    # --- resolve services list ---
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
    elif service and str(service).strip():
        service_list = [str(service).strip()]

    if not service_list:
        frappe.throw("Missing required field: service or services")

    for s in service_list:
        if not frappe.db.exists("Item", s):
            frappe.throw(f"Invalid service: {s}")

    # --- input validation ---
    _missing = [f for f, v in {
        "booking_date": booking_date,
        "start_time": start_time,
        "phone": phone,
        "customer_name": customer_name,
    }.items() if not v]
    if _missing:
        frappe.throw(f"Missing required field(s): {', '.join(_missing)}")

    if staff and not frappe.db.exists("Staff Member", staff):
        frappe.throw(f"Invalid staff member: {staff}")

    try:
        _bd = getdate(booking_date)
    except Exception:
        frappe.throw(f"Invalid booking date: {booking_date}")
    if _bd < getdate(today_date()):
        frappe.throw("Cannot book a date in the past.")

    # --- calculate totals across all services ---
    total_duration = sum(int(frappe.db.get_value("Item", s, "duration_minutes") or 0) for s in service_list)
    if total_duration <= 0:
        total_duration = 15
    total_rate = sum(flt(frappe.db.get_value("Item", s, "standard_rate") or 0) for s in service_list)

    # Staff is optional: auto-assign the first free active staff member.
    if not staff:
        staff = _auto_assign_staff(total_duration, booking_date, start_time)

    # Find or create customer by phone
    existing = frappe.db.get_value("Customer Profile", {"phone": phone}, "name")
    if existing:
        customer = existing
        if email and not frappe.db.get_value("Customer Profile", existing, "email"):
            frappe.db.set_value("Customer Profile", existing, "email", email)
    else:
        customer = frappe.get_doc({
            "doctype": "Customer Profile",
            "customer_name": customer_name,
            "phone": phone,
            "email": email or "",
        }).insert(ignore_permissions=True).name

    primary_service = service_list[0]
    child_services = [
        {
            "service": s,
            "service_name": frappe.db.get_value("Item", s, "item_name") or s,
            "duration_minutes": int(frappe.db.get_value("Item", s, "duration_minutes") or 0),
            "price": flt(frappe.db.get_value("Item", s, "standard_rate") or 0),
        }
        for s in service_list
    ]

    booking = frappe.get_doc({
        "doctype": "Booking",
        "customer": customer,
        "staff": staff,
        "service": primary_service,
        "booking_date": booking_date,
        "start_time": start_time,
        "status": "Booked",
        "source": "Web",
        "duration_minutes": total_duration,
        "price": total_rate,
        "services": child_services,
    })
    booking.insert(ignore_permissions=True)

    # Check online payment
    payment_url = ""
    payment_request_id = ""
    requires_payment = False

    try:
        bs = frappe.get_single("Business Settings")
        from frontdesk.api.payments import is_online_payment_enabled
        if is_online_payment_enabled(bs) and total_rate > 0:
            pm = bs.get("payment_mode") or "Pay on Service"
            should_pay_online = (pm in ("Online Now", "Pay Now (online)")) or (pm == "Both" and cint(pay_online))
            if should_pay_online:
                from frontdesk.api.payments import create_payment_request
                pr_res = create_payment_request(
                    booking=booking.name,
                    grand_total=total_rate,
                    guest_email=email,
                    guest_phone=phone,
                )
                payment_url = pr_res.get("payment_url") or ""
                payment_request_id = pr_res.get("payment_request") or ""
                requires_payment = bool(payment_url)
    except Exception:
        frappe.log_error(frappe.get_traceback(), "FrontDesk Create Web Booking Payment")

    service_names_joined = " + ".join(
        frappe.db.get_value("Item", s, "item_name") or s for s in service_list
    )

    return {
        "booking": booking.name,
        "service": service_names_joined,
        "services": child_services,
        "staff": frappe.db.get_value("Staff Member", staff, "staff_name"),
        "date": str(booking.booking_date),
        "time": str(booking.start_time)[:5],
        "duration_minutes": total_duration,
        "price": total_rate,
        "payment_url": payment_url,
        "payment_request": payment_request_id,
        "requires_payment": requires_payment,
    }


def _auto_assign_staff(duration_or_service, booking_date, start_time):
    """Auto-assign the first active staff member free for the requested slot.

    Returns the Staff Member name of the first active member (ordered by
    staff_name) whose working hours on the booking weekday cover the slot and
    who has no overlapping non-cancelled booking that day. Throws if nobody
    is available.
    """
    from frontdesk.frontdesk.doctype.booking.overlap import (
        CANCELLED_STATES,
        add_minutes_to_time,
        normalize_time,
        times_overlap,
        to_minutes,
    )

    if isinstance(duration_or_service, int):
        duration_min = duration_or_service
    else:
        service_doc = frappe.get_doc("Item", duration_or_service)
        duration_min = int(service_doc.duration_minutes or 0)

    weekday = getdate(booking_date).strftime("%A")

    start = normalize_time(start_time)
    end = add_minutes_to_time(start, duration_min)
    start_min, end_min = to_minutes(start), to_minutes(end)

    for row in frappe.get_all(
        "Staff Member",
        filters={"active": 1},
        fields=["name"],
        order_by="staff_name asc",
    ):
        staff = row.name
        staff_doc = frappe.get_doc("Staff Member", staff)
        window_ok = any(
            hr.weekday == weekday
            and start_min >= to_minutes(hr.start_time)
            and end_min <= to_minutes(hr.end_time)
            for hr in staff_doc.working_hours
        )
        if not window_ok:
            continue

        existing = frappe.get_all(
            "Booking",
            filters={
                "staff": staff,
                "booking_date": getdate(booking_date),
                "status": ["not in", list(CANCELLED_STATES)],
            },
            fields=["start_time", "end_time", "duration_minutes"],
        )
        for b in existing:
            b_end = b.end_time or add_minutes_to_time(b.start_time, b.duration_minutes or 0)
            if times_overlap(start, end, b.start_time, b_end):
                break
        else:
            return staff

    frappe.throw("No staff member is available at that time. Please pick a different slot.")


@frappe.whitelist()
def get_booking_events(start, end, filters=None):
    """Calendar event source for Booking."""
    if isinstance(filters, str):
        filters = json.loads(filters)
    filters = filters or {}

    booking_filters = [
        ["booking_date", ">=", getdate(start)],
        ["booking_date", "<=", getdate(end)],
    ]
    for k, v in filters.items():
        if v:
            booking_filters.append([k, "=", v])

    bookings = frappe.get_all(
        "Booking",
        filters=booking_filters,
        fields=["name", "customer", "staff", "service", "booking_date", "start_time", "end_time", "status"],
    )

    events = []
    for b in bookings:
        c_name = frappe.db.get_value("Customer Profile", b.customer, "customer_name") or b.customer
        s_name = frappe.db.get_value("Staff Member", b.staff, "staff_name") or b.staff
        i_name = frappe.db.get_value("Item", b.service, "item_name") or b.service
        title = f"{c_name} ({s_name} - {i_name})"

        st_str = str(b.start_time)[:5] if b.start_time else "09:00"
        et_str = str(b.end_time)[:5] if b.end_time else "10:00"
        events.append({
            "name": b.name,
            "title": title,
            "start": f"{b.booking_date} {st_str}:00",
            "end": f"{b.booking_date} {et_str}:00",
            "status": b.status,
            "allDay": 0,
        })
    return events


@frappe.whitelist(allow_guest=True)
def reschedule_web_booking(token, new_date, new_time, staff=None):
    """Reschedule an existing booking using its secure token."""
    if not token or not token.strip():
        frappe.throw("Invalid reschedule token.")

    b_name = frappe.db.get_value("Booking", {"reschedule_token": token.strip()}, "name")
    if not b_name:
        frappe.throw("Booking not found or invalid link.")

    booking = frappe.get_doc("Booking", b_name)
    if booking.status in ("Completed", "Paid", "Cancelled", "No-Show"):
        frappe.throw(f"Cannot reschedule an appointment in status '{booking.status}'.")

    try:
        nd = getdate(new_date)
    except Exception:
        frappe.throw("Invalid date format.")
    if nd < getdate(today_date()):
        frappe.throw("Cannot reschedule to a date in the past.")

    target_staff = staff or booking.staff
    if not frappe.db.exists("Staff Member", target_staff):
        frappe.throw(f"Staff member not found: {target_staff}")

    booking.booking_date = new_date
    booking.start_time = new_time
    booking.end_time = None
    booking.staff = target_staff
    booking.save(ignore_permissions=True)

    return {
        "ok": True,
        "booking": booking.name,
        "date": str(booking.booking_date),
        "time": str(booking.start_time)[:5],
        "staff": frappe.db.get_value("Staff Member", booking.staff, "staff_name"),
    }


@frappe.whitelist(allow_guest=True)
def cancel_web_booking(token, reason=None):
    """Cancel an appointment using its secure token."""
    if not token or not token.strip():
        frappe.throw("Invalid token.")

    b_name = frappe.db.get_value("Booking", {"reschedule_token": token.strip()}, "name")
    if not b_name:
        frappe.throw("Booking not found or invalid link.")

    booking = frappe.get_doc("Booking", b_name)
    if booking.status in ("Completed", "Paid", "Cancelled"):
        frappe.throw(f"Appointment is already {booking.status}.")

    booking.status = "Cancelled"
    if reason:
        booking.notes = (booking.notes or "") + f"\nCancelled by client: {reason.strip()}"
    booking.save(ignore_permissions=True)

    return {
        "ok": True,
        "booking": booking.name,
        "status": "Cancelled",
    }
