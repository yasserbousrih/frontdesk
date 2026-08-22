/**
 * FrontDesk i18n & Translation Manager
 * Supports zero-flash language restoration, RTL switching, MariaDB-backed
 * translations, and seamless instant language toggle.
 */

(function (window, document) {
  'use strict';

  var DEFAULT_LANG = 'en';
  var STORAGE_KEY = 'fd_lang';

  // Base fallback dictionary (matches backend UI_TRANSLATIONS)
  var DICTIONARY = {
    ar: {
      "Home": "الرئيسية",
      "Services": "الخدمات",
      "Our Services": "خدماتنا",
      "What we do": "ما نقدمه",
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
      "Select Services": "اختر الخدمات",
      "Select a Staff Member": "اختر الأخصائي",
      "Select Staff": "اختر الأخصائي",
      "Select Date & Time": "اختر التاريخ والوقت",
      "Your Details": "بياناتك",
      "Full Name": "الاسم الكامل",
      "Phone Number": "رقم الهاتف",
      "Phone": "الهاتف",
      "Email": "البريد الإلكتروني",
      "Address": "العنوان",
      "Location": "الموقع",
      "WhatsApp": "واتساب",
      "Instagram": "إنستغرام",
      "Notes": "ملاحظات إضافية",
      "Special instructions or preferences": "ملاحظات أو تفضيلات خاصة",
      "Confirm Booking": "تأكيد الحجز",
      "Back": "رجوع",
      "Next": "التالي",
      "Cancel": "إلغاء",
      "Reschedule": "إعادة جدولة",
      "Manage Appointment": "إدارة الموعد",
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
      "Get directions →": "الاتجاهات على الخريطة ←",
      "Contact Us": "تواصل معنا",
      "Find us": "موقعنا",
      "Hours & Visit": "ساعات العمل والموقع",
      "Opening Hours": "ساعات العمل",
      "About Us": "من نحن",
      "Our Story": "قصتنا",
      "Simple steps": "خطوات بسيطة",
      "How It Works": "كيف يعمل",
      "Take a look": "معرض الصور",
      "Gallery": "المعرض",
      "Kind words": "آراء العملاء",
      "Testimonials": "آراء العملاء",
      "Happy Clients": "عملاء سعداء",
      "Happy client": "عميل سعيد",
      "Staff Queue": "قائمة انتظار الموظف",
      "Station Board": "لوحة المحطات",
      "POS Checkout": "نقطة البيع والدفع",
      "My Schedule": "جدولي اليومي",
      "Booked": "محجوز",
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
      "Mon–Sat · 9:00 AM – 8:00 PM": "من الإثنين إلى السبت · ٩:٠٠ ص – ٨:٠٠ م"
    }
  };

  // Merge server-injected translations if present
  if (window.FD_SERVER_TRANSLATIONS) {
    DICTIONARY.ar = Object.assign({}, DICTIONARY.ar, window.FD_SERVER_TRANSLATIONS);
  }

  function getLang() {
    try {
      var saved = localStorage.getItem(STORAGE_KEY);
      if (saved === 'ar' || saved === 'en') return saved;
    } catch (e) {}
    return DEFAULT_LANG;
  }

  function t(key, fallback) {
    var lang = getLang();
    if (lang === 'en') return fallback || key;
    if (DICTIONARY.ar && DICTIONARY.ar[key]) {
      return DICTIONARY.ar[key];
    }
    return fallback || key;
  }

  function setLanguage(lang) {
    if (lang !== 'ar' && lang !== 'en') lang = DEFAULT_LANG;
    try {
      localStorage.setItem(STORAGE_KEY, lang);
      document.cookie = STORAGE_KEY + '=' + lang + ';path=/;max-age=31536000';
    } catch (e) {}
    applyLanguage(lang);
  }

  function toggleLanguage() {
    var cur = getLang();
    var next = cur === 'ar' ? 'en' : 'ar';
    setLanguage(next);
  }

  function applyLanguage(lang) {
    document.documentElement.lang = lang;
    document.documentElement.dir = (lang === 'ar') ? 'rtl' : 'ltr';

    // Update toggle buttons across page
    var toggles = document.querySelectorAll('.lang-toggle, #langToggle');
    toggles.forEach(function (btn) {
      var textEl = btn.querySelector('.lang-text, .lang-label');
      if (textEl) {
        textEl.textContent = (lang === 'ar') ? 'English' : 'العربية';
      }
    });

    // Translate [data-i18n] text nodes
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (!el.hasAttribute('data-i18n-en')) {
        el.setAttribute('data-i18n-en', el.textContent.trim());
      }
      if (lang === 'ar') {
        var tr = (DICTIONARY.ar && DICTIONARY.ar[key]) || el.getAttribute('data-i18n-ar') || key;
        el.textContent = tr;
      } else {
        el.textContent = el.getAttribute('data-i18n-en') || key;
      }
    });

    // Translate [data-i18n-placeholder] input fields
    document.querySelectorAll('[data-i18n-placeholder]').forEach(function (el) {
      var key = el.getAttribute('data-i18n-placeholder');
      if (!el.hasAttribute('data-placeholder-en')) {
        el.setAttribute('data-placeholder-en', el.getAttribute('placeholder') || '');
      }
      if (lang === 'ar') {
        var tr = (DICTIONARY.ar && DICTIONARY.ar[key]) || el.getAttribute('data-placeholder-ar') || key;
        el.setAttribute('placeholder', tr);
      } else {
        el.setAttribute('placeholder', el.getAttribute('data-placeholder-en') || key);
      }
    });

    // Dispatch event for dynamic single-page components
    window.dispatchEvent(new CustomEvent('fd:language-change', {
      detail: { language: lang, dir: (lang === 'ar') ? 'rtl' : 'ltr' }
    }));
  }

  // Pre-load dynamic translations from API in background if needed
  function fetchRemoteTranslations() {
    if (typeof fetch === 'function') {
      fetch('/api/method/frontdesk.api.translation.get_translations?lang=ar')
        .then(function (r) { return r.json(); })
        .then(function (data) {
          if (data && data.message && data.message.translations) {
            DICTIONARY.ar = Object.assign({}, DICTIONARY.ar, data.message.translations);
            if (getLang() === 'ar') {
              applyLanguage('ar');
            }
          }
        })
        .catch(function () {});
    }
  }

  // Auto-translate helper for custom dynamically added terms
  function translateMissing(text, callback) {
    if (!text || getLang() === 'en') {
      if (callback) callback(text);
      return;
    }
    if (DICTIONARY.ar && DICTIONARY.ar[text]) {
      if (callback) callback(DICTIONARY.ar[text]);
      return;
    }
    if (typeof fetch === 'function') {
      fetch('/api/method/frontdesk.api.translation.translate_text?text=' + encodeURIComponent(text) + '&target_lang=ar')
        .then(function (r) { return r.json(); })
        .then(function (data) {
          var res = (data && data.message && data.message.translated) ? data.message.translated : text;
          if (DICTIONARY.ar) DICTIONARY.ar[text] = res;
          if (callback) callback(res);
        })
        .catch(function () {
          if (callback) callback(text);
        });
    }
  }

  // Expose API on window
  window.FrontDeskI18n = {
    getLang: getLang,
    setLanguage: setLanguage,
    toggleLanguage: toggleLanguage,
    t: t,
    applyLanguage: applyLanguage,
    translateMissing: translateMissing,
    dictionary: DICTIONARY
  };
  window.t = t;
  window.toggleLanguage = toggleLanguage;

  // Initialize on DOM ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', function () {
      applyLanguage(getLang());
      fetchRemoteTranslations();
    });
  } else {
    applyLanguage(getLang());
    fetchRemoteTranslations();
  }

})(window, document);
