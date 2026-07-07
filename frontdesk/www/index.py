# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Public landing page for FrontDesk.

URL: /index  (also reachable as the site root when configured)
Renders business name, branding, about copy and a single CTA to /book.
"""

import frappe

from ._branding import get_branding


def get_context(context):
	b = get_branding()
	active_staff = frappe.db.count("Staff Member", filters={"active": 1})

	context.business = b
	context.active_staff_count = active_staff
	context.no_cache = 1
	context.title = b["brand_name"]
	return context
