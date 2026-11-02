import re
import frappe
from frappe import _

GSTIN_REGEX = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
PAN_REGEX = r"^[A-Z]{5}[0-9]{4}[A-Z]{1}$"

def validate_gstin(gstin):
	if not gstin:
		return True
	gstin = gstin.strip().upper()
	if not re.match(GSTIN_REGEX, gstin):
		frappe.throw(_("Invalid GSTIN format: '{0}'. GSTIN must be 15 characters (e.g. 27AAAAA0000A1Z5)").format(gstin))
	return True

def validate_pan(pan):
	if not pan:
		return True
	pan = pan.strip().upper()
	if not re.match(PAN_REGEX, pan):
		frappe.throw(_("Invalid PAN format: '{0}'. PAN must be 10 characters (e.g. AAAAA0000A)").format(pan))
	return True

def extract_pan_from_gstin(gstin):
	if gstin and len(gstin) >= 12:
		return gstin[2:12].upper()
	return ""

def extract_state_code_from_gstin(gstin):
	if gstin and len(gstin) >= 2:
		return gstin[:2]
	return ""
