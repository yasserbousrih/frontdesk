from frappe import _


def get_data():
    """Desk tile shown under the Frontdesk module."""
    return [
        {
            "module_name": "Frontdesk",
            "color": "#5B7CFA",
            "icon": "fa fa-calendar-check-o",
            "type": "module",
            "label": _("FrontDesk"),
        }
    ]
