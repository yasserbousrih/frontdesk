import frappe
from frappe.model.document import Document


class FrontDeskGatewaySettings(Document):
	"""Hosted-checkout controller for the custom FrontDesk gateway.

	ERPNext's Payment Request resolves the gateway controller by the
	Payment Gateway name — "FrontDesk Gateway" → this Settings single —
	and calls get_payment_url(). In demo mode the hosted checkout
	(/fd-pay) shows the booking details and simulates payment; live mode
	swaps in the configured PSP (api_base_url + merchant_key/merchant_secret).
	"""

	def validate_transaction_currency(self, currency):
		# Accept any currency configured for the site
		return

	def get_payment_url(self, **kwargs):
		"""The guest lands here to pay: the hosted checkout page."""
		reference_docname = kwargs.get("reference_docname")
		return f"/fd_pay?pr={reference_docname}"

	def on_payment_authorized(self, status=None, **kwargs):
		"""PSP webhook hook (live mode). Demo mode drives the same
		transition via frontdesk.api.payments.confirm_demo_payment.
		"""
		return True
