// Copyright (c) 2026, Yasser Bousrih and contributors
// For license information, please see license.txt

frappe.ui.form.on("Customer Profile", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Book Appointment"), function () {
				window.open("/book", "_blank");
			}, __("Actions"));

			frm.add_custom_button(__("View Bookings"), function () {
				frappe.set_route("List", "Booking", { customer: frm.doc.name });
			}, __("Actions"));

			frm.add_custom_button(__("POS Checkout"), function () {
				window.open("/checkout", "_blank");
			}, __("Actions"));
		}
	},
});
