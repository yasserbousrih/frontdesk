# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

from frappe.model.document import Document


class BusinessSettings(Document):
    """Single DocType holding the per-tenant site config.

    Branding fields drive the public booking website (Phase 1).
    booking_rules (slot buffer, cancellation window) drive the availability
    engine and the cancellation flow.
    """
    pass
