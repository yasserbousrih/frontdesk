"""Help links shown on the Frontdesk module page in Desk."""
from frappe import _


def get_data():
    return [
        {
            "label": _("FrontDesk Documentation"),
            "items": [
                {
                    "type": "help",
                    "label": _("Stack Decisions"),
                    "docs_url": "https://github.com/yasserbousrih/frontdesk/blob/master/docs/STACK.md",
                },
                {
                    "type": "help",
                    "label": _("Build Plan"),
                    "docs_url": "https://github.com/yasserbousrih/frontdesk/blob/master/docs/PLAN.md",
                },
            ],
        }
    ]
