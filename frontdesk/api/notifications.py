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
    service_name = frappe.db.get_value("Service", doc.service, "service_name")

    message = (
        f"✅ Booking Confirmed\n\n"
        f"{service_name} with {staff_name}\n"
        f"📅 {doc.booking_date}\n"
        f"🕐 {str(doc.start_time)[:5]}\n\n"
        f"See you soon! — {bs.business_name}"
    )

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