# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class StaffMember(Document):
    """A staff member who delivers services — barber, stylist, therapist, etc.

    Working hours are stored in the child table `Staff Working Hour`:
    one row per weekday the staff works. Services they can perform are
    stored in `Staff Service`. Bookings are validated against this data
    by `frontdesk.api.availability.get_available_slots`.
    """

    def validate(self):
        if not self.working_hours:
            frappe.throw("At least one working hour row is required.")

        # Ensure no duplicate weekdays.
        weekdays = [row.weekday for row in self.working_hours]
        if len(weekdays) != len(set(weekdays)):
            frappe.throw("Working hours: each weekday can only appear once.")

        # Ensure each row's start < end.
        for row in self.working_hours:
            if row.start_time and row.end_time and row.start_time >= row.end_time:
                frappe.throw(
                    f"Working hours: start time must be before end time ({row.weekday})."
                )
