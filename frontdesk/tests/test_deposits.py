# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, today
from frontdesk.api.checkout import create_invoice
from frontdesk.api.payments import (
	confirm_demo_payment,
	create_payment_request,
	is_online_payment_enabled,
	on_payment_request_authorized,
)


class TestDeposits(FrappeTestCase):
	def setUp(self):
		self.svc = "Deposit Test Service"
		if not frappe.db.exists("Item", self.svc):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc,
				"item_name": "Deposit Test Service",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 45,
				"standard_rate": 200.0,
			}).insert(ignore_permissions=True)

		staff = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])
		if staff:
			self.staff = staff[0].name
		else:
			sm = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Test Deposit Staff",
				"active": 1,
			}).insert(ignore_permissions=True)
			self.staff = sm.name

		cust = frappe.get_all("Customer Profile", filters={"phone": "+97455554321"}, fields=["name"])
		if cust:
			self.customer = cust[0].name
		else:
			cd = frappe.get_doc({
				"doctype": "Customer Profile",
				"customer_name": "Deposit Client",
				"phone": "+97455554321",
				"email": "deposit@example.com",
			}).insert(ignore_permissions=True)
			self.customer = cd.name

		# Set Business Settings for deposit (25% deposit)
		bs = frappe.get_single("Business Settings")
		bs.enable_online_payments = 1
		bs.payment_gateway = "FrontDesk Gateway"
		bs.payment_mode = "Both"
		bs.require_deposit = 1
		bs.deposit_type = "Percentage"
		bs.deposit_value = 25.0
		bs.save(ignore_permissions=True)

	def test_deposit_calculation_percentage(self):
		booking = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": add_days(today(), 20),
			"start_time": "11:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		self.assertEqual(flt(booking.price), 200.0)
		self.assertEqual(flt(booking.deposit_amount), 50.0)  # 25% of 200
		self.assertEqual(booking.deposit_paid, 0)

	def test_deposit_payment_request_and_checkout(self):
		booking = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": add_days(today(), 21),
			"start_time": "11:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		# Create payment request for deposit
		pr_res = create_payment_request(booking=booking.name)
		self.assertIn("payment_url", pr_res)
		pr_name = pr_res["payment_request"]

		pr = frappe.get_doc("Payment Request", pr_name)
		self.assertEqual(flt(pr.grand_total), 50.0)  # Charged deposit amount, not full 200

		# Complete demo payment
		confirm_demo_payment(pr_name)

		booking.reload()
		self.assertEqual(booking.deposit_paid, 1)
		self.assertEqual(booking.status, "Booked")  # Still Booked, awaiting visit & completion

		# Now mark Completed at the chair and run checkout
		booking.status = "Completed"
		booking.save(ignore_permissions=True)

		inv_res = create_invoice(booking_name=booking.name, payment_method="Cash")
		si = frappe.get_doc("Sales Invoice", inv_res["sales_invoice"])
		self.assertEqual(flt(si.grand_total), 200.0)

		# Check payments split
		payments = {p.mode_of_payment: flt(p.amount) for p in si.payments}
		self.assertIn("Online", payments)
		self.assertEqual(payments["Online"], 50.0)  # Pre-paid deposit
		self.assertIn("Cash", payments)
		self.assertEqual(payments["Cash"], 150.0)   # Remaining at chair

		booking.reload()
		self.assertEqual(booking.status, "Paid")
