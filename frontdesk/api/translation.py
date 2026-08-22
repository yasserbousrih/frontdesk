"""Translation helper and API endpoints for FrontDesk.

Supports on-the-fly translation with automatic caching in MariaDB
(`tabTranslation` DocType), batch translation, service item name
auto-translation, and frontend dictionary delivery for language selector.
"""

import json
import urllib.parse
import urllib.request
import frappe
from frappe import _

# Standard UI dictionary for immediate zero-latency rendering
UI_TRANSLATIONS = {
    "ar": {
        "Home": "الرئيسية",
        "Services": "الخدمات",
        "Our Services": "خدماتنا",
        "Book Appointment": "احجز موعداً",
        "Book Now": "احجز الآن",
        "Book a Session": "احجز جلسة",
        "Book a Consultation": "احجز استشارة",
        "Book a Treatment": "احجز علاجاً",
        "Book a Manicure": "احجز مانيكير",
        "Pick Your Service": "اختر الخدمة",
        "Choose a Time": "اختر الوقت",
        "Get Reminded": "تذكير تلقائي",
        "Select a Service": "اختر الخدمة",
        "Select a Staff Member": "اختر الأخصائي",
        "Select Date & Time": "اختر التاريخ والوقت",
        "Your Details": "بياناتك",
        "Full Name": "الاسم الكامل",
        "Phone Number": "رقم الهاتف",
        "Notes": "ملاحظات إضافية",
        "Special instructions or preferences": "ملاحظات أو تفضيلات خاصة",
        "Confirm Booking": "تأكيد الحجز",
        "Back": "رجوع",
        "Next": "التالي",
        "Cancel": "إلغاء",
        "Reschedule": "إعادة جدولة",
        "Date": "التاريخ",
        "Time": "الوقت",
        "Staff": "الأخصائي",
        "Price": "السعر",
        "Total": "المجموع",
        "Duration": "المدة",
        "min": "دقيقة",
        "Deposit Required": "عربون مطلوب",
        "Pay Deposit": "دفع العربون",
        "Pay on Service": "الدفع عند الخدمة",
        "Online Payment": "دفع إلكتروني",
        "Any Available Staff": "أي أخصائي متاح",
        "No slots available for this date": "لا توجد مواعيد متاحة في هذا اليوم",
        "Booking Confirmed": "تم تأكيد الحجز بنجاح",
        "Thank you! Your booking reference is": "شكراً لك! رقم حجزك هو",
        "We sent details to your WhatsApp": "تم إرسال تفاصيل الحجز عبر واتساب",
        "View Location": "عرض الموقع",
        "Contact Us": "تواصل معنا",
        "Opening Hours": "ساعات العمل",
        "About Us": "من نحن",
        "Our Story": "قصتنا",
        "How It Works": "كيف يعمل",
        "Testimonials": "آراء العملاء",
        "Happy Clients": "عملاء سعداء",
        "Staff Queue": "قائمة انتظار الموظف",
        "Station Board": "لوحة الصالون / العيادة",
        "POS Checkout": "نقطة البيع والدفع",
        "My Schedule": "جدولي اليومي",
        "Seated": "جالس بالكرسي",
        "In Progress": "قيد التنفيذ",
        "Completed": "مكتمل",
        "Paid": "تم الدفع",
        "Formula / Notes": "التركيبة / الملاحظات الفنية",
        "Save Notes": "حفظ الملاحظات",
        "Quick Actions": "إجراءات سريعة",
        "Walk-in": "عميل مباشر",
        "Add Walk-in": "إضافة عميل مباشر",
        "Today's Summary": "ملخص اليوم",
        "Commission": "العمولة",
        "Visits": "الزيارات",
        "Language": "اللغة",
        "English": "English",
        "Arabic": "العربية",
        "Reserve your spot in seconds — pick a time that works for you.": "احجز موعدك في ثوانٍ — اختر الوقت المناسب لك.",
        "Mon–Sat · 9:00 AM – 8:00 PM": "من الإثنين إلى السبت · ٩:٠٠ ص – ٨:٠٠ م",
    }
}


def _query_free_translation_api(text: str, target_lang: str = "ar", source_lang: str = "en") -> str | None:
    """Query free MyMemory Translation API."""
    if not text or not text.strip():
        return text
    clean_text = text.strip()
    try:
        url = f"https://api.mymemory.translated.net/get?q={urllib.parse.quote(clean_text)}&langpair={source_lang}|{target_lang}"
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) FrontDesk/1.0",
                "Accept": "application/json",
            },
        )
        with urllib.request.urlopen(req, timeout=6) as res:
            if res.status == 200:
                data = json.loads(res.read().decode("utf-8"))
                resp_data = data.get("responseData", {})
                translated = resp_data.get("translatedText")
                if translated and not translated.startswith("MYMEMORY WARNING"):
                    return translated.strip()
    except Exception as e:
        frappe.log_error(f"Translation API error for '{text}': {e}", "FrontDesk Translation")
    return None


def get_cached_translation(text: str, target_lang: str = "ar") -> str | None:
    """Look up an existing translation in MariaDB `tabTranslation`."""
    if not text:
        return ""
    try:
        res = frappe.db.get_value(
            "Translation",
            {"language": target_lang, "source_text": text.strip()},
            "translated_text",
        )
        if res:
            return res
    except Exception:
        pass
    return None


def save_translation_to_db(source_text: str, translated_text: str, target_lang: str = "ar"):
    """Persist a translation into MariaDB `tabTranslation`."""
    if not source_text or not translated_text or source_text == translated_text:
        return
    source_clean = source_text.strip()
    trans_clean = translated_text.strip()
    try:
        existing = frappe.db.get_value(
            "Translation",
            {"language": target_lang, "source_text": source_clean},
            "name",
        )
        if existing:
            frappe.db.set_value("Translation", existing, "translated_text", trans_clean)
        else:
            doc = frappe.get_doc({
                "doctype": "Translation",
                "language": target_lang,
                "source_text": source_clean,
                "translated_text": trans_clean,
            })
            doc.insert(ignore_permissions=True)
        frappe.db.commit()
    except Exception as e:
        frappe.log_error(f"Failed saving translation '{source_text}': {e}", "FrontDesk Translation")


@frappe.whitelist(allow_guest=True)
def translate_text(text: str, target_lang: str = "ar", source_lang: str = "en") -> dict:
    """Translate a single text string with DB cache check & auto-save."""
    if not text or not text.strip():
        return {"source": text, "translated": text, "cached": True}

    clean_text = text.strip()

    # 1. Check DB Cache
    cached = get_cached_translation(clean_text, target_lang)
    if cached:
        return {"source": clean_text, "translated": cached, "cached": True}

    # 2. Check Static Fallback Map
    static_val = UI_TRANSLATIONS.get(target_lang, {}).get(clean_text)
    if static_val:
        save_translation_to_db(clean_text, static_val, target_lang)
        return {"source": clean_text, "translated": static_val, "cached": False}

    # 3. Call Free Translation API
    translated = _query_free_translation_api(clean_text, target_lang, source_lang)
    if translated:
        save_translation_to_db(clean_text, translated, target_lang)
        return {"source": clean_text, "translated": translated, "cached": False}

    return {"source": clean_text, "translated": clean_text, "cached": False}


@frappe.whitelist(allow_guest=True)
def get_translations(lang: str = "ar") -> dict:
    """Return all translations for `lang` as a key-value dictionary."""
    dictionary = dict(UI_TRANSLATIONS.get(lang, {}))
    try:
        db_translations = frappe.get_all(
            "Translation",
            filters={"language": lang},
            fields=["source_text", "translated_text"],
        )
        for r in db_translations:
            if r.get("source_text") and r.get("translated_text"):
                dictionary[r["source_text"]] = r["translated_text"]
    except Exception:
        pass
    return {"language": lang, "translations": dictionary}


@frappe.whitelist(allow_guest=True)
def translate_batch(texts: list | str, target_lang: str = "ar", source_lang: str = "en") -> dict:
    """Batch-translate a list of strings, reusing cache and saving new ones."""
    if isinstance(texts, str):
        try:
            texts = json.loads(texts)
        except Exception:
            texts = [texts]

    if not isinstance(texts, list):
        return {"translations": {}}

    results = {}
    missing = []

    for t in texts:
        if not t or not str(t).strip():
            continue
        st = str(t).strip()
        cached = get_cached_translation(st, target_lang)
        if cached:
            results[st] = cached
        elif st in UI_TRANSLATIONS.get(target_lang, {}):
            val = UI_TRANSLATIONS[target_lang][st]
            results[st] = val
            save_translation_to_db(st, val, target_lang)
        else:
            missing.append(st)

    for m in missing:
        translated = _query_free_translation_api(m, target_lang, source_lang)
        if translated:
            results[m] = translated
            save_translation_to_db(m, translated, target_lang)
        else:
            results[m] = m

    return {"translations": results}


def auto_translate_item(doc, method=None):
    """Doc event hook: Auto-translate Service Item Name to Arabic if missing."""
    if getattr(doc, "item_group", "") == "Services" and getattr(doc, "item_name", ""):
        if not getattr(doc, "item_name_ar", ""):
            res = translate_text(doc.item_name, target_lang="ar", source_lang="en")
            if res.get("translated") and res["translated"] != doc.item_name:
                doc.item_name_ar = res["translated"]
