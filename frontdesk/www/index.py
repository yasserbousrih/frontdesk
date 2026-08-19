"""Public landing page for FrontDesk.

URL: /index  (also reachable as the site root when configured)
Renders business name, branding, services, story, how-it-works,
gallery, testimonials, visit info and a single CTA to /book — every
section toggleable and every string overridable from Business Settings
(Homepage section), mirroring the Back House guest site pattern.
"""

import frappe

from ._branding import get_branding

no_cache = 1


def get_context(context):
    b = get_branding()

    # Active staff, for the hero "N barbers ready" line (label from settings).
    active_staff = frappe.db.count("Staff Member", filters={"active": 1})

    # Featured services: active first, capped at the configured count.
    services = []
    gallery = []
    try:
        rows = frappe.get_all(
            "Item",
            fields=["name", "item_name", "service_category", "duration_minutes", "standard_rate", "description", "image"],
            filters={"item_group": "Services", "disabled": 0, "show_on_homepage": 1},
            order_by="modified desc",
            limit_page_length=b["services_count"],
        )
        for r in rows:
            services.append({
                "name": r.item_name,
                "category": r.service_category or "",
                "duration_minutes": r.duration_minutes,
                "price": r.standard_rate,
                "description": r.description or "",
                "image": r.image or "",
            })
            if r.image:
                gallery.append(r.image)
    except Exception:
        frappe.log_error("Item fetch failed", "FrontDesk Home")

    context.business = b
    context.services = services
    context.gallery = gallery[:6]
    context.active_staff_count = active_staff
    context.no_cache = 1
    context.title = b["brand_name"]
    return context
