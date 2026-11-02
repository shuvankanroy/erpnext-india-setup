# India Quickstart: One-Click Regional Automation for ERPNext

`india_quickstart` is a Frappe / ERPNext application designed to eliminate manual configuration, reduce setup complexity, and instantly make ERPNext compliant with Indian statutory and regional accounting practices.

---

## 📌 Why This Addon?

Starting ERPNext for an Indian business requires dozens of manual configuration steps across multiple modules:
- Localization (INR ₹, Indian number format Lakhs/Crores, Asia/Kolkata IST timezone).
- April 1 - March 31 Financial Year cycle.
- Setting up CGST, SGST, IGST tax ledgers under Chart of Accounts.
- In-state (CGST + SGST) and Out-of-state (IGST) sales & purchase tax templates.
- Income Tax TDS Categories (194C, 194J, 194I, 194H, 194Q) with statutory deduction thresholds.
- GST State codes (01 to 38, 97, 99) and GSTIN / PAN validation regex.
- Indian national & gazetted holiday calendars.
- Item HSN / SAC codes mapping.

**`india_quickstart` automates all of this into a single click.**

---

## 🚀 Key Features

1. **System & Currency Localization:**
   - Default Currency: **INR (₹)**
   - Number Format: **`#,##,###.##`** (Lakhs & Crores standard)
   - Date Format: **`dd-mm-yyyy`**
   - Time Zone: **`Asia/Kolkata`** (IST)

2. **Automated GST Ledgers & Tax Templates:**
   - Auto-creates child ledger accounts under Duties and Taxes:
     - `Input Tax CGST`, `Input Tax SGST`, `Input Tax IGST`
     - `Output Tax CGST`, `Output Tax SGST`, `Output Tax IGST`
     - `TDS Payable`
   - Configures default **Sales Taxes and Charges Templates** and **Purchase Taxes and Charges Templates**:
     - *Output GST In-State (CGST 9% + SGST 9%)*
     - *Output IGST Out-State (IGST 18%)*
     - *Input GST In-State (CGST 9% + SGST 9%)*
     - *Input IGST Out-State (IGST 18%)*

3. **Income Tax TDS Withholding Categories:**
   - Pre-seeds standard Indian Income Tax Act withholding categories:
     - **194C** (Contractors / Subcontractors - 1% Individual / 2% Others)
     - **194J** (Professional 10% / Technical Services 2%)
     - **194I** (Rent - Plant/Machinery 2%, Land/Building 10%)
     - **194H** (Commission / Brokerage 5%)
     - **194Q** (TDS on Purchase of Goods 0.1%)

4. **Compliance Custom Fields & Auto-derivation:**
   - Adds `gstin`, `pan_number`, `gst_state`, `gst_state_number` to **Company**, **Address**, **Customer**, and **Supplier**.
   - Adds `msme_type` and `msme_reg_no` (Udyam) to **Supplier** (critical for 45-day payment clause Section 43B(h)).
   - Adds `place_of_supply` and GSTIN references to **Sales Invoice** and **Purchase Invoice**.
   - Auto-extracts **PAN** (digits 3-12) and **GST State Code** (digits 1-2) whenever a 15-digit GSTIN is entered.

5. **HSN / SAC Code Master:**
   - New DocType `GST HSN SAC Code` with common pre-loaded IT, professional, hardware, logistics, and service codes.
   - Automatically links and autofills `gst_hsn_code` from Item Master to invoice items.

6. **Indian Fiscal Calendar & Holiday List:**
   - Auto-generates **1-April to 31-March** Fiscal Years for past, current, and upcoming years.
   - Seeds Indian Gazetted / National Public Holidays (Republic Day, Independence Day, Gandhi Jayanti, Diwali, Holi, etc.) with Sunday weekly off.

---

## 🛠️ Usage

### Via Frappe Desk UI
1. In Frappe Desk search bar, navigate to **India Quickstart Settings**.
2. Select your **Company** and **GST State** (or enter your **GSTIN**; state and PAN will auto-populate).
3. Check the desired modules (GST Ledgers, TDS Categories, HSN Codes, Holiday List).
4. Click **Execute India Quickstart Setup**.

### Via Bench Console / Python API
```python
from india_quickstart.setup_manager import run_india_quickstart_setup

run_india_quickstart_setup(
    company_name="Your Company Name",
    state="Maharashtra",
    gstin="27ABCDE1234F1Z5",
    create_taxes=True,
    create_tds=True,
    seed_hsn=True,
    create_holidays=True
)
```
