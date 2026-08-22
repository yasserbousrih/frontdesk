"""Shared brand-data helper for `www/` page context builders.

Reads the Frappe ``Website Settings`` single first, then falls back to
``Business Settings`` for fields that don't exist in the built-in doctype
(colours, about blurb, contact links, operational settings, homepage copy).

Every page that renders a booking-site template should call
``get_branding()`` once and feed the returned dict into its Jinja context.
"""

import frappe

from ._theme import FONT_URLS, resolve_theme

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

# Per-vertical default LOOK — each industry gets a completely different
# theme preset, Arabic font and layout out of the box (all still
# overridable from Business Settings appearance fields).
VERTICAL_LOOKS = {
    "Barbershop": {"preset": "Brass", "ar_font": "Tajawal", "layout": "Modern (Card & Booking)"},
    "Salon": {"preset": "Rose", "ar_font": "Amiri", "layout": "Modern (Card & Booking)"},
    "Clinic": {"preset": "Navy", "ar_font": "Noto Kufi Arabic", "layout": "Minimal (Editorial)"},
    "Spa": {"preset": "Forest", "ar_font": "Noto Sans Arabic", "layout": "Minimal (Editorial)"},
    "Nail Studio": {"preset": "Burgundy", "ar_font": "Cairo", "layout": "Vibrant (Bold)"},
    "Other": {"preset": "Slate", "ar_font": "Noto Naskh Arabic", "layout": "Modern (Card & Booking)"},
}

# Per-vertical booking-wizard FLOW — which steps each industry runs and in
# what order. 'staff' steps are skipped entirely for verticals that don't
# need a staff pick (Spa, Other).
VERTICAL_FLOWS = {
    "Barbershop": ["staff", "service", "time", "details"],  # barber first — regulars follow their barber
    "Salon": ["service", "staff", "time", "details"],  # service first, then stylist
    "Clinic": ["department", "service", "staff", "time", "details"],  # department first (dermatology etc), then service, then doctor
    "Spa": ["service", "time", "details"],  # no staff pick — treatment then time
    "Nail Studio": ["service", "staff", "time", "details"],  # service first, then artist
    "Other": ["service", "time", "details"],  # no staff pick — simplest
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
    # Resolve and set current request language safely
    cookies = {}
    try:
        if getattr(frappe, "request", None) and hasattr(frappe.request, "cookies"):
            cookies = frappe.request.cookies or {}
    except Exception:
        cookies = {}

    req_lang = (
        frappe.form_dict.get("lang")
        or cookies.get("preferred_language")
        or cookies.get("fd_lang")
        or getattr(frappe.local, "lang", "en")
        or "en"
    )
    if req_lang in ("ar", "fr", "en"):
        frappe.local.lang = req_lang

    ws = _safe_single("Website Settings") or {}
    bs = _safe_single("Business Settings") or {}

    # LIVE PREVIEW: when ?preview_settings=<urlencoded JSON> is present,
    # overlay those draft values on top so the page renders unsaved desk
    # edits (Back House Website Settings desk preview button pattern).
    pv = frappe.form_dict.get("preview_settings") or ""
    if pv:
        try:
            import json as _json
            overlay = _json.loads(pv)
            for k, v in (overlay or {}).items():
                if v is not None and v != "":
                    bs[k] = v
        except Exception:
            frappe.log_error("Bad preview_settings param", "get_branding")

    business_name = bs.get("business_name") or ws.get("app_name") or "FrontDesk"
    vertical = bs.get("vertical") or "Barbershop"
    vd = VERTICAL_DEFAULTS.get(vertical, VERTICAL_DEFAULTS["Other"])
    vl = VERTICAL_LOOKS.get(vertical, VERTICAL_LOOKS["Other"])
    vf = VERTICAL_FLOWS.get(vertical, VERTICAL_FLOWS["Other"])

    # Industry default look: each vertical has its own theme preset, Arabic
    # font and layout — Business Settings appearance fields override.
    if not bs.get("preset_theme"):
        bs["preset_theme"] = vl["preset"]
    ar_font = vl["ar_font"]
    if not bs.get("site_layout"):
        bs["site_layout"] = vl["layout"]

    theme = resolve_theme(bs)

    # Typography: Google Fonts for the body + heading (when a serif pair is
    # chosen), base size, radius + shadow tokens, layout name.
    font_family = bs.get("font_family") or "Inter"
    heading_font = bs.get("heading_font") or "Same as Body"
    font_urls = []
    if FONT_URLS.get(font_family):
        font_urls.append(FONT_URLS[font_family])
    if FONT_URLS.get(ar_font) and ar_font != font_family:
        font_urls.append(FONT_URLS[ar_font])
    if heading_font.startswith("Serif (Playfair") and font_family != "Playfair Display":
        font_urls.append("family=Playfair+Display:wght@600;700;800")
    elif heading_font.startswith("Serif (Cormorant") and font_family != "Cormorant Garamond":
        font_urls.append("family=Cormorant+Garamond:wght@500;600;700")
    font_display = (
        "'Playfair Display', Georgia, serif" if heading_font.startswith("Serif (Playfair")
        else "'Cormorant Garamond', Georgia, serif" if heading_font.startswith("Serif (Cormorant")
        else f"{font_family}, sans-serif"
    )
    font_size_base = bs.get("font_size_base") or "Normal (16px)"
    radius_map = {"Sharp (0px)": "0px", "Soft (8px)": "8px", "Rounded (16px)": "16px", "Pill (999px)": "999px"}
    shadow_map = {"None": "none", "Subtle": "0 2px 10px rgba(0,0,0,0.08)",
                  "Medium": "0 6px 20px rgba(0,0,0,0.12)", "Strong": "0 12px 32px rgba(0,0,0,0.2)"}
    layout_map = {"Minimal (Editorial)": "minimal", "Vibrant (Bold)": "vibrant"}
    site_layout = bs.get("site_layout") or "Modern (Card & Booking)"
    theme_mode = (bs.get("theme_mode") or "Light").strip().lower()

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
        "primary_color": theme["light"]["primary"],
        "accent_color": theme["light"]["accent"],
        "vertical": vertical,
        "flow": vf,
        # -- appearance (Back House structure: colors / typography / layout) -
        "theme": theme,
        "theme_mode": theme_mode,  # 'light' | 'dark' | 'auto'
        "font_family": font_family,
        "font_urls": font_urls,
        "font_display": font_display,
        "ar_font": ar_font,
        "font_size": "14px" if font_size_base.startswith("Small") else "18px" if font_size_base.startswith("Large") else "16px",
        "radius": radius_map.get(bs.get("border_radius")) or "16px",
        "shadow": shadow_map.get(bs.get("card_shadow")) or "0 2px 10px rgba(0,0,0,0.08)",
        "site_layout": layout_map.get(site_layout) or "modern",  # 'modern' | 'minimal' | 'vibrant'
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
        "enable_online_payments": bool(bs.get("enable_online_payments")) and (bs.get("payment_gateway") not in (None, "", "None", "Cash On Service")),
        "payment_mode": bs.get("payment_mode") or "Pay on Service",
        "payment_gateway": bs.get("payment_gateway") or "None",
        "require_deposit": bool(bs.get("require_deposit")),
        "deposit_type": bs.get("deposit_type") or "Percentage",
        "deposit_value": float(bs.get("deposit_value") or 20.0),
        # -- translations & localization --------------------------------------
        "lang": req_lang,
        "is_rtl": req_lang in ("ar", "he", "fa", "ur"),
        "ui_translations": _get_ui_translations(req_lang),
    }


def _get_ui_translations(lang: str = "ar") -> dict:
    """Fetch all translations for client hydration."""
    try:
        from frontdesk.api.translation import get_translations
        return get_translations(lang).get("translations", {})
    except Exception:
        return {}


def _safe_single(doctype: str) -> dict | None:
    """Return the single DocType as a dict, or ``None`` if not installed."""
    try:
        return frappe.get_single(doctype).as_dict()
    except Exception:
        return None
