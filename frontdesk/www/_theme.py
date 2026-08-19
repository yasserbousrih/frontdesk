"""Theme resolution for the guest site — Back House pattern.

``preset_theme`` picks a full light+dark palette; ``Custom`` uses the
individual color fields for light mode and derives a dark palette that
keeps the brand colors. Every palette exposes CSS-variable-friendly keys
(primary, secondary, accent, bg, text, card, border, muted).
"""

# Google Fonts families → query parameter for the css2 endpoint.
FONT_URLS = {
    "Inter": "family=Inter:wght@400;500;600;700;800",
    "Poppins": "family=Poppins:wght@400;500;600;700;800",
    "Plus Jakarta Sans": "family=Plus+Jakarta+Sans:wght@400;500;600;700;800",
    "DM Sans": "family=DM+Sans:opsz,wght@9..40,400;9..40,500;9..40,600;9..40,700;9..40,800",
    "Nunito Sans": "family=Nunito+Sans:opsz,wght@6..12,400;6..12,600;6..12,700;6..12,800",
    "Montserrat": "family=Montserrat:wght@400;500;600;700;800",
    "Lora": "family=Lora:wght@400;500;600;700",
    "Merriweather": "family=Merriweather:wght@400;700",
    "Playfair Display": "family=Playfair+Display:wght@500;600;700;800",
    "Cormorant Garamond": "family=Cormorant+Garamond:wght@500;600;700",
    "Tajawal": "family=Tajawal:wght@400;500;700;800",
    "Cairo": "family=Cairo:wght@400;600;700;800",
    "Noto Sans Arabic": "family=Noto+Sans+Arabic:wght@400;500;600;700;800",
    "Noto Kufi Arabic": "family=Noto+Kufi+Arabic:wght@400;500;600;700;800",
    "Noto Naskh Arabic": "family=Noto+Naskh+Arabic:wght@400;500;600;700",
    "Amiri": "family=Amiri:wght@400;700",
}

THEME_PRESETS = {
    "Brass": {
        "light": {"primary": "#b98a44", "secondary": "#28251d", "accent": "#9a7b3c", "bg": "#faf9f6", "text": "#28251d", "card": "#ffffff", "border": "#e2e0d8", "muted": "#6b6b66"},
        "dark": {"primary": "#c9a55e", "secondary": "#0f0d0a", "accent": "#9a7b3c", "bg": "#171410", "text": "#f2ece1", "card": "#211d18", "border": "#322b21", "muted": "#a09887"},
    },
    "Teal": {
        "light": {"primary": "#0e7c86", "secondary": "#18323a", "accent": "#0e5f66", "bg": "#f6faf9", "text": "#18323a", "card": "#ffffff", "border": "#d8e4e2", "muted": "#5d7370"},
        "dark": {"primary": "#5fb3bd", "secondary": "#0a1416", "accent": "#4a94a0", "bg": "#0e1a1d", "text": "#e8f2f0", "card": "#152428", "border": "#24403c", "muted": "#8fa8a3"},
    },
    "Terracotta": {
        "light": {"primary": "#c2571b", "secondary": "#33241c", "accent": "#8f3d16", "bg": "#fbf7f4", "text": "#33241c", "card": "#ffffff", "border": "#e8dbd2", "muted": "#8a756a"},
        "dark": {"primary": "#e0854f", "secondary": "#120c08", "accent": "#b96a3d", "bg": "#1d1510", "text": "#f7ece4", "card": "#281c15", "border": "#3d2d22", "muted": "#a69080"},
    },
    "Forest": {
        "light": {"primary": "#2f6b3f", "secondary": "#1d2e22", "accent": "#245232", "bg": "#f6faf5", "text": "#1d2e22", "card": "#ffffff", "border": "#d8e4d6", "muted": "#5f7363"},
        "dark": {"primary": "#7fbf8d", "secondary": "#0b100c", "accent": "#5da06e", "bg": "#101711", "text": "#e8f2e9", "card": "#18221a", "border": "#2b3d2e", "muted": "#8fa394"},
    },
    "Navy": {
        "light": {"primary": "#2b4c7e", "secondary": "#1c2b3f", "accent": "#1f3a63", "bg": "#f7f9fc", "text": "#1c2b3f", "card": "#ffffff", "border": "#dce4ee", "muted": "#5f6e85"},
        "dark": {"primary": "#7fa3d8", "secondary": "#0a0f18", "accent": "#5d83b8", "bg": "#0f1622", "text": "#e9eff8", "card": "#17202f", "border": "#2a3a52", "muted": "#93a3ba"},
    },
    "Burgundy": {
        "light": {"primary": "#8e2f43", "secondary": "#331d22", "accent": "#6e2435", "bg": "#fbf7f8", "text": "#331d22", "card": "#ffffff", "border": "#e8d9dc", "muted": "#8a7076"},
        "dark": {"primary": "#d47a8c", "secondary": "#120a0c", "accent": "#b05a6e", "bg": "#1c1114", "text": "#f7e9ec", "card": "#28181c", "border": "#3e2a30", "muted": "#a98f95"},
    },
    "Midnight": {
        "light": {"primary": "#2c4a7c", "secondary": "#1b2434", "accent": "#b08d4f", "bg": "#f7f8fb", "text": "#1b2434", "card": "#ffffff", "border": "#dde3ec", "muted": "#66748c"},
        "dark": {"primary": "#8fa8d4", "secondary": "#0a0e16", "accent": "#c9a55e", "bg": "#0a0e16", "text": "#e8eef8", "card": "#131a28", "border": "#243048", "muted": "#8b98b0"},
    },
    "Desert": {
        "light": {"primary": "#b06a3b", "secondary": "#3a2f26", "accent": "#8a4f2c", "bg": "#faf6ef", "text": "#3a2f26", "card": "#ffffff", "border": "#e8ddce", "muted": "#8a7a68"},
        "dark": {"primary": "#d99a68", "secondary": "#1a1510", "accent": "#b06a3b", "bg": "#1a1510", "text": "#f5ece1", "card": "#261e16", "border": "#3a2e20", "muted": "#a4937f"},
    },
    "Ocean": {
        "light": {"primary": "#1a6d8a", "secondary": "#17323d", "accent": "#12566e", "bg": "#f4f9fb", "text": "#17323d", "card": "#ffffff", "border": "#d6e6ec", "muted": "#5f7a84"},
        "dark": {"primary": "#6fb6cf", "secondary": "#0b1519", "accent": "#4a8fa8", "bg": "#0b1519", "text": "#e4f0f4", "card": "#122229", "border": "#23404c", "muted": "#87a3ad"},
    },
    "Slate": {
        "light": {"primary": "#4a5a68", "secondary": "#232a31", "accent": "#37434e", "bg": "#f6f7f8", "text": "#232a31", "card": "#ffffff", "border": "#dde1e5", "muted": "#6a7680"},
        "dark": {"primary": "#a8b6c2", "secondary": "#101418", "accent": "#7d8d9b", "bg": "#101418", "text": "#e9eef2", "card": "#191f26", "border": "#2a333d", "muted": "#8f9ba6"},
    },
    "Rose": {
        "light": {"primary": "#b0485e", "secondary": "#38242a", "accent": "#8c3749", "bg": "#fdf7f8", "text": "#38242a", "card": "#ffffff", "border": "#ecd9de", "muted": "#8d7078"},
        "dark": {"primary": "#df8ea0", "secondary": "#1c1115", "accent": "#b86a7e", "bg": "#1c1115", "text": "#f7e9ec", "card": "#291820", "border": "#402a32", "muted": "#ab8d95"},
    },
    "Olive": {
        "light": {"primary": "#6b7a3f", "secondary": "#2e3222", "accent": "#525f2e", "bg": "#f8f7f1", "text": "#2e3222", "card": "#ffffff", "border": "#e2e3d3", "muted": "#7a7d66"},
        "dark": {"primary": "#a8b86a", "secondary": "#141610", "accent": "#838f4e", "bg": "#141610", "text": "#eef0e2", "card": "#1e2117", "border": "#33392a", "muted": "#9aa08a"},
    },
}

_LIGHT_STATUS = {"danger": "#b42318", "danger_bg": "#fee4e2", "success": "#128a4b", "success_bg": "#dcfce7", "warn": "#92400e", "warn_bg": "#fef3c7"}
_DARK_STATUS = {"danger": "#e8836f", "danger_bg": "#3a201c", "success": "#7cc49a", "success_bg": "#1d3527", "warn": "#e0b35c", "warn_bg": "#3a2e18"}

_FRONTDESK_FALLBACK = {
    "primary": "#1a1a2e", "secondary": "#2b2b4a", "accent": "#e94560",
    "bg": "#fafafa", "text": "#1a1a1a", "card": "#ffffff", "border": "#e5e7eb", "muted": "#6b7280",
}


def _contrast_text(hex_color: str) -> str:
    """Pick '#ffffff' or '#1d1812' whichever has the higher WCAG contrast
    against the given background — robust for any brand color."""
    def _lum(c):
        c = c.lstrip("#")
        if len(c) != 6:
            return 0.0
        r, g, b = (int(c[i:i + 2], 16) / 255.0 for i in (0, 2, 4))
        f = lambda v: v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4
        return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)

    try:
        l1, l2 = _lum(hex_color), _lum("#ffffff")
        return "#ffffff" if (l1 + 0.05) / (l2 + 0.05) > (l2 + 0.05) / (l1 + 0.05) else "#1d1812"
    except Exception:
        return "#ffffff"


def resolve_theme(bs: dict) -> dict:
    """Return {'light': {...}, 'dark': {...}} palettes for the template.

    preset_theme (not 'Custom') wins; otherwise the individual color
    fields with sensible fallbacks, and dark mode derives dark surfaces
    while keeping the brand colors (Back House pattern).
    """
    preset = (bs.get("preset_theme") or "Custom").strip()
    base = THEME_PRESETS.get(preset)
    if base:
        out = {"light": dict(base["light"]), "dark": dict(base["dark"])}
    else:
        light = {
            "primary": bs.get("primary_color") or _FRONTDESK_FALLBACK["primary"],
            "secondary": bs.get("secondary_color") or _FRONTDESK_FALLBACK["secondary"],
            "accent": bs.get("accent_color") or _FRONTDESK_FALLBACK["accent"],
            "bg": bs.get("background_color") or _FRONTDESK_FALLBACK["bg"],
            "text": bs.get("text_color") or _FRONTDESK_FALLBACK["text"],
            "card": "#ffffff",
            "border": _FRONTDESK_FALLBACK["border"],
            "muted": _FRONTDESK_FALLBACK["muted"],
        }
        dark = {
            "primary": light["primary"], "secondary": _FRONTDESK_FALLBACK["secondary"],
            "accent": light["accent"], "bg": _FRONTDESK_FALLBACK["secondary"],
            "text": "#e8eaf6", "card": "#26264a", "border": "#3a3a5e", "muted": "#9a9ab0",
        }
        out = {"light": light, "dark": dark}
    for mode in ("light", "dark"):
        p = out[mode]
        p.update(_LIGHT_STATUS if mode == "light" else _DARK_STATUS)
        p["btn_text"] = _contrast_text(p["primary"])
        p["btn_accent_text"] = _contrast_text(p["accent"])
    return out
