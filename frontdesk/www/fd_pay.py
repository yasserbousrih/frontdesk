# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt
from ._branding import get_branding


def get_context(context):
	pr_name = frappe.form_dict.get("pr") or frappe.form_dict.get("payment_request") or ""
	if not pr_name or not frappe.db.exists("Payment Request", pr_name):
		context.error = "Payment request not found or has expired."
		context.title = "Payment Not Found"
		context.business = get_branding()
		context.no_cache = 1
		return context

	pr = frappe.get_doc("Payment Request", pr_name)
	context.business = get_branding()
	context.payment_request = pr
	context.grand_total = flt(pr.grand_total)
	context.currency = pr.currency or context.business.get("currency") or "QAR"
	context.status = pr.status
	context.is_paid = pr.status == "Paid"

	# Resolve reference details (Booking or Sales Invoice)
	context.booking = None
	if pr.reference_doctype == "Booking" and frappe.db.exists("Booking", pr.reference_name):
		b = frappe.get_doc("Booking", pr.reference_name)
		context.booking = {
			"name": b.name,
			"service_name": frappe.db.get_value("Item", b.service, "item_name") if b.service else "",
			"staff_name": frappe.db.get_value("Staff Member", b.staff, "staff_name") if b.staff else "Any Staff",
			"booking_date": str(b.booking_date),
			"start_time": str(b.start_time)[:5] if b.start_time else "",
			"customer_name": frappe.db.get_value("Customer Profile", b.customer, "customer_name") if b.customer else "",
			"status": b.status,
		}

	# Check demo mode
	gateway_name = pr.payment_gateway or "FrontDesk Gateway"
	context.demo_mode = True
	if gateway_name == "FrontDesk Gateway":
		try:
			gw_settings = frappe.db.get_singles_dict("FrontDesk Gateway Settings")
			context.demo_mode = bool(gw_settings.get("demo_mode", 1))
		except Exception:
			context.demo_mode = True

	context.title = f"Pay for {context.booking['service_name'] if context.booking else 'Service'}"
	context.no_cache = 1
	return context
