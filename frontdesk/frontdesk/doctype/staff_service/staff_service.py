# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class StaffService(Document):
    """Child table row: a service (Item) a staff member can perform.

    Validation lives in the parent (Staff Member); this controller exists
    so the v16 migrate orphan-scan can import the doctype.
    """
    pass
