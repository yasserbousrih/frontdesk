# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
import requests

def send_booking_confirmation(doc, method):
    """Called via doc_events after_insert hook on Booking.
    Sends WhatsApp confirmation via Omnichat send API.
    Skips walk-ins and bookings where Omnichat is not configured."""
    if doc.source == "Walk-in":
        return

    bs = frappe.get_single("Business Settings")
    if not (bs.omnichat_api_url and bs.omnichat_api_token):
        return

    customer = frappe.get_doc("Customer Profile", doc.customer)
    if not customer.phone:
        return

    staff_name = frappe.db.get_value("Staff Member", doc.staff, "staff_name")
    
    service_names = []
    if doc.get("services"):
        service_names = [s.service_name or frappe.db.get_value("Item", s.service, "item_name") for s in doc.services if s.service]
    if not service_names and doc.service:
        service_names = [frappe.db.get_value("Item", doc.service, "item_name")]
    services_str = ", ".join(filter(None, service_names)) or "Appointment"

    reschedule_url = ""
    if doc.reschedule_token:
        reschedule_url = frappe.utils.get_url(f"/reschedule?token={doc.reschedule_token}")

    message = (
        f"✅ Booking Confirmed\n\n"
        f"💈 {services_str} with {staff_name}\n"
        f"📅 {doc.booking_date}\n"
        f"🕐 {str(doc.start_time)[:5]}\n"
    )
    if reschedule_url:
        message += f"\nNeed to change or cancel? Manage your booking:\n{reschedule_url}\n"
    message += f"\nSee you soon! — {bs.business_name}"

    payload = {
        "to": customer.phone,
        "message": message,
    }
    if bs.omnichat_sender_id:
        payload["sender"] = bs.omnichat_sender_id

    try:
        resp = requests.post(
            bs.omnichat_api_url.rstrip("/") + "/send",
            headers={"Authorization": f"Bearer {bs.omnichat_api_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
    except Exception:
        frappe.log_error(f"FrontDesk: WhatsApp confirmation failed for booking {doc.name}")