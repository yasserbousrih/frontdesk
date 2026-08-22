# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Post-paid follow-up — triggered via the ``on_update`` Booking doc_event.

When a booking transitions to ``Paid``, sends a WhatsApp message with a
rebooking link and (optionally) a Google review prompt.
"""

import frappe
import requests


def on_booking_update(doc, method):
    """Fired by Frappe on every Booking save. Only acts when status == Paid
    and the follow_up_sent flag hasn't been set yet.
    """
    if doc.status == "Paid" and not doc.follow_up_sent:
        if send_post_paid_message(doc):
            doc.db_set("follow_up_sent", 1, update_modified=False)


def send_post_paid_message(doc):
    """Send rebooking + review prompt via Omnichat."""
    bs = frappe.get_single("Business Settings")
    if not (bs.get("omnichat_api_url") and bs.get("omnichat_api_token")):
        return True  # nothing to do — mark as handled

    customer = frappe.get_doc("Customer Profile", doc.customer)
    if not customer.phone:
        return True  # no phone to send to — mark as handled

    staff_name = frappe.db.get_value("Staff Member", doc.staff, "staff_name")
    
    # Multi-service support
    service_names = []
    if doc.get("services"):
        service_names = [s.service_name or frappe.db.get_value("Item", s.service, "item_name") for s in doc.services if s.service]
    if not service_names and doc.service:
        service_names = [frappe.db.get_value("Item", doc.service, "item_name")]
    services_str = ", ".join(filter(None, service_names)) or "Appointment"

    book_link = frappe.utils.get_url("/book")
    review_link = bs.get("google_review_url") or ""

    message = (
        f"Thanks for visiting {bs.business_name}! 💈\n\n"
        f"{services_str} with {staff_name}\n\n"
        f"📅 Book your next visit:\n{book_link}\n"
    )
    if review_link:
        message += f"\n⭐ Enjoyed your visit? Leave a review:\n{review_link}"

    payload = {"to": customer.phone, "message": message}
    if bs.get("omnichat_sender_id"):
        payload["sender"] = bs.omnichat_sender_id

    try:
        resp = requests.post(
            bs.omnichat_api_url.rstrip("/") + "/send",
            headers={"Authorization": f"Bearer {bs.omnichat_api_token}", "Content-Type": "application/json"},
            json=payload, timeout=10,
        )
        resp.raise_for_status()
        return True
    except Exception:
        frappe.log_error(f"FrontDesk: post-paid follow-up failed for booking {doc.name}")
        return False
