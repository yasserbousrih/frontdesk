import frappe
from frappe import _

app_name = "frontdesk"
app_title = "FrontDesk"
app_publisher = "Yasser Bousrih"
app_description = "Booking, POS, and AI-powered front desk for service businesses."
app_email = "yasser@basira.tech"
app_license = "MIT"

# -------------------
# Install hook — ensure custom roles exist before DocType perms are applied
# -------------------
def after_install():
    """Create custom roles on first install so the DocType permissions
    referencing them don't fail the install."""
    for role_name in ("Frontdesk Manager", "Frontdesk User"):
        if not frappe.db.exists("Role", role_name):
            frappe.get_doc({"doctype": "Role", "role_name": role_name}).insert(
                ignore_permissions=True
            )

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
    }
}

# -------------------
# Scheduled tasks (Phase 2)
# -------------------
# scheduler_events = {
#     "hourly": [
#         "frontdesk.api.reminders.send_2h_reminders"
#     ]
# }

# -------------------
# Permissions
# -------------------
# permission_query_conditions = {
#     "Booking": "frontdesk.frontdesk.doctype.booking.booking.get_permission_query_conditions"
# }
