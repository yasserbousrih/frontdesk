import frappe
from frappe import _
from frappe.utils import today

app_name = "frontdesk"
app_title = "FrontDesk"
app_publisher = "Yasser Bousrih"
app_description = "Booking, POS, and AI-powered front desk for service businesses."
app_email = "yasser@basira.tech"
app_license = "MIT"

# -------------------
# Install hook — ensure custom roles + loyalty program exist
# -------------------
def after_install():
    """Create custom roles on first install so the DocType permissions
    referencing them don't fail the install. Also seed the default
    FrontDesk Rewards loyalty program if ERPNext is installed."""
    for role_name in ("Frontdesk Manager", "Frontdesk User"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(
                ignore_permissions=True
            )
    _ensure_loyalty_program()


def _ensure_loyalty_program():
    """Create a simple 1-point-per-unit loyalty program if ERPNext is present."""
    if not frappe.db.exists("DocType", "Loyalty Program"):
        return
    if frappe.db.exists("Loyalty Program", "FrontDesk Rewards"):
        return
    frappe.get_doc({
        "doctype": "Loyalty Program",
        "loyalty_program_name": "FrontDesk Rewards",
        "auto_opt_in": 1,
        "from_date": today(),
        "collection_rules": [{
            "tier_name": "Bronze",
            "collection_factor": 1,
            "minimum_total_spent": 0,
        }],
    }).insert(ignore_permissions=True)

# -------------------
# Fixtures (none for now — vertical templates come in Phase 4)
# -------------------
# fixtures = []

# -------------------
# Document events
# -------------------
doc_events = {
    "Booking": {
        "after_insert": "frontdesk.api.notifications.send_booking_confirmation",
        "on_update": "frontdesk.api.followups.on_booking_update",
    },
    "Customer Profile": {
        "on_update": "frontdesk.api.basira_crm.sync_customer_to_basira",
    }
}

# -------------------
# Scheduled tasks
# -------------------
scheduler_events = {
    "hourly": [
        "frontdesk.api.reminders.send_2h_reminders"
    ]
}

# -------------------
# Permissions
# -------------------
# permission_query_conditions = {
#     "Booking": "frontdesk.frontdesk.doctype.booking.booking.get_permission_query_conditions"
# }
