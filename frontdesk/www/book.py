# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Multi-step booking wizard page.

URL: /book
Loads Business Settings, active staff and active services so the
client-side wizard can render its steps without any extra round trips.
"""

import frappe


def get_context(context):
	business = _load_business_settings()

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

	context.business = business
	context.staff_list = staff_list
	context.services = services
	context.no_cache = 1
	context.title = "Book an Appointment"
	return context


def _load_business_settings() -> dict:
	"""Same shape as the landing-page loader — kept local so the two
	pages can evolve independently."""
	defaults = {
		"business_name": "FrontDesk",
		"vertical": "Barbershop",
		"logo": "",
		"cover_image": "",
		"primary_color": "#1a1a2e",
		"accent_color": "#e94560",
		"about_text": "",
		"contact_phone": "",
		"contact_whatsapp": "",
		"contact_email": "",
		"instagram": "",
		"slot_buffer_minutes": 0,
		"cancellation_window_hours": 0,
		"currency": "USD",
	}
	if not frappe.db.exists("DocType", "Business Settings"):
		return defaults
	try:
		doc = frappe.get_single("Business Settings")
	except frappe.DoesNotExistError:
		return defaults

	out = dict(defaults)
	for key in defaults:
		if hasattr(doc, key):
			out[key] = getattr(doc, key)
	return out