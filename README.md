# FeeJustifier — CA Fee Benchmarking & Professional Proposal Generator

**AICA (AI for CA) Level 2 Capstone Project**

FeeJustifier helps Chartered Accountants create professional fee proposals backed by market benchmark data. Select an engagement type, enter client details, review fee benchmarks, customize your proposal, and generate a Big-4 quality PDF engagement letter.

## Features

- **18 Engagement Types** covering Audit, Tax, GST, Company Registration, ROC Compliance, Bookkeeping, Certification, and Advisory
- **Fee Benchmarking** based on ICAI guidelines, regional council data, and industry practice — organized by turnover slab, city tier, entity type, and complexity level
- **Step-by-Step Wizard** — Select Service → Client Details → Review Benchmarks → Customize → Generate Proposal
- **Professional PDF Output** — Scope of Work, Deliverables, Timeline, Fee Structure with market comparison, Payment Terms, T&C, Acceptance block
- **Full Customization** — Override suggested fees, edit scope/deliverables/timeline, add custom terms
- **Demo Mode** — Works end-to-end without any API keys

## Quick Start

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Project Structure

```
FeeJustifier/
├── app.py                      # Main Streamlit application
├── config.py                   # App configuration and constants
├── fee_engine.py               # Fee benchmark calculation engine
├── proposal_generator.py       # PDF proposal generation (ReportLab)
├── data/
│   ├── fee_benchmarks.json     # Fee benchmark data (editable)
│   └── engagement_templates.json # Scope, deliverables, timelines per engagement
├── templates/                  # (Reserved for future PDF templates)
├── utils/
│   ├── __init__.py
│   └── helpers.py              # Utility functions
├── requirements.txt
└── README.md
```

## Engagement Types Covered

| Category | Engagements |
|----------|------------|
| Audit & Assurance | Statutory Audit, Tax Audit, Internal Audit, Bank Branch Audit |
| Tax Compliance | ITR (Individual, HUF, Partnership, Company, Trust), GST (Monthly, Quarterly, Annual), TDS Returns |
| Registration & Setup | Company Incorporation, LLP Registration |
| Corporate Compliance | ROC Annual Compliances |
| Accounting Services | Bookkeeping & Accounting |
| Certification | Net Worth, Turnover, FEMA Certificates |
| Advisory | Consulting (Hourly Rate) |

## Fee Benchmark Dimensions

- **Turnover Slabs:** Up to ₹40L | ₹40L–₹2Cr | ₹2Cr–₹10Cr | ₹10Cr–₹50Cr | ₹50Cr–₹250Cr | Above ₹250Cr
- **City Tiers:** Metro | Tier-1 | Tier-2 | Tier-3
- **Complexity:** Low (0.85x) | Medium (1.0x) | High (1.3x) | Very High (1.6x)

## Tech Stack

- Python + Streamlit
- ReportLab (PDF generation)
- Gemini API ready (placeholder for future AI-powered scope/fee suggestions)
