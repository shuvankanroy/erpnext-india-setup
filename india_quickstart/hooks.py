app_name = "india_quickstart"
app_title = "India Quickstart"
app_publisher = "Ankan"
app_description = "One-click Automated India-specific Setup for ERPNext"
app_email = "ankan@example.com"
app_license = "mit"

required_apps = ["erpnext"]

after_install = "india_quickstart.custom_fields.setup_custom_fields"
after_migrate = "india_quickstart.custom_fields.setup_custom_fields"

doc_events = {
	"Address": {
		"validate": "india_quickstart.events.validate_address_gst"
	},
	"Company": {
		"validate": "india_quickstart.events.validate_company_india"
	},
	"Sales Invoice": {
		"validate": "india_quickstart.events.autofill_item_hsn"
	},
	"Purchase Invoice": {
		"validate": "india_quickstart.events.autofill_item_hsn"
	}
}
