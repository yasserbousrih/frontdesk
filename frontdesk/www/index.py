# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Public landing page for FrontDesk.

URL: /index  (also reachable as the site root when configured)
Renders business name, branding, about copy and a single CTA to /book.
"""

import frappe


def get_context(context):
	business = _load_business_settings()
	active_staff = frappe.db.count("Staff Member", filters={"active": 1})

	context.business = business
	context.active_staff_count = active_staff
	context.no_cache = 1
	context.title = business.get("business_name") or "FrontDesk"
	return context


def _load_business_settings() -> dict:
	"""Return Business Settings as a plain dict, with safe defaults
	if the singleton doesn't exist yet (fresh install)."""
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