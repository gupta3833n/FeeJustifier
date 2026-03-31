"""Configuration for FeeJustifier application."""

import os

# Application settings
APP_NAME = "FeeJustifier"
APP_TAGLINE = "CA Fee Benchmarking & Professional Proposal Generator"
APP_VERSION = "1.0.0"

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "data")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Data files
FEE_BENCHMARKS_FILE = os.path.join(DATA_DIR, "fee_benchmarks.json")
ENGAGEMENT_TEMPLATES_FILE = os.path.join(DATA_DIR, "engagement_templates.json")

# Gemini API
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
GEMINI_MODEL = "gemini-2.0-flash"

# PDF settings
PDF_FONT_DIR = os.path.join(BASE_DIR, "templates")
FIRM_DEFAULTS = {
    "firm_name": "Your Firm Name",
    "firm_address": "Your Address Line 1\nYour Address Line 2",
    "firm_phone": "+91-XXXXXXXXXX",
    "firm_email": "ca@yourfirm.com",
    "firm_website": "www.yourfirm.com",
    "firm_registration": "FRN: XXXXXXX",
    "signatory_name": "CA Your Name",
    "signatory_designation": "Partner",
    "signatory_membership": "M. No. XXXXXX",
}

# Engagement type to key mapping
ENGAGEMENT_DISPLAY_ORDER = [
    ("Audit & Assurance", [
        ("statutory_audit", "Statutory Audit"),
        ("tax_audit", "Tax Audit (Section 44AB)"),
        ("internal_audit", "Internal Audit"),
        ("bank_branch_audit", "Bank Branch Audit"),
    ]),
    ("Tax Compliance", [
        ("itr_individual", "ITR Filing — Individual"),
        ("itr_huf", "ITR Filing — HUF"),
        ("itr_partnership", "ITR Filing — Partnership / LLP"),
        ("itr_company", "ITR Filing — Company"),
        ("itr_trust", "ITR Filing — Trust / Society"),
        ("gst_monthly", "GST Return Filing — Monthly"),
        ("gst_quarterly", "GST Return Filing — Quarterly"),
        ("gst_annual", "GST Annual Return (GSTR-9/9C)"),
        ("tds_return", "TDS Return Filing"),
    ]),
    ("Registration & Setup", [
        ("company_incorporation", "Company Incorporation"),
        ("llp_registration", "LLP Registration"),
    ]),
    ("Corporate Compliance", [
        ("roc_annual_compliance", "ROC Annual Compliances"),
    ]),
    ("Accounting Services", [
        ("bookkeeping", "Bookkeeping & Accounting"),
    ]),
    ("Certification & Attestation", [
        ("certification", "Certification Work (Net Worth, Turnover, FEMA, etc.)"),
    ]),
    ("Advisory Services", [
        ("advisory_consulting", "Advisory / Consulting (Hourly Rate)"),
    ]),
]

# Theme colors
COLORS = {
    "primary": "#1a5276",
    "primary_light": "#2980b9",
    "secondary": "#2c3e50",
    "accent": "#3498db",
    "success": "#27ae60",
    "warning": "#f39c12",
    "background": "#f8f9fa",
    "surface": "#ffffff",
    "text_primary": "#2c3e50",
    "text_secondary": "#7f8c8d",
    "border": "#dee2e6",
}
