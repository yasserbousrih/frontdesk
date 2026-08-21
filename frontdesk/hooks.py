import frappe
from frappe import _
from frappe.utils import today

app_name = "frontdesk"
app_title = "FrontDesk"
app_publisher = "Yasser Bousrih"
app_description = "Booking, POS, and AI-powered front desk for service businesses."
app_email = "yasser@basira.tech"
app_license = "MIT"

# Hook registrations (dotted-path strings — bare functions in hooks.py are
# NOT picked up by frappe's hook loader, which filters out FunctionType).
# Implementation functions are named setup_* to avoid shadowing these strings.
after_install = "frontdesk.hooks.setup_after_install"
after_migrate = "frontdesk.hooks.setup_after_migrate"

def setup_after_migrate():
    """Re-ensure custom fields on every migrate — after_install only fires on
    fresh installs, so existing sites that pull this app would never get the
    Item custom fields without this.
    Also force-reload Business Settings so its Tab Break fields always land in
    tabDocField correctly (bench migrate skips rows that look unchanged but
    won't flush Redis meta — reload_doc guarantees the DB + cache are in sync
    with the JSON on every migrate and fresh clone/install)."""
    _ensure_custom_fields()
    # Force-sync Business Settings schema from JSON → DB + Redis
    try:
        frappe.reload_doc("Frontdesk", "doctype", "business_settings", force=True)
        frappe.db.commit()
    except Exception:
        pass


# -------------------
# Install hook — ensure custom roles + loyalty program exist
# -------------------
def setup_after_install():
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
    try:
        frappe.reload_doc("Frontdesk", "doctype", "business_settings", force=True)
        frappe.db.commit()
    except Exception:
        pass


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

_HOME_TOGGLES = (
    "show_hero", "show_story", "show_services", "show_prices",
    "show_how_it_works", "show_gallery", "show_testimonials",
    "show_visit", "show_cta_band",
)

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
        # business_name is mandatory on the doctype — a fresh site's row
        # fails validation on save without it.
        if not bs.get("business_name"):
            bs.set("business_name", "My Business")
            changed = True
        # Section toggles default ON on a fresh site. A full save() of the
        # single row writes every Check column as 0, so we must set them
        # explicitly BEFORE the first save or every section hides itself.
        for toggle in _HOME_TOGGLES:
            if bs.get(toggle) is None:
                bs.set(toggle, 1)
                changed = True
        for field, value in _HOME_SEED.items():
            if not bs.get(field) and value:
                bs.set(field, value)
                changed = True
        if changed:
            bs.save(ignore_permissions=True)

        if frappe.db.exists("DocType", "Item") and frappe.db.count(
            "Item", filters={"item_group": "Services"}
        ) == 0:
            for name, category, dur, price, desc in _SAMPLE_SERVICES:
                frappe.get_doc({
                    "doctype": "Item",
                    "item_code": name,
                    "item_name": name,
                    "item_group": "Services",
                    "is_stock_item": 0,
                    "stock_uom": "Nos",
                    "standard_rate": price,
                    "duration_minutes": dur,
                    "service_category": category,
                    "description": desc,
                    "show_on_homepage": 1,
                    "disabled": 0,
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
      commission tracking.
    - Item: ``duration_minutes``, ``service_category``, ``show_on_homepage``
      — services-as-items metadata used by the booking/availability engine
      and the public homepage."""
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

    if not frappe.db.exists("DocType", "Item"):
        return

    _upsert_custom_field(
        dt="Item",
        fieldname="duration_minutes",
        label="Duration (minutes)",
        fieldtype="Int",
        non_negative=1,
    )
    _upsert_custom_field(
        dt="Item",
        fieldname="service_category",
        label="Service Category",
        fieldtype="Data",
    )
    _upsert_custom_field(
        dt="Item",
        fieldname="show_on_homepage",
        label="Show on Homepage",
        fieldtype="Check",
        default="1",
    )
    _upsert_custom_field(
        dt="Item",
        fieldname="item_name_ar",
        label="Item Name (Arabic)",
        fieldtype="Data",
    )
    _upsert_custom_field(
        dt="Item",
        fieldname="department",
        label="Department",
        fieldtype="Select",
        options="\nDermatology\nCardiology\nPediatrics\nGeneral Medicine\nDental\nOphthalmology\nOrthopedics\nENT\nGynecology\nOther",
    )

    # Receipts print the Arabic name — the Sales Invoice Item row snapshots it
    # so epson_middleware renders bilingual EN/AR rows without re-looking-up.
    _upsert_custom_field(
        dt="Sales Invoice Item",
        fieldname="item_name_ar",
        label="Item Name (Arabic)",
        fieldtype="Data",
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
# Fixtures — Role Profiles ship with the app so they survive a clone /
# fresh install: export_fixtures dumps them to fixtures/role_profile.json
# and import_fixtures re-imports on every migrate.
# -------------------
fixtures = [
    {
        "dt": "Role Profile",
        "filters": [["role_profile", "in", ["Frontdesk Manager", "Frontdesk User"]]],
    },
]

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
