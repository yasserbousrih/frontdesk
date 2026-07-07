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
		"service": frappe.db.get_value("Service", service, "service_name"),
		"staff": frappe.db.get_value("Staff Member", staff, "staff_name"),
		"date": str(booking.booking_date),
		"time": str(booking.start_time)[:5],
	}