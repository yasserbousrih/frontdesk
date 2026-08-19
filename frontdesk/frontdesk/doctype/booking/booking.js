// Copyright (c) 2026, Yasser Bousrih and contributors
// For license information, please see license.txt

frappe.ui.form.on("Booking", {
	refresh: function (frm) {
		if (!frm.is_new()) {
			frm.add_custom_button(__("Live Board"), function () {
				window.open("/board", "_blank");
			}, __("Actions"));

			frm.add_custom_button(__("POS Checkout"), function () {
				window.open("/checkout?booking=" + encodeURIComponent(frm.doc.name), "_blank");
			}, __("Actions"));

			if (frm.doc.status === "Booked") {
				frm.add_custom_button(__("Seat Customer"), function () {
					frm.set_value("status", "Seated");
					frm.save();
				});
			} else if (frm.doc.status === "Seated" || frm.doc.status === "In Progress") {
				frm.add_custom_button(__("Complete Service"), function () {
					frm.set_value("status", "Completed");
					frm.save();
				});
			}
		}
	},

	service: function (frm) {
		if (frm.doc.service) {
			frappe.db.get_value("Item", frm.doc.service, ["standard_rate", "duration_minutes"], function (r) {
				if (r) {
					if (r.standard_rate && !frm.doc.price) {
						frm.set_value("price", r.standard_rate);
					}
					if (r.duration_minutes) {
						frm.set_value("duration_minutes", r.duration_minutes);
					}
				}
			});
		}
	},
});
