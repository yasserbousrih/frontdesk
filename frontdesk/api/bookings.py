# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Public booking creation endpoint, called by /book.

Guest-allowed so unauthenticated website visitors can create a booking.
Finds-or-creates the Customer Profile by phone, then writes a Booking
with status Booked and source Web.
"""

import frappe


@frappe.whitelist(allow_guest=True)
def create_web_booking(staff, service, booking_date, start_time, phone, customer_name):
	"""Create a booking from the public website.
	Find-or-create Customer Profile by phone, then create a Booking with status Booked, source Web.
	Returns dict with booking name + details."""
	# --- input validation ---
	_missing = [f for f, v in {
		"service": service, "booking_date": booking_date,
		"start_time": start_time, "phone": phone, "customer_name": customer_name,
	}.items() if not v]
	if _missing:
		frappe.throw(f"Missing required field(s): {', '.join(_missing)}")

	if staff and not frappe.db.exists("Staff Member", staff):
		frappe.throw(f"Invalid staff member: {staff}")
	if not frappe.db.exists("Item", service):
		frappe.throw(f"Invalid service: {service}")

	from frappe.utils import getdate, today as today_date
	try:
		_bd = getdate(booking_date)
	except Exception:
		frappe.throw(f"Invalid booking date: {booking_date}")
	if _bd < getdate(today_date()):
		frappe.throw("Cannot book a date in the past.")

	# --- end validation ---

	# Staff is optional: auto-assign the first free active staff member.
	if not staff:
		staff = _auto_assign_staff(service, booking_date, start_time)

	# Find or create customer by phone
	existing = frappe.db.get_value("Customer Profile", {"phone": phone}, "name")
	if existing:
		customer = existing
	else:
		customer = frappe.get_doc({
			"doctype": "Customer Profile",
			"customer_name": customer_name,
			"phone": phone,
		}).insert(ignore_permissions=True).name

	booking = frappe.get_doc({
		"doctype": "Booking",
		"customer": customer,
		"staff": staff,
		"service": service,
		"booking_date": booking_date,
		"start_time": start_time,
		"status": "Booked",
		"source": "Web",
	})
	booking.insert(ignore_permissions=True)

	return {
		"booking": booking.name,
		"service": frappe.db.get_value("Item", service, "item_name"),
		"staff": frappe.db.get_value("Staff Member", staff, "staff_name"),
		"date": str(booking.booking_date),
		"time": str(booking.start_time)[:5],
	}


def _auto_assign_staff(service, booking_date, start_time):
	"""Auto-assign the first active staff member free for the requested slot.

	Returns the Staff Member name of the first active member (ordered by
	staff_name) whose working hours on the booking weekday cover the slot and
	who has no overlapping non-cancelled booking that day. Throws if nobody
	is available.
	"""
	from frappe.utils import getdate

	from frontdesk.frontdesk.doctype.booking.overlap import (
		CANCELLED_STATES,
		add_minutes_to_time,
		normalize_time,
		times_overlap,
		to_minutes,
	)

	service_doc = frappe.get_doc("Item", service)
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