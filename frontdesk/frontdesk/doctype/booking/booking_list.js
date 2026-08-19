frappe.listview_settings["Booking"] = {
	add_fields: ["customer", "staff", "service", "booking_date", "start_time", "end_time", "status", "price"],
	get_indicator: function (doc) {
		const colors = {
			"Booked": "blue",
			"Seated": "orange",
			"In Progress": "purple",
			"Completed": "cyan",
			"Paid": "green",
			"Cancelled": "red",
			"No-Show": "darkgrey",
		};
		const color = colors[doc.status] || "gray";
		return [__(doc.status), color, "status,=," + doc.status];
	},
	onload: function (listview) {
		listview.page.add_inner_button(__("Live Board"), function () {
			window.open("/board", "_blank");
		});
		listview.page.add_inner_button(__("POS Checkout"), function () {
			window.open("/checkout", "_blank");
		});
		listview.page.add_inner_button(__("Online Booking"), function () {
			window.open("/book", "_blank");
		});
	},
};
