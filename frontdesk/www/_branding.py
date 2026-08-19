"""Shared brand-data helper for `www/` page context builders.

Reads the Frappe ``Website Settings`` single first, then falls back to
``Business Settings`` for fields that don't exist in the built-in doctype
(colours, about blurb, contact links, operational settings, homepage copy).

Every page that renders a booking-site template should call
``get_branding()`` once and feed the returned dict into its Jinja context.
"""

import frappe

# Per-vertical defaults for the homepage copy (mirrors the Back House
# pattern: every string on the page is overridable from Business Settings,
# and these only fill the gap until the owner customises them).
VERTICAL_DEFAULTS = {
    "Barbershop": {"tagline": "Fresh cuts, sharp fades", "cta": "Book Appointment", "staff_label": "barber"},
    "Salon": {"tagline": "Look good, feel even better", "cta": "Book a Session", "staff_label": "stylist"},
    "Clinic": {"tagline": "Care you can trust", "cta": "Book a Consultation", "staff_label": "practitioner"},
    "Spa": {"tagline": "Recharge. Restore. Glow.", "cta": "Book a Treatment", "staff_label": "therapist"},
    "Nail Studio": {"tagline": "Nails that turn heads", "cta": "Book a Manicure", "staff_label": "nail artist"},
    "Other": {"tagline": "Book your appointment", "cta": "Book Appointment", "staff_label": "professional"},
}

HOW_DEFAULTS = [
    ("Pick Your Service", "Browse our services and pick the one that suits you."),
    ("Choose a Time", "See real-time availability and lock in your slot in seconds."),
    ("Get Reminded", "We confirm instantly and remind you before your visit."),
]


def get_branding() -> dict:
    """Return a flat dict of branding values safe for template injection.

    Source priority: Website Settings (Frappe built-in) → Business
    Settings (FrontDesk custom) → hard-coded defaults.
    """
    ws = _safe_single("Website Settings") or {}
    bs = _safe_single("Business Settings") or {}

    business_name = bs.get("business_name") or ws.get("app_name") or "FrontDesk"
    vertical = bs.get("vertical") or "Barbershop"
    vd = VERTICAL_DEFAULTS.get(vertical, VERTICAL_DEFAULTS["Other"])

    # Section toggles: Check fields default to ON on a fresh site (the
    # Back House pattern — `setting_bool(bs, name, default)`).
    def on(fieldname, default=True):
        v = bs.get(fieldname)
        return default if v is None else bool(v)

    how = [{"title": bs.get(f"how_step{i}_title") or t, "text": bs.get(f"how_step{i}_text") or x}
           for i, (t, x) in [(1, HOW_DEFAULTS[0]), (2, HOW_DEFAULTS[1]), (3, HOW_DEFAULTS[2])]]

    testimonials = []
    for i in (1, 2, 3):
        text = bs.get(f"testimonial_{i}_text")
        if text:
            testimonials.append({"text": text, "author": bs.get(f"testimonial_{i}_author") or "Happy client"})

    return {
        # -- from Website Settings (built-in) ---------------------------------
        "brand_name": business_name,
        "brand_logo": ws.get("app_logo") or bs.get("logo") or "",
        "brand_cover": ws.get("banner_image") or bs.get("cover_image") or "",
        "brand_favicon": ws.get("favicon") or "",
        "footer_powered": ws.get("footer_powered") or "Basira",
        "copyright_text": ws.get("copyright") or f"© {business_name}",
        "head_html": ws.get("head_html") or "",
        # -- from Business Settings (no Website Settings equivalent) ----------
        "primary_color": bs.get("primary_color") or "#1a1a2e",
        "accent_color": bs.get("accent_color") or "#e94560",
        "vertical": vertical,
        # -- homepage copy (all overridable, defaults per vertical) -----------
        "hero_tagline": bs.get("hero_tagline") or vd["tagline"],
        "cta_label": bs.get("cta_label") or vd["cta"],
        "cta_secondary_label": bs.get("cta_secondary_label") or "",
        "cta_secondary_link": bs.get("cta_secondary_link") or "",
        "staff_label": bs.get("staff_label") or vd["staff_label"],
        "staff_label_plural": (bs.get("staff_label") or vd["staff_label"]) + "s",
        "story_heading": bs.get("story_heading") or "Our Story",
        "story_text": bs.get("story_text") or bs.get("about_text") or "",
        "story_image": bs.get("story_image") or "",
        "services_heading": bs.get("services_heading") or "Our Services",
        "services_count": int(bs.get("services_count") or 4),
        "show_prices": on("show_prices"),
        "how_heading": bs.get("how_heading") or "How It Works",
        "how_steps": how,
        "testimonials": testimonials,
        "hours_text": bs.get("hours_text") or "",
        "address": bs.get("address") or "",
        "maps_url": bs.get("maps_url") or "",
        "cta_band_heading": bs.get("cta_band_heading") or "Book Your Appointment",
        "cta_band_text": bs.get("cta_band_text") or "Reserve your spot in seconds — pick a time that works for you.",
        "cta_band_label": bs.get("cta_band_label") or vd["cta"],
        # -- section toggles ----------------------------------------------------
        "show_hero": on("show_hero"),
        "show_story": on("show_story"),
        "show_services": on("show_services"),
        "show_how_it_works": on("show_how_it_works"),
        "show_gallery": on("show_gallery"),
        "show_testimonials": on("show_testimonials"),
        "show_visit": on("show_visit"),
        "show_cta_band": on("show_cta_band"),
        # -- contact (existing) ------------------------------------------------
        "contact_phone": bs.get("contact_phone") or "",
        "contact_whatsapp": bs.get("contact_whatsapp") or "",
        "contact_email": bs.get("contact_email") or "",
        "instagram": bs.get("instagram") or "",
        # -- operational (still from Business Settings) -----------------------
        "slot_buffer_minutes": bs.get("slot_buffer_minutes", 0),
        "currency": bs.get("currency") or "QAR",
    }


def _safe_single(doctype: str) -> dict | None:
    """Return the single DocType as a dict, or ``None`` if not installed."""
    try:
        return frappe.get_single(doctype).as_dict()
    except Exception:
        return None
