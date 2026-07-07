"""Shared brand-data helper for `www/` page context builders.

Reads the Frappe ``Website Settings`` single first, then falls back to
``Business Settings`` for fields that don't exist in the built-in doctype
(colours, about blurb, contact links, operational settings).

Every page that renders a booking-site template should call
``get_branding()`` once and feed the returned dict into its Jinja context.
"""

import frappe


def get_branding() -> dict:
    """Return a flat dict of branding values safe for template injection.

    Source priority: Website Settings (Frappe built-in) → Business
    Settings (FrontDesk custom) → hard-coded defaults.
    """
    ws = _safe_single("Website Settings") or {}
    bs = _safe_single("Business Settings") or {}

    business_name = (
        ws.get("app_name")
        or bs.get("business_name")
        or "FrontDesk"
    )

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
        "about_text": bs.get("about_text") or "",
        "vertical": bs.get("vertical") or "Barbershop",
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
