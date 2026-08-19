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
    _ensure_custom_fields()
    _seed_homepage_defaults()


# -------------------
# Homepage defaults — the page is fully editable from Business Settings,
# these only fill the gaps on a fresh site (Back House seeding pattern).
# -------------------
_HOME_SEED = {
    "story_text": (
        "We're built around one idea: your time matters. Book in seconds, "
        "get a reminder before your visit, and walk out feeling your best."
    ),
    "hours_text": "Mon–Sat · 9:00 AM – 8:00 PM",
    "testimonial_1_text": "Booking took ten seconds and they were right on time. Best experience I've had.",
    "testimonial_1_author": "Ahmed K.",
    "testimonial_2_text": "Love being able to see availability and lock a slot without calling.",
    "testimonial_2_author": "Lina M.",
}

_SAMPLE_SERVICES = [
    ("Haircut", "Cut & Style", 45, 60, "Classic cut, washed and styled to your shape."),
    ("Beard Trim", "Grooming", 20, 30, "Sharp lines and a shape-up that lasts."),
    ("Hair + Beard", "Cut & Style", 60, 85, "The full package — fresh cut with a clean beard trim."),
    ("Kids Haircut", "Cut & Style", 30, 40, "Patient, gentle cuts for the little ones."),
]


def _seed_homepage_defaults():
    """Fill empty homepage fields + sample services on a fresh site.

    Idempotent: only writes when the target is empty, so re-running after
    the owner customises the site changes nothing.
    """
    try:
        bs = frappe.get_single("Business Settings")
        changed = False
        for field, value in _HOME_SEED.items():
            if not bs.get(field) and value:
                bs.set(field, value)
                changed = True
        if changed:
            bs.save(ignore_permissions=True)

        if frappe.db.count("Service") == 0:
            for name, category, dur, price, desc in _SAMPLE_SERVICES:
                frappe.get_doc({
                    "doctype": "Service",
                    "service_name": name,
                    "category": category,
                    "duration_minutes": dur,
                    "price": price,
                    "description": desc,
                    "active": 1,
                }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Homepage seed failed: {e}", "FrontDesk Install")


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


def _ensure_custom_fields():
    """Create Custom Fields that FrontDesk needs on ERPNext doctypes.

    - Sales Invoice Item: ``staff_member`` — link to Staff Member for
      commission tracking."""
    if not frappe.db.exists("DocType", "Sales Invoice"):
        return  # ERPNext not installed — nothing to patch

    _upsert_custom_field(
        dt="Sales Invoice Item",
        fieldname="staff_member",
        label="Staff Member",
        fieldtype="Link",
        options="Staff Member",
        insert_after="item_name",
        read_only=1,
    )


def _upsert_custom_field(dt, fieldname, **kwargs):
    """Create a Custom Field if it doesn't exist; no-op otherwise."""
    if frappe.db.exists("Custom Field", f"{dt}-{fieldname}"):
        return
    frappe.get_doc({
        "doctype": "Custom Field",
        "dt": dt,
        "fieldname": fieldname,
        **kwargs,
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
