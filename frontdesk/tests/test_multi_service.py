# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import json
import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, today
from frontdesk.api.availability import get_available_slots
from frontdesk.api.bookings import create_web_booking
from frontdesk.api.checkout import create_invoice


class TestMultiService(FrappeTestCase):
	def setUp(self):
		# Ensure at least 2 service items exist
		self.svc1_name = "Haircut Test"
		self.svc2_name = "Beard Trim Test"

		if not frappe.db.exists("Item", self.svc1_name):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc1_name,
				"item_name": "Haircut Test",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 30,
				"standard_rate": 50.0,
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Item", self.svc2_name):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc2_name,
				"item_name": "Beard Trim Test",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 15,
				"standard_rate": 30.0,
			}).insert(ignore_permissions=True)

		# Ensure dedicated test staff member exists with full hours
		staff_name = "Multi Test Staff"
		existing_staff = frappe.db.get_value("Staff Member", {"staff_name": staff_name}, "name")
		if existing_staff:
			self.staff = existing_staff
		else:
			sm = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": staff_name,
				"active": 1,
				"working_hours": [
					{"weekday": "Monday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Tuesday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Wednesday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Thursday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Friday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Saturday", "start_time": "09:00:00", "end_time": "21:00:00"},
					{"weekday": "Sunday", "start_time": "09:00:00", "end_time": "21:00:00"},
				]
			}).insert(ignore_permissions=True)
			self.staff = sm.name

	def test_availability_multi_service_duration(self):
		"""Verify that get_available_slots computes slots based on combined duration."""
		target_date = str(add_days(today(), 5))
		
		# 1 service (30 min)
		slots_1 = get_available_slots(
			staff=self.staff,
			services=[self.svc1_name],
			date=target_date,
		)
		self.assertTrue(len(slots_1) > 0)

		# 2 services (30 min + 15 min = 45 min)
		slots_2 = get_available_slots(
			staff=self.staff,
			services=[self.svc1_name, self.svc2_name],
			date=target_date,
		)
		self.assertTrue(len(slots_2) > 0)

		# Slots for 45 min should fit properly in working hours
		self.assertIn("start", slots_2[0])

	def test_create_web_booking_multi_service(self):
		"""Verify creating a booking with multiple services creates child table rows and correct totals."""
		target_date = str(add_days(today(), 6))
		services_list = [self.svc1_name, self.svc2_name]

		res = create_web_booking(
			staff=self.staff,
			services=json.dumps(services_list),
			booking_date=target_date,
			start_time="10:00:00",
			phone="+974 5599 8877",
			customer_name="Cart Customer",
		)

		self.assertIn("booking", res)
		b_name = res["booking"]
		self.assertEqual(res["price"], 80.0)  # 50 + 30
		self.assertEqual(res["duration_minutes"], 45)  # 30 + 15

		doc = frappe.get_doc("Booking", b_name)
		self.assertEqual(len(doc.services), 2)
		self.assertEqual(doc.services[0].service, self.svc1_name)
		self.assertEqual(flt(doc.services[0].price), 50.0)
		self.assertEqual(doc.services[1].service, self.svc2_name)
		self.assertEqual(flt(doc.services[1].price), 30.0)
		self.assertEqual(flt(doc.price), 80.0)
		self.assertEqual(doc.duration_minutes, 45)

	def test_checkout_multi_service_invoicing(self):
		"""Verify that checking out a multi-service booking creates multiple Sales Invoice Item lines."""
		target_date = str(add_days(today(), 7))
		services_list = [self.svc1_name, self.svc2_name]

		res = create_web_booking(
			staff=self.staff,
			services=services_list,
			booking_date=target_date,
			start_time="14:00:00",
			phone="+974 3322 1100",
			customer_name="Checkout Cart Client",
		)
		b_name = res["booking"]
		
		# Set status to Completed to allow checkout
		doc = frappe.get_doc("Booking", b_name)
		doc.status = "Completed"
		doc.save(ignore_permissions=True)

		inv_res = create_invoice(booking_name=b_name, payment_method="Cash")
		self.assertIn("sales_invoice", inv_res)
		si_name = inv_res["sales_invoice"]

		si = frappe.get_doc("Sales Invoice", si_name)
		self.assertEqual(si.docstatus, 1)  # Submitted
		self.assertEqual(flt(si.grand_total), 80.0)
		self.assertEqual(len(si.items), 2)
		
		item_codes = [it.item_code for it in si.items]
		self.assertIn(self.svc1_name, item_codes)
		self.assertIn(self.svc2_name, item_codes)
