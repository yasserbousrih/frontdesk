# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frappe.utils import add_days, today
from frontdesk.api.board import add_walkin, get_stations


class TestStations(FrappeTestCase):
	def setUp(self):
		self.svc = "Station Test Service"
		if not frappe.db.exists("Item", self.svc):
			frappe.get_doc({
				"doctype": "Item",
				"item_code": self.svc,
				"item_name": "Station Test Service",
				"item_group": "Services",
				"is_stock_item": 0,
				"duration_minutes": 30,
				"standard_rate": 150.0,
			}).insert(ignore_permissions=True)

		# Create two staff members with working hours
		staff_a_list = frappe.get_all("Staff Member", filters={"staff_name": "Station Staff A"}, fields=["name"])
		if staff_a_list:
			self.staff_a = staff_a_list[0].name
		else:
			sm_a = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Station Staff A",
				"active": 1,
				"working_hours": [
					{"weekday": day, "start_time": "08:00:00", "end_time": "22:00:00"}
					for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
				],
			}).insert(ignore_permissions=True)
			self.staff_a = sm_a.name

		staff_b_list = frappe.get_all("Staff Member", filters={"staff_name": "Station Staff B"}, fields=["name"])
		if staff_b_list:
			self.staff_b = staff_b_list[0].name
		else:
			sm_b = frappe.get_doc({
				"doctype": "Staff Member",
				"staff_name": "Station Staff B",
				"active": 1,
				"working_hours": [
					{"weekday": day, "start_time": "08:00:00", "end_time": "22:00:00"}
					for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
				],
			}).insert(ignore_permissions=True)
			self.staff_b = sm_b.name

		# Create Service Station
		if not frappe.db.exists("Service Station", "Laser Suite 1"):
			self.station = frappe.get_doc({
				"doctype": "Service Station",
				"station_name": "Laser Suite 1",
				"station_type": "Treatment Room",
				"active": 1,
			}).insert(ignore_permissions=True).name
		else:
			self.station = "Laser Suite 1"

		# Create Customer
		cust = frappe.get_all("Customer Profile", filters={"phone": "+97455557777"}, fields=["name"])
		if cust:
			self.customer = cust[0].name
		else:
			cd = frappe.get_doc({
				"doctype": "Customer Profile",
				"customer_name": "Station Client",
				"phone": "+97455557777",
			}).insert(ignore_permissions=True)
			self.customer = cd.name

	def test_get_stations_api(self):
		stations = get_stations()
		self.assertTrue(len(stations) > 0)
		suite_names = [s.station_name for s in stations]
		self.assertIn("Laser Suite 1", suite_names)

	def test_station_overlap_rejection(self):
		test_date = add_days(today(), 25)

		# Staff A books Laser Suite 1 from 15:00 to 15:30
		b1 = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff_a,
			"station": self.station,
			"service": self.svc,
			"booking_date": test_date,
			"start_time": "15:00:00",
			"status": "Booked",
			"source": "Web",
		}).insert(ignore_permissions=True)
		self.assertEqual(b1.station, self.station)

		# Staff B tries to book the same Laser Suite 1 at 15:15 (overlap)
		b2 = frappe.get_doc({
			"doctype": "Booking",
			"customer": self.customer,
			"staff": self.staff_b,
			"station": self.station,
			"service": self.svc,
			"booking_date": test_date,
			"start_time": "15:15:00",
			"status": "Booked",
			"source": "Web",
		})
		with self.assertRaises(frappe.ValidationError) as ctx:
			b2.insert(ignore_permissions=True)
		self.assertIn("already reserved", str(ctx.exception))

	def test_add_walkin_with_station(self):
		walkin = add_walkin(
			staff=self.staff_a,
			service=self.svc,
			customer_name="Walkin Station Guest",
			phone="+97455558888",
			status="In Progress",
			start_time="08:00:00",
			station=self.station,
		)
		self.assertTrue(walkin["name"])
		b_doc = frappe.get_doc("Booking", walkin["name"])
		self.assertEqual(b_doc.station, self.station)
