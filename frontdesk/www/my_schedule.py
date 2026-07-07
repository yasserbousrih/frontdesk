import frappe
from frappe.utils import today, add_days

def get_context(context):
    # Require login — redirect if not authenticated
    if frappe.session.user == "Guest":
        frappe.local.login_manager.require_login = True
        raise frappe.Redirect

    # Find Staff Member linked to this user
    staff = frappe.db.get_value("Staff Member", {"user": frappe.session.user}, "name")
    if not staff:
        frappe.throw("No staff profile linked to your account.", frappe.PermissionError)

    context.no_cache = 1
    context.business = frappe.get_single("Business Settings")
    context.staff_name = frappe.db.get_value("Staff Member", staff, "staff_name")

    # Today's bookings
    context.today_bookings = _get_bookings(staff, today(), today())
    # Upcoming (next 7 days, excluding today)
    context.upcoming_bookings = _get_bookings(staff, add_days(today(), 1), add_days(today(), 7))
    return context

def _get_bookings(staff, from_date, to_date):
    bookings = frappe.get_all("Booking",
        filters={"staff": staff, "booking_date": ["between", [from_date, to_date]], "status": ["not in", ["Cancelled", "No-Show"]]},
        fields=["name", "customer", "service", "booking_date", "start_time", "end_time", "status"],
        order_by="booking_date asc, start_time asc")
    if not bookings:
        return []
    # Batch-load names to avoid N+1
    customer_ids = {b["customer"] for b in bookings}
    service_ids = {b["service"] for b in bookings}
    customer_names = {
        r["name"]: r["customer_name"]
        for r in frappe.get_all("Customer Profile", filters={"name": ["in", list(customer_ids)]}, fields=["name", "customer_name"])
    }
    service_names = {
        r["name"]: r["service_name"]
        for r in frappe.get_all("Service", filters={"name": ["in", list(service_ids)]}, fields=["name", "service_name"])
    }
    for b in bookings:
        b.customer_name = customer_names.get(b.customer, "")
        b.service_name = service_names.get(b.service, "")
    return bookings