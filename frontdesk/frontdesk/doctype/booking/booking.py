# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

from frontdesk.frontdesk.doctype.booking import overlap


CANCELLED_STATES = {"Cancelled", "No-Show"}


class Booking(Document):
    """A reservation of a specific staff member for a specific service at a specific time.

    The controller:
      * snapshots the service duration + price onto the booking so historical
        records survive changes to the Service / Staff Member rows.
      * validates that the staff member is active and works on the booking day.
      * rejects overlaps with other non-cancelled bookings for the same staff
        member (the same guarantee `get_available_slots` honors).
    """

    def validate(self):
        self._snapshot_service_fields()
        self._compute_end_time()
        self._enforce_timing()
        self._enforce_staff_active()
        self._enforce_no_overlap()

    def _compute_end_time(self):
        """Derive end_time from start_time + service duration if not set.

        Must run BEFORE the overlap check so that bookings created without an
        explicit end_time (e.g. web bookings) are still validated for conflicts.
        """
        if self.start_time and not self.end_time and (self.duration_minutes or 0) > 0:
            self.end_time = overlap.add_minutes_to_time(self.start_time, self.duration_minutes)

    # ----- internals -----

    def _enforce_timing(self):
        if not (self.start_time and self.end_time):
            return
        if self.start_time >= self.end_time:
            frappe.throw("Start time must be before end time.")

    def _enforce_staff_active(self):
        if not self.staff:
            return
        staff_doc = frappe.get_doc("Staff Member", self.staff)
        if not staff_doc.active:
            frappe.throw(f"Staff member '{staff_doc.staff_name}' is not active.")

    def _enforce_no_overlap(self):
        """Reject if any non-cancelled booking for the same staff overlaps this one."""
        if not (self.staff and self.booking_date and self.start_time and self.end_time):
            return

        existing = frappe.get_all(
            "Booking",
            filters={
                "staff": self.staff,
                "booking_date": self.booking_date,
                "status": ["not in", list(CANCELLED_STATES)],
                "name": ["!=", self.name or ""],
            },
            fields=["name", "start_time", "end_time", "status"],
        )

        for b in existing:
            if overlap.times_overlap(
                self.start_time, self.end_time, b.start_time, b.end_time
            ):
                frappe.throw(
                    f"Staff is already booked for {b.name} "
                    f"({b.start_time}–{b.end_time}, {b.status}). "
                    f"Pick a different time or staff member."
                )

    def _snapshot_service_fields(self):
        """Copy duration + price from Service if not already set on the booking."""
        if not self.service:
            return
        svc = frappe.get_doc("Service", self.service)
        if not self.duration_minutes:
            self.duration_minutes = svc.duration_minutes
        if self.price is None:
            self.price = svc.price
