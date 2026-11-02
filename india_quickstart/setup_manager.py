import os
import json
import frappe
from frappe import _
from frappe.utils import getdate
from india_quickstart.validators import validate_gstin, validate_pan, extract_pan_from_gstin, extract_state_code_from_gstin
from india_quickstart.custom_fields import setup_custom_fields

def get_data_file_path(filename):
	return os.path.join(os.path.dirname(__file__), "data", filename)

def load_json_data(filename):
	with open(get_data_file_path(filename), "r") as f:
		return json.load(f)

def run_india_quickstart_setup(company_name, state=None, gstin=None, pan=None,
							   create_taxes=True, create_tds=True, seed_hsn=True, create_holidays=True):
	"""
	Complete Tally-style automated India setup for ERPNext.
	"""
	summary_messages = []

	if not frappe.db.exists("Company", company_name):
		frappe.throw(_("Company '{0}' does not exist.").format(company_name))

	# 1. Custom Fields (Statutory fields)
	setup_custom_fields()
	summary_messages.append("✓ Configured India Compliance Custom Fields (GSTIN, PAN, HSN/SAC, Place of Supply, MSME)")

	# 2. System Settings Localization
	frappe.db.set_single_value("System Settings", {
		"country": "India",
		"time_zone": "Asia/Kolkata",
		"currency": "INR",
		"number_format": "#,##,###.##",
		"date_format": "dd-mm-yyyy"
	})
	summary_messages.append("✓ System Settings localized (IST timezone Asia/Kolkata, INR ₹ currency, Indian Lakh/Crore numbering #,##,###.##, dd-mm-yyyy)")

	# 3. Accounts Settings (Tally-style Auto Row Rounding & Tax Determination)
	acc_settings = frappe.get_doc("Accounts Settings")
	acc_settings.determine_address_tax_category_from = "Billing Address"
	acc_settings.add_taxes_from_taxes_and_charges_template = 1
	acc_settings.add_taxes_from_item_tax_template = 0
	acc_settings.round_row_wise_tax = 1
	acc_settings.save(ignore_permissions=True)
	summary_messages.append("✓ Configured Tally-style Accounts Settings (Auto tax calculation, Row-wise rounding, Billing Address tax category)")

	# 4. Company Updates
	company = frappe.get_doc("Company", company_name)
	company.country = "India"
	company.default_currency = "INR"

	if gstin:
		gstin = gstin.strip().upper()
		validate_gstin(gstin)
		company.gstin = gstin
		if not pan:
			pan = extract_pan_from_gstin(gstin)
		if not state:
			state_code = extract_state_code_from_gstin(gstin)
			gst_states = load_json_data("gst_states.json")
			state = gst_states.get(state_code, "")

	if pan:
		pan = pan.strip().upper()
		validate_pan(pan)
		company.pan_number = pan

	if state:
		company.gst_state = state
		gst_states = load_json_data("gst_states.json")
		for code, s_name in gst_states.items():
			if s_name.lower() == state.lower() or code == state:
				company.gst_state_number = code
				company.gst_state = s_name
				state = s_name
				break

	# Create Round Off Ledger if missing and set as default
	round_off_acc = get_or_create_round_off_account(company_name)
	if round_off_acc and not company.round_off_account:
		company.round_off_account = round_off_acc

	company.save(ignore_permissions=True)
	summary_messages.append(f"✓ Company '{company_name}' updated with Country: India, Currency: INR, State: {state or 'N/A'}")

	# 5. Fiscal Year (Indian Financial Year: 1-Apr to 31-Mar)
	setup_fiscal_years(summary_messages)

	# 6. GST Ledger Accounts and Tax Templates
	if create_taxes:
		setup_gst_ledgers_and_templates(company_name, state, summary_messages)

	# 7. TDS Categories & Tax Withholding
	if create_tds:
		setup_tds_categories(company_name, summary_messages)

	# 8. Seed HSN / SAC Codes
	if seed_hsn:
		setup_hsn_sac_codes(summary_messages)

	# 9. Standard Indian Holiday List
	if create_holidays:
		setup_indian_holidays(company_name, summary_messages)

	# 10. GST Compliant Tax Invoice Print Format
	setup_gst_print_format(summary_messages)

	return summary_messages


def get_or_create_round_off_account(company_name):
	existing = frappe.db.get_value("Account", {"company": company_name, "account_name": "Round Off"}, "name")
	if existing:
		return existing
	parent_expense = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_name": ("like", "%Indirect Expenses%"), "is_group": 1},
		"name"
	)
	if not parent_expense:
		parent_expense = frappe.db.get_value(
			"Account",
			{"company": company_name, "root_type": "Expense", "is_group": 1},
			"name"
		)
	if parent_expense:
		acc = frappe.new_doc("Account")
		acc.account_name = "Round Off"
		acc.company = company_name
		acc.parent_account = parent_expense
		acc.account_type = "Round Off"
		acc.flags.ignore_permissions = True
		acc.insert()
		return acc.name
	return None


def setup_fiscal_years(summary_messages):
	today = getdate()
	year = today.year
	if today.month < 4:
		fy_start_year = year - 1
	else:
		fy_start_year = year

	for offset in range(-1, 3):
		start_y = fy_start_year + offset
		end_y = start_y + 1
		fy_name = f"{start_y}-{end_y}"
		start_date = f"{start_y}-04-01"
		end_date = f"{end_y}-03-31"

		if not frappe.db.exists("Fiscal Year", fy_name):
			fy = frappe.new_doc("Fiscal Year")
			fy.year = fy_name
			fy.year_start_date = start_date
			fy.year_end_date = end_date
			fy.flags.ignore_permissions = True
			fy.insert()

	summary_messages.append("✓ Indian Fiscal Years initialized (Apr 1 - Mar 31 cycles)")


def setup_gst_ledgers_and_templates(company_name, company_state, summary_messages):
	parent_duties = frappe.db.get_value(
		"Account",
		{"company": company_name, "account_type": "Tax", "is_group": 1},
		"name"
	)
	if not parent_duties:
		parent_duties = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_name": ("like", "%Duties and Taxes%"), "is_group": 1},
			"name"
		)
	if not parent_duties:
		parent_duties = frappe.db.get_value(
			"Account",
			{"company": company_name, "account_name": ("like", "%Current Liabilities%"), "is_group": 1},
			"name"
		)

	accounts_to_create = [
		("Output Tax CGST", parent_duties),
		("Output Tax SGST", parent_duties),
		("Output Tax IGST", parent_duties),
		("Input Tax CGST", parent_duties),
		("Input Tax SGST", parent_duties),
		("Input Tax IGST", parent_duties),
		("TDS Payable", parent_duties),
	]

	account_map = {}
	for acc_name, parent in accounts_to_create:
		existing = frappe.db.get_value("Account", {"company": company_name, "account_name": acc_name}, "name")
		if not existing and parent:
			acc = frappe.new_doc("Account")
			acc.account_name = acc_name
			acc.company = company_name
			acc.parent_account = parent
			acc.account_type = "Tax"
			acc.flags.ignore_permissions = True
			acc.insert()
			account_map[acc_name] = acc.name
		elif existing:
			account_map[acc_name] = existing

	# Sales & Purchase Taxes and Charges Templates
	sales_intra_title = "Output GST In-State (CGST 9% + SGST 9%)"
	sales_inter_title = "Output IGST Out-State (IGST 18%)"
	purch_intra_title = "Input GST In-State (CGST 9% + SGST 9%)"
	purch_inter_title = "Input IGST Out-State (IGST 18%)"

	s_intra_doc = create_sales_tax_template(company_name, sales_intra_title, [("Output Tax CGST", 9.0), ("Output Tax SGST", 9.0)], account_map)
	s_inter_doc = create_sales_tax_template(company_name, sales_inter_title, [("Output Tax IGST", 18.0)], account_map)
	p_intra_doc = create_purchase_tax_template(company_name, purch_intra_title, [("Input Tax CGST", 9.0), ("Input Tax SGST", 9.0)], account_map)
	p_inter_doc = create_purchase_tax_template(company_name, purch_inter_title, [("Input Tax IGST", 18.0)], account_map)

	# Item Tax Templates for Multi-Rate GST (5%, 12%, 18%, 28%)
	setup_item_tax_templates(company_name, account_map)

	# Tally-Style Smart Auto Tax Rules (Inter-State vs Intra-State auto switching!)
	if company_state:
		s_intra_name = s_intra_doc.name if s_intra_doc else frappe.db.get_value("Sales Taxes and Charges Template", {"title": sales_intra_title, "company": company_name}, "name")
		s_inter_name = s_inter_doc.name if s_inter_doc else frappe.db.get_value("Sales Taxes and Charges Template", {"title": sales_inter_title, "company": company_name}, "name")
		p_intra_name = p_intra_doc.name if p_intra_doc else frappe.db.get_value("Purchase Taxes and Charges Template", {"title": purch_intra_title, "company": company_name}, "name")
		p_inter_name = p_inter_doc.name if p_inter_doc else frappe.db.get_value("Purchase Taxes and Charges Template", {"title": purch_inter_title, "company": company_name}, "name")

		setup_tally_smart_tax_rules(company_name, company_state, s_intra_name, s_inter_name, p_intra_name, p_inter_name)

	summary_messages.append("✓ GST Accounts, Tax Templates (18%), Item Tax Slabs (5%, 12%, 18%, 28%) & Tally-Style Smart Tax Rules created")


def setup_item_tax_templates(company_name, account_map):
	slabs = [
		("GST 5%", [("Output Tax CGST", 2.5), ("Output Tax SGST", 2.5), ("Output Tax IGST", 5.0)]),
		("GST 12%", [("Output Tax CGST", 6.0), ("Output Tax SGST", 6.0), ("Output Tax IGST", 12.0)]),
		("GST 18%", [("Output Tax CGST", 9.0), ("Output Tax SGST", 9.0), ("Output Tax IGST", 18.0)]),
		("GST 28%", [("Output Tax CGST", 14.0), ("Output Tax SGST", 14.0), ("Output Tax IGST", 28.0)]),
		("GST 0% / Nil", [("Output Tax CGST", 0.0), ("Output Tax SGST", 0.0), ("Output Tax IGST", 0.0)])
	]

	for slab_title, tax_rates in slabs:
		template_name = f"{slab_title} - {company_name}"
		if not frappe.db.exists("Item Tax Template", template_name):
			itt = frappe.new_doc("Item Tax Template")
			itt.title = slab_title
			itt.company = company_name
			for acc_key, rate in tax_rates:
				acc = account_map.get(acc_key)
				if acc:
					itt.append("taxes", {
						"tax_type": acc,
						"tax_rate": rate
					})
			itt.flags.ignore_permissions = True
			itt.insert()


def setup_tally_smart_tax_rules(company_name, company_state, s_intra, s_inter, p_intra, p_inter):
	if s_intra and not frappe.db.exists("Tax Rule", {"company": company_name, "sales_tax_template": s_intra, "billing_state": company_state}):
		tr = frappe.new_doc("Tax Rule")
		tr.tax_type = "Sales"
		tr.sales_tax_template = s_intra
		tr.company = company_name
		tr.billing_state = company_state
		tr.priority = 10
		tr.flags.ignore_permissions = True
		tr.insert()

	if s_inter and not frappe.db.exists("Tax Rule", {"company": company_name, "sales_tax_template": s_inter, "billing_state": None}):
		tr = frappe.new_doc("Tax Rule")
		tr.tax_type = "Sales"
		tr.sales_tax_template = s_inter
		tr.company = company_name
		tr.priority = 1
		tr.flags.ignore_permissions = True
		tr.insert()

	if p_intra and not frappe.db.exists("Tax Rule", {"company": company_name, "purchase_tax_template": p_intra, "billing_state": company_state}):
		tr = frappe.new_doc("Tax Rule")
		tr.tax_type = "Purchase"
		tr.purchase_tax_template = p_intra
		tr.company = company_name
		tr.billing_state = company_state
		tr.priority = 10
		tr.flags.ignore_permissions = True
		tr.insert()

	if p_inter and not frappe.db.exists("Tax Rule", {"company": company_name, "purchase_tax_template": p_inter, "billing_state": None}):
		tr = frappe.new_doc("Tax Rule")
		tr.tax_type = "Purchase"
		tr.purchase_tax_template = p_inter
		tr.company = company_name
		tr.priority = 1
		tr.flags.ignore_permissions = True
		tr.insert()


def create_sales_tax_template(company_name, title, tax_rows, account_map):
	existing = frappe.db.get_value("Sales Taxes and Charges Template", {"title": title, "company": company_name}, "name")
	if existing:
		return frappe.get_doc("Sales Taxes and Charges Template", existing)

	template = frappe.new_doc("Sales Taxes and Charges Template")
	template.title = title
	template.company = company_name
	template.is_default = 1 if "In-State" in title else 0

	for acc_key, rate in tax_rows:
		acc = account_map.get(acc_key)
		if not acc:
			continue
		template.append("taxes", {
			"charge_type": "On Net Total",
			"account_head": acc,
			"description": acc_key,
			"rate": rate
		})

	if template.taxes:
		template.flags.ignore_permissions = True
		template.insert()
		return template
	return None


def create_purchase_tax_template(company_name, title, tax_rows, account_map):
	existing = frappe.db.get_value("Purchase Taxes and Charges Template", {"title": title, "company": company_name}, "name")
	if existing:
		return frappe.get_doc("Purchase Taxes and Charges Template", existing)

	template = frappe.new_doc("Purchase Taxes and Charges Template")
	template.title = title
	template.company = company_name
	template.is_default = 1 if "In-State" in title else 0

	for acc_key, rate in tax_rows:
		acc = account_map.get(acc_key)
		if not acc:
			continue
		template.append("taxes", {
			"charge_type": "On Net Total",
			"account_head": acc,
			"description": acc_key,
			"rate": rate,
			"category": "Total",
			"add_deduct_tax": "Add"
		})

	if template.taxes:
		template.flags.ignore_permissions = True
		template.insert()
		return template
	return None


def setup_tds_categories(company_name, summary_messages):
	tds_data = load_json_data("tds_categories.json")
	tds_acc = frappe.db.get_value("Account", {"company": company_name, "account_name": "TDS Payable"}, "name")

	for row in tds_data:
		cat_name = f"TDS - {row['section']} - {row['description'][:40]}"
		if not frappe.db.exists("Tax Withholding Category", cat_name):
			doc = frappe.new_doc("Tax Withholding Category")
			doc.name = cat_name
			doc.category_name = cat_name
			doc.flags.ignore_permissions = True

			if tds_acc:
				doc.append("accounts", {
					"company": company_name,
					"account": tds_acc
				})

			doc.append("rates", {
				"from_date": "2024-04-01",
				"to_date": "2030-03-31",
				"tax_withholding_rate": row["rate"],
				"single_threshold": row["threshold"],
				"cumulative_threshold": row["threshold"] * 2 if row["rate"] < 5 else row["threshold"]
			})
			doc.insert()

	summary_messages.append("✓ Standard TDS Categories seeded (194C Contractor, 194J Professional/Technical, 194I Rent, 194H Commission, 194Q)")


def setup_hsn_sac_codes(summary_messages):
	hsn_data = load_json_data("hsn_sac_codes.json")
	count = 0
	for row in hsn_data:
		if not frappe.db.exists("GST HSN SAC Code", row["hsn_code"]):
			doc = frappe.new_doc("GST HSN SAC Code")
			doc.hsn_code = row["hsn_code"]
			doc.description = row["description"]
			doc.gst_rate = row["gst_rate"]
			doc.flags.ignore_permissions = True
			doc.insert()
			count += 1
	summary_messages.append(f"✓ Seeded {count} common GST HSN/SAC codes (IT, Consulting, Hardware, Transport, etc.)")


def setup_indian_holidays(company_name, summary_messages):
	holiday_list_name = f"Indian National & Gazetted Holidays - {company_name}"
	if frappe.db.exists("Holiday List", holiday_list_name):
		return

	today = getdate()
	year = today.year
	start_date = f"{year}-01-01"
	end_date = f"{year}-12-31"

	holidays = [
		(f"{year}-01-26", "Republic Day"),
		(f"{year}-03-14", "Holi"),
		(f"{year}-04-14", "Dr. Ambedkar Jayanti"),
		(f"{year}-04-18", "Good Friday"),
		(f"{year}-05-12", "Buddha Purnima"),
		(f"{year}-08-15", "Independence Day"),
		(f"{year}-09-05", "Janmashtami"),
		(f"{year}-10-02", "Mahatma Gandhi Jayanti"),
		(f"{year}-10-20", "Dussehra"),
		(f"{year}-11-08", "Diwali (Deepavali)"),
		(f"{year}-11-24", "Guru Nanak Jayanti"),
		(f"{year}-12-25", "Christmas Day")
	]

	hl = frappe.new_doc("Holiday List")
	hl.holiday_list_name = holiday_list_name
	hl.from_date = start_date
	hl.to_date = end_date
	hl.weekly_off = "Sunday"
	hl.flags.ignore_permissions = True
	hl.get_weekly_off_dates()

	existing_dates = {str(d.holiday_date) for d in hl.holidays}
	for h_date, h_desc in holidays:
		if h_date not in existing_dates:
			hl.append("holidays", {
				"holiday_date": h_date,
				"description": h_desc
			})

	hl.insert()
	frappe.db.set_value("Company", company_name, "default_holiday_list", holiday_list_name)
	summary_messages.append(f"✓ Generated Indian Gazetted Holiday List ({year}) and set as default for {company_name}")


def setup_gst_print_format(summary_messages):
	pf_name = "Indian GST Compliant Tax Invoice"
	html_path = os.path.join(os.path.dirname(__file__), "india_quickstart", "print_format", "indian_gst_tax_invoice.html")
	if not os.path.exists(html_path):
		return

	with open(html_path, "r") as f:
		html_content = f.read()

	if not frappe.db.exists("Print Format", pf_name):
		pf = frappe.new_doc("Print Format")
		pf.name = pf_name
		pf.doc_type = "Sales Invoice"
		pf.module = "India Quickstart"
		pf.standard = "No"
		pf.custom_format = 1
		pf.html = html_content
		pf.flags.ignore_permissions = True
		pf.insert()
		summary_messages.append("✓ Created 'Indian GST Compliant Tax Invoice' Print Format with HSN table, CGST/SGST/IGST breakdown and Amount in Words")
	else:
		frappe.db.set_value("Print Format", pf_name, "html", html_content)
