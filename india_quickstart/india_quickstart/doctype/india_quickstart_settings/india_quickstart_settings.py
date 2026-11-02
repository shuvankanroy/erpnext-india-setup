import json
import frappe
from frappe.model.document import Document
from frappe import _
from india_quickstart.setup_manager import run_india_quickstart_setup, load_json_data
from india_quickstart.validators import extract_pan_from_gstin, extract_state_code_from_gstin

class IndiaQuickstartSettings(Document):
	@frappe.whitelist()
	def get_gst_states(self):
		return load_json_data("gst_states.json")

	@frappe.whitelist()
	def execute_setup(self):
		if not self.company:
			frappe.throw(_("Please select a target Company."))

		messages = run_india_quickstart_setup(
			company_name=self.company,
			state=self.state,
			gstin=self.gstin,
			pan=self.pan,
			create_taxes=self.create_tax_templates,
			create_tds=self.create_tds_categories,
			seed_hsn=self.create_standard_hsn,
			create_holidays=self.create_holidays
		)

		status_html = "<div style='background: #f0fdf4; border: 1px solid #86efac; padding: 15px; border-radius: 6px;'>"
		status_html += "<h4 style='color: #166534; margin-top: 0;'>Setup Completed Successfully!</h4><ul style='color: #15803d; margin-bottom: 0;'>"
		for m in messages:
			status_html += f"<li>{m}</li>"
		status_html += "</ul></div>"

		self.status_html = status_html
		self.save(ignore_permissions=True)
		return messages
