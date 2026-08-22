# Copyright (c) 2026, Yasser Bousrih and contributors
# For license information, please see license.txt

import frappe
from frappe.tests.utils import FrappeTestCase
from frontdesk.api.translation import (
    translate_text,
    get_translations,
    translate_batch,
    auto_translate_item,
)
from frontdesk.www._branding import get_branding


class TestFrontDeskTranslation(FrappeTestCase):
    def setUp(self):
        super().setUp()
        frappe.set_user("Administrator")

    def test_translate_text_single_and_cached(self):
        # 1. Translate string
        res = translate_text("Consultation & Skin Care", target_lang="ar", source_lang="en")
        self.assertIn("translated", res)
        self.assertTrue(len(res["translated"]) > 0)

        # 2. Verify stored in tabTranslation
        db_val = frappe.db.get_value("Translation", {"language": "ar", "source_text": "Consultation & Skin Care"}, "translated_text")
        self.assertEqual(db_val, res["translated"])

        # 3. Verify subsequent call hits cache
        cached_res = translate_text("Consultation & Skin Care", target_lang="ar", source_lang="en")
        self.assertTrue(cached_res.get("cached"))
        self.assertEqual(cached_res["translated"], res["translated"])

    def test_get_translations_dictionary(self):
        res_ar = get_translations(lang="ar")
        self.assertEqual(res_ar.get("language"), "ar")
        self.assertIn("translations", res_ar)
        self.assertIn("Book Appointment", res_ar["translations"])

        res_fr = get_translations(lang="fr")
        self.assertEqual(res_fr.get("language"), "fr")
        self.assertIn("translations", res_fr)

    def test_translate_batch(self):
        keys = ["Book Appointment", "Staff Queue", "Payment Methods"]
        batch_res = translate_batch(keys, target_lang="ar")
        self.assertIn("translations", batch_res)
        for k in keys:
            self.assertIn(k, batch_res["translations"])
            self.assertTrue(len(batch_res["translations"][k]) > 0)

    def test_auto_translate_service_item(self):
        item_code = "Test Auto Translate Service"
        if frappe.db.exists("Item", item_code):
            frappe.delete_doc("Item", item_code, force=1)

        item = frappe.get_doc({
            "doctype": "Item",
            "item_code": item_code,
            "item_name": "Deluxe Head Massage",
            "item_group": "Services",
            "is_stock_item": 0,
        })
        auto_translate_item(item)
        self.assertTrue(bool(item.item_name_ar))
        self.assertNotEqual(item.item_name_ar, "")

    def test_branding_language_resolution(self):
        from werkzeug.test import EnvironBuilder
        from werkzeug.wrappers import Request

        builder = EnvironBuilder(headers={"Cookie": "preferred_language=ar"})
        frappe.local.request = Request(builder.get_environ())

        branding = get_branding()
        self.assertEqual(branding.get("lang"), "ar")
        self.assertTrue(branding.get("is_rtl"))
