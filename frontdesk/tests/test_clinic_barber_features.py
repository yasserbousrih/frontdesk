# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, flt, today
from frontdesk.api.board import (
	add_walkin,
	get_board_data,
	get_customer_card,
	get_daily_summary,
	update_customer_technical_notes,
	update_status,
)
from frontdesk.api.bookings import (
	cancel_web_booking,
	create_web_booking,
	reschedule_web_booking,
)


class TestClinicBarberFeatures(FrappeTestCase):
	def setUp(self):
		# Ensure service items exist
		self.svc1 = "Haircut Clinic Test"
		self.svc2 = "Beard Clinic Test"

		if not frappe.db.exists("Item", self.svc1):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc1,
				"item_name": "Haircut Clinic Test",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 30,
				"standard_rate": 60.0,
			}).insert(ignore_permissions=True)

		if not frappe.db.exists("Item", self.svc2):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc2,
				"item_name": "Beard Clinic Test",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 15,
				"standard_rate": 40.0,
			}).insert(ignore_permissions=True)

		# Ensure staff member with commission exists
		staff = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])
		if staff:
			self.staff = staff[0].name
			frappe.db.set_value("Staff Member", self.staff, "commission_pct", 40.0)
		else:
			sm = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Dr. Barber",
				"active": 1,
				"commission_pct": 40.0,
				"working_hours": [
					{"weekday": "Monday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Tuesday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Wednesday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Thursday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Friday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Saturday", "start_time": "08:00:00", "end_time": "22:00:00"},
					{"weekday": "Sunday", "start_time": "08:00:00", "end_time": "22:00:00"},
				]
			}).insert(ignore_permissions=True)
			self.staff = sm.name

	def test_fast_walkin_and_immediate_seating(self):
		"""Verify fast walk-in seating with custom name, phone, and multiple services."""
		res = add_walkin(
			staff=self.staff,
			services=[self.svc1, self.svc2],
			customer_name="Walkin VIP",
			phone="+974 7788 9900",
			status="In Progress",
		)
		self.assertIn("name", res)
		self.assertEqual(res["status"], "In Progress")
		self.assertEqual(res["price"], 100.0)  # 60 + 40
		self.assertEqual(res["duration_minutes"], 45)  # 30 + 15

		b_doc = frappe.get_doc("Booking", res["name"])
		self.assertEqual(b_doc.status, "In Progress")
		self.assertEqual(len(b_doc.services), 2)

	def test_customer_technical_notes_and_card(self):
		"""Verify saving client formula / allergies and retrieving visit history."""
		# Create customer
		cp = frappe.get_doc({
			"doctype": "Customer Profile",
			"customer_name": "Formula Customer",
			"phone": "+974 5500 1122",
			"technical_notes": "#1.5 fade on sides, textured scissor top",
		}).insert(ignore_permissions=True)

		# Create completed visit
		b = frappe.get_doc({
			"doctype": "Booking",
			"customer": cp.name,
			"staff": self.staff,
			"service": self.svc1,
			"booking_date": today(),
			"start_time": "09:00:00",
			"status": "Completed",
			"price": 60.0,
		}).insert(ignore_permissions=True)

		# Update formula
		update_res = update_customer_technical_notes(cp.name, "#2 skin fade + beard oil")
		self.assertTrue(update_res.get("ok"))

		# Get customer card
		card = get_customer_card(cp.name)
		self.assertEqual(card["customer_name"], "Formula Customer")
		self.assertEqual(card["technical_notes"], "#2 skin fade + beard oil")
		self.assertGreaterEqual(card["total_visits"], 1)
		self.assertTrue(len(card["past_visits"]) >= 1)

	def test_daily_summary_and_commissions(self):
		"""Verify daily closing summary calculates completed tickets and commission % cut."""
		summary = get_daily_summary(today())
		self.assertIn("total_tickets", summary)
		self.assertIn("gross_revenue", summary)
		self.assertIn("staff_summary", summary)

		staff_entry = [s for s in summary["staff_summary"] if s["staff_id"] == self.staff]
		if staff_entry:
			s_data = staff_entry[0]
			expected_comm = (s_data["gross_revenue"] * s_data["commission_pct"]) / 100.0
			self.assertAlmostEqual(s_data["commission_amount"], expected_comm, places=2)

	def test_reschedule_and_cancel_self_service(self):
		"""Verify 1-click self-service rescheduling and cancellation using secure token."""
		future_date = str(add_days(today(), 8))
		res = create_web_booking(
			staff=self.staff,
			service=self.svc1,
			booking_date=future_date,
			start_time="10:00:00",
			phone="+974 6677 8899",
			customer_name="Self Service Client",
		)
		b_name = res["booking"]
		b_doc = frappe.get_doc("Booking", b_name)
		token = b_doc.reschedule_token
		self.assertTrue(bool(token))

		# Reschedule to 14:00:00 on future date
		new_date = str(add_days(today(), 14))
		resched_res = reschedule_web_booking(token=token, new_date=new_date, new_time="14:00:00")
		self.assertTrue(resched_res.get("ok"))
		self.assertEqual(resched_res["date"], new_date)
		self.assertEqual(resched_res["time"], "14:00")

		b_doc.reload()
		self.assertEqual(str(b_doc.booking_date), new_date)

		# Cancel booking
		cancel_res = cancel_web_booking(token=token, reason="Change of plans")
		self.assertTrue(cancel_res.get("ok"))

		b_doc.reload()
		self.assertEqual(b_doc.status, "Cancelled")
		self.assertIn("Cancelled by client", b_doc.notes or "")
