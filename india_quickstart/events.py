import frappe
from india_quickstart.validators import validate_gstin, validate_pan, extract_pan_from_gstin

def validate_address_gst(doc, method):
	if doc.gstin:
		doc.gstin = doc.gstin.strip().upper()
		validate_gstin(doc.gstin)
		if not doc.gst_state_number and len(doc.gstin) >= 2:
			doc.gst_state_number = doc.gstin[:2]

def validate_company_india(doc, method):
	if doc.country == "India":
		if doc.gstin:
			doc.gstin = doc.gstin.strip().upper()
			validate_gstin(doc.gstin)
			if not doc.pan_number:
				doc.pan_number = extract_pan_from_gstin(doc.gstin)
		if doc.pan_number:
			doc.pan_number = doc.pan_number.strip().upper()
			validate_pan(doc.pan_number)

def autofill_item_hsn(doc, method):
	"""
	When adding items to Sales or Purchase Invoice, autofill HSN from Item master if available
	"""
	for item in doc.get("items", []):
		if not item.gst_hsn_code and item.item_code:
			hsn = frappe.db.get_value("Item", item.item_code, "gst_hsn_code")
			if hsn:
				item.gst_hsn_code = hsn
