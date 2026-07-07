# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Multi-step booking wizard page.

URL: /book
Loads Business Settings, active staff and active services so the
client-side wizard can render its steps without any extra round trips.
"""

import frappe

from ._branding import get_branding


def get_context(context):
	b = get_branding()

	staff_list = frappe.get_all(
		"Staff Member",
		filters={"active": 1},
		fields=["name", "staff_name", "photo", "bio"],
		order_by="staff_name asc",
	)

	services = frappe.get_all(
		"Service",
		filters={"active": 1},
		fields=["name", "service_name", "duration_minutes", "price", "description"],
		order_by="service_name asc",
	)

	context.business = b
	context.staff_list = staff_list
	context.services = services
	context.no_cache = 1
	context.title = "Book an Appointment"
	return context
