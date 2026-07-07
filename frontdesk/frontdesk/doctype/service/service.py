# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class Service(Document):
    """A bookable service (e.g. 'Haircut — 30 min — 40 QAR').

    The price is captured on the Booking at booking time so historical
    bookings survive price changes on this record.
    """

    def validate(self):
        if self.duration_minutes is not None and self.duration_minutes <= 0:
            frappe.throw("Duration must be greater than zero minutes.")
