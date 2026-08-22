# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

from unittest.mock import patch

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today
from frontdesk.api.followups import on_booking_update
from frontdesk.api.notifications import send_booking_confirmation
from frontdesk.api.reminders import _send_reminder


class TestRetention(FrappeTestCase):
	def setUp(self):
		self.svc = "Retention Haircut Test"
		if not frappe.db.exists("Item", self.svc):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc,
				"item_name": "Retention Haircut Test",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 30,
				"standard_rate": 70.0,
			}).insert(ignore_permissions=True)

		staff = frappe.get_all("Staff Member", filters={"active": 1}, fields=["name"])
		if staff:
			self.staff = staff[0].name
		else:
			sm = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Test Retention Staff",
				"active": 1,
			}).insert(ignore_permissions=True)
			self.staff = sm.name

		# Create customer with phone
		cust = frappe.get_all("Customer Profile", filters={"phone": "+97455551234"}, fields=["name"])
		if cust:
			self.customer = cust[0].name
		else:
			cd = frappe.get_doc({
				"doctype": "Customer Profile",
				"customer_name": "Retention VIP",
				"phone": "+97455551234",
				"email": "retention@example.com",
			}).insert(ignore_permissions=True)
			self.customer = cd.name

		# Configure Business Settings for Omnichat
		bs = frappe.get_single("Business Settings")
		bs.business_name = "Retention Salon"
		bs.omnichat_api_url = "https://omnichat.example.com"
		bs.omnichat_api_token = "test_token_123"
		bs.omnichat_sender_id = "test_sender"
		bs.google_review_url = "https://g.page/r/test"
		bs.save(ignore_permissions=True)

	@patch("requests.post")
	def test_booking_confirmation_with_reschedule_link(self, mock_post):
		mock_post.return_value.status_code = 200

		booking = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": add_days(today(), 15),
			"start_time": "09:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		self.assertTrue(booking.reschedule_token)
		send_booking_confirmation(booking, "after_insert")

		self.assertTrue(mock_post.called)
		payload = mock_post.call_args[1]["json"]
		self.assertEqual(payload["to"], "+97455551234")
		self.assertIn("Retention Haircut Test", payload["message"])
		self.assertIn(f"/reschedule?token={booking.reschedule_token}", payload["message"])

	@patch("requests.post")
	def test_2h_reminder_with_reschedule_link(self, mock_post):
		mock_post.return_value.status_code = 200

		booking = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": add_days(today(), 16),
			"start_time": "09:30:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		bs = frappe.get_single("Business Settings")
		result = _send_reminder(booking.as_dict(), bs)
		self.assertTrue(result)
		self.assertTrue(mock_post.called)

		payload = mock_post.call_args[1]["json"]
		self.assertEqual(payload["to"], "+97455551234")
		self.assertIn("⏰ Reminder", payload["message"])
		self.assertIn(f"/reschedule?token={booking.reschedule_token}", payload["message"])

	@patch("requests.post")
	def test_post_paid_followup_and_rebooking(self, mock_post):
		mock_post.return_value.status_code = 200

		booking = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff,
			"service": self.svc,
			"booking_date": add_days(today(), 17),
			"start_time": "10:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)

		booking.status = "Paid"
		booking.save(ignore_permissions=True)
		on_booking_update(booking, "on_update")

		self.assertTrue(mock_post.called)
		payload = mock_post.call_args[1]["json"]
		self.assertEqual(payload["to"], "+97455551234")
		self.assertIn("Thanks for visiting", payload["message"])
		self.assertIn("/book", payload["message"])
		self.assertIn("https://g.page/r/test", payload["message"])
