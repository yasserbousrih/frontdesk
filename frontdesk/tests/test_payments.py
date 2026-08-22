# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today
from frontdesk.api.bookings import create_web_booking
from frontdesk.api.payments import (
	confirm_demo_payment,
	get_payment_modes,
	is_online_payment_enabled,
	sync_gateway_from_settings,
	verify_payment,
)


class TestFrontDeskPayments(FrappeTestCase):
	def setUp(self):
		# Reset Business Settings for predictable testing
		bs = frappe.get_single("Business Settings")
		bs.enable_online_payments = 1
		bs.payment_gateway = "FrontDesk Gateway"
		bs.payment_mode = "Both"
		bs.save(ignore_permissions=True)
		sync_gateway_from_settings(bs)

	def test_payment_disabled_setting(self):
		bs = frappe.get_single("Business Settings")
		bs.enable_online_payments = 0
		bs.save(ignore_permissions=True)

		self.assertFalse(is_online_payment_enabled(bs))

		modes = get_payment_modes()
		online_in_modes = any(m.get("method") == "Online" for m in modes.get("modes", []))
		self.assertFalse(online_in_modes)

		# Create booking when disabled
		services = frappe.get_all("Item", filters={"item_group": "Services"}, fields=["name"])
		staff_members = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])
		if not services or not staff_members:
			return

		booking_date = str(add_days(today(), 3))
		res = create_web_booking(
			staff=staff_members[0].name,
			service=services[0].name,
			booking_date=booking_date,
			start_time="11:00:00",
			phone="+974 6611 2233",
			customer_name="Cash Customer",
			pay_online=1,  # Attempting to pay online when setting is disabled
		)
		self.assertFalse(res.get("requires_payment"))
		self.assertEqual(res.get("payment_url"), "")

	def test_payment_chain_and_booking_flow(self):
		bs = frappe.get_single("Business Settings")
		bs.enable_online_payments = 1
		bs.payment_gateway = "FrontDesk Gateway"
		bs.payment_mode = "Both"
		bs.save(ignore_permissions=True)
		sync_gateway_from_settings(bs)

		self.assertTrue(is_online_payment_enabled(bs))
		self.assertTrue(frappe.db.exists("Payment Gateway", "FrontDesk Gateway"))
		self.assertTrue(frappe.db.exists("DocType", "FrontDesk Gateway Settings"))

		# Fetch service and staff
		services = frappe.get_all("Item", filters={"item_group": "Services"}, fields=["name", "standard_rate"])
		staff_members = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])

		if not services or not staff_members:
			return

		svc = services[0]
		stf = staff_members[0]

		# Create booking with online payment enabled
		booking_date = str(add_days(today(), 4))
		res = create_web_booking(
			staff=stf.name,
			service=svc.name,
			booking_date=booking_date,
			start_time="15:00:00",
			phone="+974 7741 5561",
			customer_name="Test Payment Customer",
			email="test_pay@example.com",
			pay_online=1,
		)

		self.assertIn("booking", res)
		self.assertTrue(res.get("requires_payment"))
		self.assertTrue(res.get("payment_url").startswith("/fd_pay?pr="))

		pr_name = res["payment_request"]
		status_before = verify_payment(pr_name)
		self.assertEqual(status_before["status"], "pending")
		self.assertFalse(status_before["paid"])

		# Pay
		pay_res = confirm_demo_payment(payment_request=pr_name)
		self.assertTrue(pay_res["ok"])
		self.assertIn(pay_res["status"], ("paid", "already_paid"))

		# Verify paid state
		status_after = verify_payment(pr_name)
		self.assertTrue(status_after["paid"])

		booking_doc = frappe.get_doc("Booking", res["booking"])
		self.assertEqual(booking_doc.status, "Paid")
