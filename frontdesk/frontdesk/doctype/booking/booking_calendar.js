frappe.views.calendar["Booking"] = {
	field_map: {
		start: "booking_date",
		end: "booking_date",
		id: "name",
		title: "customer",
		allDay: "allDay",
	},
	style_map: {
		"Booked": "info",
		"Seated": "warning",
		"In Progress": "primary",
		"Completed": "success",
		"Paid": "success",
		"Cancelled": "danger",
		"No-Show": "secondary",
	},
	get_events_method: "frontdesk.api.bookings.get_booking_events",
};
