# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class CustomerProfile(Document):
    """Thin customer record — Basira CRM is the CRM of record.

    The basira_crm_id + erpnext_customer link fields are populated by the
    Basira CRM sync (Phase 2/3). For Phase 0 we only require phone, since
    guest bookings flow through this DocType.
    """

    def validate(self):
        # Light normalization: phone is the primary identifier for guest flows.
        if self.phone:
            self.phone = self.phone.strip()
