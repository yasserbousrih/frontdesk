# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

"""Basira CRM sync — pushes customer profiles to the CRM of record."""

import frappe
import requests


def sync_customer_to_basira(doc, method):
    """Called via on_update doc_event on Customer Profile.

    POSTs the customer's name + phone to Basira CRM's internal upsert
    endpoint. Stores the returned ``basira_crm_id`` on the profile so
    subsequent syncs update the same record.

    Silently skips when:
      * Basira CRM is not configured
      * The customer has no phone (nothing to link)
      * The API returns a non-2xx — logged for ops review
    """
    bs = frappe.get_single("Business Settings")
    if not (bs.get("basira_crm_api_url") and bs.get("basira_crm_secret")):
        return

    # No phone = nothing to dedupe on in CRM
    if not doc.phone:
        return

    payload = {
        "phone": doc.phone,
        "name": doc.customer_name,
        "source": "frontdesk",
    }
    if doc.get("email"):
        payload["email"] = doc.email
    if doc.get("basira_crm_id"):
        payload["external_id"] = doc.basira_crm_id

    try:
        resp = requests.post(
            bs.basira_crm_api_url.rstrip("/") + "/internal/contacts/upsert",
            headers={
                "Authorization": f"Bearer {bs.basira_crm_secret}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        crm_id = resp.json().get("id")
        if crm_id and crm_id != doc.basira_crm_id:
            frappe.db.set_value("Customer Profile", doc.name, "basira_crm_id", crm_id, update_modified=False)
    except Exception:
        frappe.log_error(f"FrontDesk: Basira CRM sync failed for customer {doc.name}")
