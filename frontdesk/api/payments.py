import frappe
from frappe.utils import cint, flt, nowdate


def _get_settings():
	try:
		return frappe._dict(frappe.db.get_singles_dict("Business Settings"))
	except Exception:
		return frappe._dict({})


GATEWAY_SETTINGS = {
	"Stripe": "Stripe Settings",
	"Razorpay": "Razorpay Settings",
	"PayPal": "PayPal Settings",
	"Paymob": "Paymob Settings",
	"FrontDesk Gateway": "FrontDesk Gateway Settings",
}


def is_online_payment_enabled(settings=None):
	"""Check if online payment is enabled for the business.

	Follows the Back House architecture:
	- Business Settings enable_online_payments toggle must be enabled (or not explicitly 0)
	- Website Payment Gateway must be selected and not 'None' or 'Cash On Service'
	- Payment Mode must be 'Online Now' or 'Both'
	"""
	s = settings or _get_settings()
	if s.get("enable_online_payments") is not None and not cint(s.get("enable_online_payments")):
		return False

	gateway = (s.get("payment_gateway") or "None").strip()
	if gateway in ("", "None", "Cash On Service"):
		return False

	pm = (s.get("payment_mode") or "Pay on Service").strip()
	if pm not in ("Online Now", "Both", "Pay Now (online)"):
		return False

	return True


def _gateway_ready(gw_account):
	"""Check if the gateway account has active configuration."""
	try:
		gateway = frappe.db.get_value("Payment Gateway Account", gw_account, "payment_gateway")
		if gateway == "FrontDesk Gateway":
			return True
		settings_doctype = GATEWAY_SETTINGS.get(gateway) or f"{gateway} Settings"
		if not frappe.db.exists("DocType", settings_doctype):
			return False
		vals = frappe.db.get_singles_dict(settings_doctype)
		return bool(vals.get("secret_key") or vals.get("api_key"))
	except Exception:
		return False


@frappe.whitelist(allow_guest=True)
def get_payment_modes(settings=None):
	"""Payment methods visible to the client on website / booking wizard.

	Follows the Back House architecture: reads Business Settings → Payment Methods table
	or standard defaults, filtering out Online / Card if not enabled or gateway not ready.
	"""
	bs = settings or _get_settings()
	label_map = {"Cash": "Cash", "Card": "Credit Card", "Online": "Online", "Pay Later": "Pay Later"}
	modes = []

	if frappe.db.exists("DocType", "FrontDesk Payment Method"):
		selected = frappe.get_all(
			"FrontDesk Payment Method",
			filters={"parent": "Business Settings", "parentfield": "booking_payment_methods"},
			fields=["method", "label"],
			order_by="idx",
		)
		for row in selected:
			m_key = (row.method or "").strip()
			if not m_key:
				continue
			display = (row.label or "").strip() or label_map.get(m_key, m_key)
			modes.append({"method": label_map.get(m_key, m_key), "label": display, "default": m_key == "Cash"})

	online_ok = is_online_payment_enabled(bs)

	if not modes:
		# Standard fallback
		modes = [
			{"method": "Cash", "label": "Pay at Front Desk", "default": True},
			{"method": "Credit Card", "label": "Card at Counter", "default": False},
		]
		if online_ok:
			modes.append({"method": "Online", "label": "Pay Online Now", "default": False})

	modes = [m for m in modes if not (m["method"] == "Online" and not online_ok)]

	return {
		"ok": True,
		"modes": modes,
		"enable_online_payments": online_ok,
		"payment_mode": bs.get("payment_mode") or "Pay on Service",
		"payment_gateway": bs.get("payment_gateway") or "None",
	}


@frappe.whitelist(allow_guest=True)
def create_payment_request(booking=None, invoice=None, grand_total=None, guest_email=None, guest_phone=None):
	"""Create a standard Frappe Payment Request for a Booking or Sales Invoice."""
	settings = _get_settings()
	if not is_online_payment_enabled(settings):
		frappe.throw("Online payment is not enabled.")

	ref_doctype = "Booking" if booking else "Sales Invoice"
	ref_name = booking or invoice
	if not ref_name or not frappe.db.exists(ref_doctype, ref_name):
		frappe.throw(f"Invalid {ref_doctype}: {ref_name}")

	doc = frappe.get_doc(ref_doctype, ref_name)
	customer_name = ""
	customer_profile = None
	phone = guest_phone or ""
	email = guest_email or ""

	if ref_doctype == "Booking":
		if flt(doc.deposit_amount) > 0 and flt(doc.deposit_amount) < flt(doc.price or 0):
			price = flt(doc.deposit_amount)
		else:
			price = flt(grand_total) if grand_total is not None else flt(doc.price or 0)
		if price <= 0:
			# If price was 0 on booking, fetch from service
			if doc.service:
				price = flt(frappe.db.get_value("Item", doc.service, "standard_rate") or 0)
		if price <= 0:
			frappe.throw("Booking has no payable amount.")
		customer_profile = doc.customer
		if customer_profile and frappe.db.exists("Customer Profile", customer_profile):
			cp = frappe.get_doc("Customer Profile", customer_profile)
			customer_name = cp.customer_name
			phone = phone or cp.phone
			email = email or cp.email
		else:
			customer_name = "Walk-in Guest"
	else:
		price = flt(grand_total) if grand_total is not None else flt(doc.grand_total or doc.rounded_total or 0)
		customer_name = doc.customer or "Walk-in Customer"

	gateway = (settings.get("payment_gateway") or "FrontDesk Gateway").strip()
	if gateway in ("", "None", "Cash On Service"):
		gateway = "FrontDesk Gateway"

	company = settings.get("company") or frappe.db.get_value("Company", {}, "name") or "My Business Co"
	gw_account = frappe.db.get_value(
		"Payment Gateway Account",
		{"payment_gateway": gateway, "company": company},
		"name",
	)
	if not gw_account:
		# Auto-create if missing
		sync_gateway_from_settings(settings)
		gw_account = frappe.db.get_value(
			"Payment Gateway Account",
			{"payment_gateway": gateway, "company": company},
			"name",
		)

	custom_gateway = gateway == "FrontDesk Gateway"

	# Check for existing pending payment request for this reference
	existing_pr = frappe.db.get_value(
		"Payment Request",
		{"reference_doctype": ref_doctype, "reference_name": ref_name, "docstatus": ["in", [0, 1]]},
		["name", "status", "payment_url"],
		as_dict=True,
	)
	if existing_pr:
		if existing_pr.status == "Paid":
			return {"already_paid": True, "payment_request": existing_pr.name, "payment_url": ""}
		pr_doc = frappe.get_doc("Payment Request", existing_pr.name)
		pay_url = pr_doc.get_payment_url() if hasattr(pr_doc, "get_payment_url") else f"/fd_pay?pr={pr_doc.name}"
		return {"payment_url": pay_url, "payment_request": pr_doc.name}

	pr = frappe.get_doc({
		"doctype": "Payment Request",
		**({"payment_gateway_account": gw_account} if gw_account else {}),
		"payment_gateway": gateway,
		"reference_doctype": ref_doctype,
		"reference_name": ref_name,
		"party_type": "Customer Profile" if ref_doctype == "Booking" else "Customer",
		"party": customer_profile if ref_doctype == "Booking" else (doc.customer or "Walk-in Customer"),
		"grand_total": price,
		"email_to": email,
		"phone_number": phone,
		"payment_request_type": "Inward",
		"transaction_date": nowdate(),
	})
	pr.flags.ignore_permissions = True

	if gw_account and not custom_gateway:
		pr.insert()
		pr.submit()
	else:
		pr.flags.ignore_validate = True
		pr.flags.ignore_mandatory = True
		pr.insert()

	pay_url = f"/fd_pay?pr={pr.name}"
	try:
		if hasattr(pr, "get_payment_url"):
			generated = pr.get_payment_url()
			if generated:
				pay_url = generated
	except Exception:
		pass

	return {"payment_url": pay_url, "payment_request": pr.name}


@frappe.whitelist(allow_guest=True)
def verify_payment(payment_request):
	"""Check if a Payment Request has been marked Paid."""
	pr = frappe.db.get_value(
		"Payment Request", payment_request, ["name", "status", "reference_doctype", "reference_name", "grand_total"], as_dict=True
	)
	if not pr:
		return {"status": "not_found"}
	return {
		"status": "success" if pr.status == "Paid" else "pending",
		"paid": pr.status == "Paid",
		"payment_request": pr.name,
		"reference_doctype": pr.reference_doctype,
		"reference_name": pr.reference_name,
		"grand_total": pr.grand_total,
	}


def _mark_pr_paid(pr):
	"""Mark Payment Request as paid and update the underlying Booking/Invoice."""
	if pr.status == "Paid":
		return pr.status
	prev_status = pr.status
	try:
		pr.set_as_paid()
	except Exception:
		pr.db_set({"status": "Paid", "outstanding_amount": 0})

	if prev_status != "Paid":
		on_payment_request_authorized(pr, "Completed")
	return pr.status


@frappe.whitelist(allow_guest=True)
def confirm_demo_payment(payment_request=None):
	"""Demo mode payment handler for hosted /fd_pay checkout."""
	pr_name = (payment_request or frappe.form_dict.get("payment_request") or "").strip()
	if not pr_name or not frappe.db.exists("Payment Request", pr_name):
		frappe.local.response["http_status_code"] = 400
		return {"ok": False, "error": "Unknown payment request"}

	pr = frappe.get_doc("Payment Request", pr_name)
	was_paid = pr.status == "Paid"
	_mark_pr_paid(pr)

	return {
		"ok": True,
		"status": "already_paid" if was_paid else "paid",
		"payment_request": pr.name,
		"reference_doctype": pr.reference_doctype,
		"reference_name": pr.reference_name,
	}


def on_payment_request_authorized(doc, status=None):
	"""Fired when a Payment Request is successfully paid."""
	ref_doctype = doc.reference_doctype
	ref_name = doc.reference_name
	if not ref_doctype or not ref_name:
		return

	if ref_doctype == "Booking" and frappe.db.exists("Booking", ref_name):
		try:
			booking = frappe.get_doc("Booking", ref_name)
			booking.deposit_paid = 1
			if flt(booking.deposit_amount) > 0 and flt(booking.deposit_amount) < flt(booking.price or 0):
				if booking.status not in ("Seated", "In Progress", "Completed", "Paid"):
					booking.status = "Booked"
			else:
				booking.status = "Paid"
			booking.flags.ignore_permissions = True
			booking.save()

			# Trigger confirmation notification if configured
			try:
				from frontdesk.api.notifications import send_booking_confirmation
				send_booking_confirmation(booking, "after_insert")
			except Exception:
				pass
		except Exception:
			frappe.log_error(frappe.get_traceback(), "FrontDesk On Payment Authorized")


def on_payment_request_submit(doc, method=None):
	"""Fired on Payment Request submission."""
	pass


def sync_gateway_from_settings(settings=None):
	"""Build or sync the ERPNext payment chain when Business Settings is saved."""
	s = settings or _get_settings()
	gateway = (s.get("payment_gateway") or "None").strip()
	if gateway in ("", "None", "Cash On Service"):
		return {"ok": True, "gateway": gateway, "status": "disabled"}

	api_key = (s.get("payment_api_key") or "").strip()
	secret_key = (s.get("payment_secret") or "").strip()
	company = s.get("company") or frappe.db.get_value("Company", {}, "name") or "My Business Co"
	currency = s.get("currency") or frappe.db.get_value("Company", company, "default_currency") or "QAR"
	payment_account = frappe.db.get_value("Company", company, "default_cash_account") or f"Cash - {company[:2].upper()}"

	settings_doctype = GATEWAY_SETTINGS.get(gateway) or f"{gateway} Settings"

	# 1. Update gateway settings doc if credentials provided
	if frappe.db.exists("DocType", settings_doctype):
		try:
			has_settings = bool(frappe.db.get_singles_dict(settings_doctype))
			if not has_settings:
				frappe.get_doc({
					"doctype": settings_doctype,
					"gateway_name": gateway,
					**({"secret_key": secret_key or api_key} if "secret_key" in [f.fieldname for f in frappe.get_meta(settings_doctype).fields] else {}),
					**({"api_key": api_key} if "api_key" in [f.fieldname for f in frappe.get_meta(settings_doctype).fields] else {}),
				}).insert(ignore_permissions=True)
			else:
				ss = frappe.get_doc(settings_doctype, settings_doctype)
				if hasattr(ss, "secret_key") and (secret_key or api_key):
					ss.secret_key = secret_key or api_key
				if hasattr(ss, "api_key") and api_key:
					ss.api_key = api_key
				if hasattr(ss, "demo_mode") and gateway == "FrontDesk Gateway":
					ss.demo_mode = 1 if not secret_key else 0
				ss.flags.ignore_permissions = True
				ss.save()
		except Exception:
			frappe.log_error(frappe.get_traceback(), f"FrontDesk Gateway Settings Sync: {settings_doctype}")

	# 2. Ensure Payment Gateway record exists
	gw_controller = settings_doctype if frappe.db.exists("DocType", settings_doctype) else None
	if not frappe.db.exists("Payment Gateway", gateway):
		frappe.get_doc({
			"doctype": "Payment Gateway",
			"gateway": gateway,
			"gateway_settings": settings_doctype if gw_controller else None,
			"gateway_controller": gw_controller,
		}).insert(ignore_permissions=True)

	# 3. Ensure Payment Gateway Account exists
	acct_name = f"{gateway} - {currency} - {company}"
	if not frappe.db.exists("Payment Gateway Account", {"payment_gateway": gateway, "company": company}):
		pga = frappe.get_doc({
			"doctype": "Payment Gateway Account",
			"payment_gateway": gateway,
			"payment_account": payment_account,
			"company": company,
			"currency": currency,
			"is_default": 1,
		}).insert(ignore_permissions=True)

	# 4. Ensure Mode of Payment "Online" exists and has account mapped
	if not frappe.db.exists("Mode of Payment", "Online"):
		frappe.get_doc({
			"doctype": "Mode of Payment",
			"mode_of_payment": "Online",
			"type": "Phone",
			"enabled": 1,
		}).insert(ignore_permissions=True)

	if frappe.db.exists("Mode of Payment", "Online"):
		mo = frappe.get_doc("Mode of Payment", "Online")
		if not frappe.db.exists("Mode of Payment Account", {"parent": "Online", "company": company}):
			mo.append("accounts", {"company": company, "default_account": payment_account})
			mo.flags.ignore_permissions = True
			mo.save()

	return {"ok": True, "gateway": gateway, "company": company}


def on_business_settings_update(doc, method=None):
	"""Sync payment gateway chain whenever Business Settings is updated in Desk."""
	try:
		sync_gateway_from_settings(doc)
	except Exception:
		frappe.log_error(frappe.get_traceback(), "FrontDesk Business Settings Payment Sync")
