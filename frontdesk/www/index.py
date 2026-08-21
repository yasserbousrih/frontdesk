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
            fields=["name", "item_name", "item_name_ar", "service_category", "duration_minutes", "standard_rate", "description", "image"],
            filters={"item_group": "Services", "disabled": 0, "show_on_homepage": 1},
            order_by="modified desc",
            limit_page_length=b["services_count"],
        )
        for r in rows:
            services.append({
                "name": r.item_name,
                "name_ar": r.item_name_ar or "",
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

    # ── Homepage Sections (ordered rows from child table) ─────────────────────
    # Falls back to a sensible default order when no rows exist yet, so a fresh
    # install still renders correctly before the client has configured anything.
    sections = []
    try:
        rows = frappe.get_all(
            "Homepage Section",
            filters={"parent": "Business Settings", "parenttype": "Business Settings"},
            fields=["section_type", "enabled", "heading", "subheading",
                    "body_text", "image", "image_position",
                    "button_label", "button_link", "idx"],
            order_by="idx asc",
        )
        sections = [r for r in rows]
    except Exception:
        frappe.log_error("Homepage Section fetch failed", "FrontDesk Home")

    # Fallback: if no sections rows exist, build defaults from the old flat toggles
    if not sections:
        _defaults = [
            ("hero",          b.get("show_hero", 1)),
            ("story",         b.get("show_story", 1)),
            ("services",      b.get("show_services", 1)),
            ("how_it_works",  b.get("show_how_it_works", 1)),
            ("gallery",       b.get("show_gallery", 1)),
            ("testimonials",  b.get("show_testimonials", 1)),
            ("visit",         b.get("show_visit", 1)),
            ("cta_band",      b.get("show_cta_band", 1)),
        ]
        sections = [
            frappe._dict(section_type=t, enabled=bool(e),
                         heading=None, subheading=None, body_text=None,
                         image=None, image_position="right",
                         button_label=None, button_link=None)
            for t, e in _defaults
        ]

    context.business = b
    context.services = services
    context.gallery = gallery[:6]
    context.sections = sections
    context.active_staff_count = active_staff
    context.no_cache = 1
    context.title = b["brand_name"]
    return context
