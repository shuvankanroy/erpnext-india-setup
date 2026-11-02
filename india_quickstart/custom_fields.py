import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_fields

def setup_custom_fields():
	"""
	Sets up GSTIN, GST Category, GST State, PAN, HSN codes across core ERPNext DocTypes.
	"""
	custom_fields = {
		"Company": [
			{
				"fieldname": "india_section",
				"label": "India Statutory Details",
				"fieldtype": "Section Break",
				"insert_after": "default_currency"
			},
			{
				"fieldname": "gstin",
				"label": "GSTIN",
				"fieldtype": "Data",
				"insert_after": "india_section"
			},
			{
				"fieldname": "pan_number",
				"label": "PAN",
				"fieldtype": "Data",
				"insert_after": "gstin"
			},
			{
				"fieldname": "gst_state",
				"label": "GST State",
				"fieldtype": "Data",
				"insert_after": "pan_number"
			},
			{
				"fieldname": "gst_state_number",
				"label": "GST State Code",
				"fieldtype": "Data",
				"insert_after": "gst_state"
			}
		],
		"Address": [
			{
				"fieldname": "india_gst_section",
				"label": "GST Compliance",
				"fieldtype": "Section Break",
				"insert_after": "country"
			},
			{
				"fieldname": "gstin",
				"label": "GSTIN",
				"fieldtype": "Data",
				"insert_after": "india_gst_section"
			},
			{
				"fieldname": "gst_state",
				"label": "GST State",
				"fieldtype": "Data",
				"insert_after": "gstin"
			},
			{
				"fieldname": "gst_state_number",
				"label": "GST State Code",
				"fieldtype": "Data",
				"insert_after": "gst_state"
			},
			{
				"fieldname": "gst_category",
				"label": "GST Category",
				"fieldtype": "Select",
				"options": "Registered Regular\nRegistered Composition\nUnregistered\nSEZ\nOverseas\nDeemed Export\nUIN Holders",
				"default": "Registered Regular",
				"insert_after": "gst_state_number"
			}
		],
		"Customer": [
			{
				"fieldname": "pan_number",
				"label": "PAN",
				"fieldtype": "Data",
				"insert_after": "customer_type"
			},
			{
				"fieldname": "gstin",
				"label": "Primary GSTIN",
				"fieldtype": "Data",
				"insert_after": "pan_number"
			},
			{
				"fieldname": "gst_category",
				"label": "GST Category",
				"fieldtype": "Select",
				"options": "Registered Regular\nRegistered Composition\nUnregistered\nSEZ\nOverseas\nDeemed Export\nUIN Holders",
				"default": "Registered Regular",
				"insert_after": "gstin"
			}
		],
		"Supplier": [
			{
				"fieldname": "pan_number",
				"label": "PAN",
				"fieldtype": "Data",
				"insert_after": "supplier_type"
			},
			{
				"fieldname": "gstin",
				"label": "Primary GSTIN",
				"fieldtype": "Data",
				"insert_after": "pan_number"
			},
			{
				"fieldname": "gst_category",
				"label": "GST Category",
				"fieldtype": "Select",
				"options": "Registered Regular\nRegistered Composition\nUnregistered\nSEZ\nOverseas\nDeemed Export\nUIN Holders",
				"default": "Registered Regular",
				"insert_after": "gstin"
			},
			{
				"fieldname": "msme_type",
				"label": "MSME Category",
				"fieldtype": "Select",
				"options": "\nMicro\nSmall\nMedium\nNon-MSME",
				"insert_after": "gst_category"
			},
			{
				"fieldname": "msme_reg_no",
				"label": "Udyam / MSME Registration No",
				"fieldtype": "Data",
				"insert_after": "msme_type",
				"depends_on": "eval:doc.msme_type && doc.msme_type != 'Non-MSME'"
			}
		],
		"Item": [
			{
				"fieldname": "gst_hsn_code",
				"label": "HSN / SAC Code",
				"fieldtype": "Link",
				"options": "GST HSN SAC Code",
				"insert_after": "item_code"
			}
		],
		"Sales Invoice Item": [
			{
				"fieldname": "gst_hsn_code",
				"label": "HSN / SAC Code",
				"fieldtype": "Data",
				"insert_after": "item_code"
			}
		],
		"Purchase Invoice Item": [
			{
				"fieldname": "gst_hsn_code",
				"label": "HSN / SAC Code",
				"fieldtype": "Data",
				"insert_after": "item_code"
			}
		],
		"Sales Invoice": [
			{
				"fieldname": "place_of_supply",
				"label": "Place of Supply (State)",
				"fieldtype": "Data",
				"insert_after": "customer_address"
			},
			{
				"fieldname": "company_gstin",
				"label": "Company GSTIN",
				"fieldtype": "Data",
				"insert_after": "company_address"
			},
			{
				"fieldname": "customer_gstin",
				"label": "Customer GSTIN",
				"fieldtype": "Data",
				"insert_after": "place_of_supply"
			}
		],
		"Purchase Invoice": [
			{
				"fieldname": "place_of_supply",
				"label": "Place of Supply (State)",
				"fieldtype": "Data",
				"insert_after": "billing_address"
			},
			{
				"fieldname": "company_gstin",
				"label": "Company GSTIN",
				"fieldtype": "Data",
				"insert_after": "shipping_address"
			},
			{
				"fieldname": "supplier_gstin",
				"label": "Supplier GSTIN",
				"fieldtype": "Data",
				"insert_after": "place_of_supply"
			}
		]
	}

	create_custom_fields(custom_fields, ignore_validate=True)
