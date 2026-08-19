// Copyright (c) 2026, Yasser Bousrih and contributors
// For license information, please see license.txt

frappe.ui.form.on("Staff Member", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("View Schedule"), function () {
				window.open("/my_schedule", "_blank");
			}, __("Actions"));

			frm.add_custom_button(__("View Bookings"), function () {
				frappe.set_route("List", "Booking", { staff: frm.doc.name });
			}, __("Actions"));

			frm.add_custom_button(__("Book Slot"), function () {
				window.open("/book?staff=" + encodeURIComponent(frm.doc.name), "_blank");
			}, __("Actions"));
		}
	},
});
