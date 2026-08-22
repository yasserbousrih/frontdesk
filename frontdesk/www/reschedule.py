# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from ._branding import get_branding


def get_context(context):
	b = get_branding()
	context.business = b
	context.business_name = b["brand_name"]
	context.primary_color = b["primary_color"]
	context.accent_color = b["accent_color"]
	context.currency = b["currency"]
	context.footer_powered = b["footer_powered"]
	context.copyright_text = b["copyright_text"]

	token = frappe.form_dict.get("token")
	context.token = token or ""
	context.booking = None
	context.error = None

	if not token:
		context.error = "No booking token provided. Please check your confirmation link."
		return

	b_name = frappe.db.get_value("Booking", {"reschedule_token": token.strip()}, "name")
	if not b_name:
		context.error = "Booking not found or link has expired."
		return

	doc = frappe.get_doc("Booking", b_name)
	customer_name = frappe.db.get_value("Customer Profile", doc.customer, "customer_name") or doc.customer
	staff_name = frappe.db.get_value("Staff Member", doc.staff, "staff_name") or doc.staff

	child_services = frappe.get_all(
		"Booking Service",
		filters={"parent": doc.name},
		fields=["service", "service_name", "duration_minutes", "price"],
	)
	if child_services:
		service_name = " + ".join(cs["service_name"] for cs in child_services)
	else:
		service_name = frappe.db.get_value("Item", doc.service, "item_name") or doc.service

	context.booking = {
		"name": doc.name,
		"customer_name": customer_name,
		"staff": doc.staff,
		"staff_name": staff_name,
		"service": doc.service,
		"service_name": service_name,
		"services_list": child_services,
		"booking_date": str(doc.booking_date),
		"start_time": str(doc.start_time)[:5],
		"end_time": str(doc.end_time)[:5] if doc.end_time else "",
		"duration_minutes": doc.duration_minutes,
		"price": doc.price,
		"status": doc.status,
	}

	context.staff_list = [
		{"name": s.name, "staff_name": s.staff_name, "photo": s.photo}
		for s in frappe.get_all("Staff Member", filters={"active": 1}, fields=["name", "staff_name", "photo"])
	]
