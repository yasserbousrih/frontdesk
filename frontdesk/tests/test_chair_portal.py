# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today
from frontdesk.api.board import update_customer_technical_notes, update_status
from frontdesk.www.my_schedule import get_context


class TestChairPortal(FrappeTestCase):
	def setUp(self):
		self.svc = "Chair Test Service"
		if not frappe.db.exists("Item", self.svc):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc,
				"item_name": "Chair Test Service",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 30,
				"standard_rate": 100.0,
			}).insert(ignore_permissions=True)

		staff_list = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])
		if staff_list:
			self.staff = staff_list[0].name
		else:
			sm = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Chair Barber Pro",
				"active": 1,
				"working_hours": [
					{"weekday": day, "start_time": "08:00:00", "end_time": "22:00:00"}
					for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
				],
			}).insert(ignore_permissions=True)
			self.staff = sm.name

		cust_list = frappe.get_all("Customer Profile", filters={"phone": "+97455559999"}, fields=["name"])
		if cust_list:
			self.customer = cust_list[0].name
		else:
			cd = frappe.get_doc({
				"doctype": "Customer Profile",
				"customer_name": "VIP Chair Client",
				"phone": "+97455559999",
				"technical_notes": "Low taper fade, beard oil",
			}).insert(ignore_permissions=True)
			self.customer = cd.name

	def test_chair_context_and_booking_load(self):
		b = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": today(),
			"start_time": "17:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		ctx = frappe._dict({"staff": self.staff})
		frappe.form_dict.staff = self.staff
		res = get_context(ctx)

		self.assertEqual(res.current_staff_id, self.staff)
		self.assertTrue(len(res.today_bookings) > 0)
		matched = [item for item in res.today_bookings if item.name == b.name]
		self.assertTrue(len(matched) > 0)
		self.assertEqual(matched[0].customer_name, "VIP Chair Client")
		self.assertIn("Low taper fade", matched[0].technical_notes)

	def test_chair_in_progress_and_complete_actions(self):
		b = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": today(),
			"start_time": "18:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		# 1-Tap Seat / In Progress
		update_status(b.name, "In Progress")
		b.reload()
		self.assertEqual(b.status, "In Progress")

		# Update tech formula notes from chair
		update_customer_technical_notes(self.customer, "Low skin taper, beard trim + line up")
		cp = frappe.get_doc("Customer Profile", self.customer)
		self.assertEqual(cp.technical_notes, "Low skin taper, beard trim + line up")

		# 1-Tap Done & send to front desk checkout
		update_status(b.name, "Completed")
		b.reload()
		self.assertEqual(b.status, "Completed")
