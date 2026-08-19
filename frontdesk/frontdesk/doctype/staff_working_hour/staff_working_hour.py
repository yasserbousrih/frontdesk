# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class StaffWorkingHour(Document):
    """Child table row: a staff member's working hours for one weekday.

    Validation lives in the parent (Staff Member); this controller exists
    so the v16 migrate orphan-scan can import the doctype.
    """
    pass
