"""Professional PDF proposal generator for FeeJustifier."""

import io
from datetime import datetime, timedelta
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, KeepTogether
)
from reportlab.pdfgen import canvas

from utils.helpers import format_currency, format_date_formal, get_proposal_number, get_current_fy


# Brand colors
NAVY = colors.HexColor("#1a5276")
DARK_BLUE = colors.HexColor("#2c3e50")
ACCENT_BLUE = colors.HexColor("#2980b9")
LIGHT_BLUE = colors.HexColor("#d6eaf8")
LIGHTER_BLUE = colors.HexColor("#eaf2f8")
LIGHT_GRAY = colors.HexColor("#f4f6f7")
MEDIUM_GRAY = colors.HexColor("#bdc3c7")
DARK_GRAY = colors.HexColor("#5d6d7e")
GREEN = colors.HexColor("#27ae60")
WHITE = colors.white


def _get_styles():
    """Create custom paragraph styles for the proposal."""
    styles = getSampleStyleSheet()

    styles.add(ParagraphStyle(
        name="DocTitle",
        parent=styles["Title"],
        fontSize=22,
        textColor=NAVY,
        spaceAfter=6,
        alignment=TA_CENTER,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="DocSubtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=DARK_GRAY,
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName="Helvetica",
    ))
    styles.add(ParagraphStyle(
        name="SectionHead",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=NAVY,
        spaceBefore=18,
        spaceAfter=8,
        fontName="Helvetica-Bold",
        borderWidth=0,
        borderPadding=0,
    ))
    styles.add(ParagraphStyle(
        name="SubSectionHead",
        parent=styles["Heading3"],
        fontSize=11,
        textColor=ACCENT_BLUE,
        spaceBefore=10,
        spaceAfter=4,
        fontName="Helvetica-Bold",
    ))
    styles.add(ParagraphStyle(
        name="BodyText2",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK_BLUE,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
        fontName="Helvetica",
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="BulletItem",
        parent=styles["Normal"],
        fontSize=10,
        textColor=DARK_BLUE,
        spaceAfter=3,
        leftIndent=20,
        bulletIndent=8,
        fontName="Helvetica",
        leading=14,
    ))
    styles.add(ParagraphStyle(
        name="SmallText",
        parent=styles["Normal"],
        fontSize=8,
        textColor=DARK_GRAY,
        spaceAfter=2,
        fontName="Helvetica",
        leading=10,
    ))
    styles.add(ParagraphStyle(
        name="FirmName",
        parent=styles["Normal"],
        fontSize=16,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
    ))
    styles.add(ParagraphStyle(
        name="FirmDetail",
        parent=styles["Normal"],
        fontSize=9,
        textColor=DARK_GRAY,
        fontName="Helvetica",
        alignment=TA_LEFT,
        leading=12,
    ))
    styles.add(ParagraphStyle(
        name="FeeAmount",
        parent=styles["Normal"],
        fontSize=18,
        textColor=NAVY,
        fontName="Helvetica-Bold",
        alignment=TA_CENTER,
        spaceAfter=4,
    ))
    styles.add(ParagraphStyle(
        name="FeeLabel",
        parent=styles["Normal"],
        fontSize=9,
        textColor=DARK_GRAY,
        fontName="Helvetica",
        alignment=TA_CENTER,
    ))

    return styles


class _HeaderFooter:
    """Handles header and footer drawing on each page."""

    def __init__(self, firm_info, proposal_ref):
        self.firm_info = firm_info
        self.proposal_ref = proposal_ref

    def __call__(self, canvas_obj, doc):
        canvas_obj.saveState()

        # Header line
        canvas_obj.setStrokeColor(NAVY)
        canvas_obj.setLineWidth(2)
        canvas_obj.line(40, A4[1] - 50, A4[0] - 40, A4[1] - 50)

        # Header text
        canvas_obj.setFont("Helvetica-Bold", 8)
        canvas_obj.setFillColor(NAVY)
        canvas_obj.drawString(40, A4[1] - 45, self.firm_info.get("firm_name", ""))

        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(DARK_GRAY)
        canvas_obj.drawRightString(A4[0] - 40, A4[1] - 45, f"Ref: {self.proposal_ref}")

        # Footer
        canvas_obj.setStrokeColor(MEDIUM_GRAY)
        canvas_obj.setLineWidth(0.5)
        canvas_obj.line(40, 45, A4[0] - 40, 45)

        canvas_obj.setFont("Helvetica", 7)
        canvas_obj.setFillColor(DARK_GRAY)
        canvas_obj.drawString(40, 32, "CONFIDENTIAL — This proposal is for the exclusive use of the addressee.")
        canvas_obj.drawRightString(A4[0] - 40, 32, f"Page {doc.page}")

        canvas_obj.restoreState()


def generate_proposal_pdf(proposal_data):
    """
    Generate a professional PDF proposal.

    Args:
        proposal_data: dict containing:
            - firm_info: dict with firm details
            - client_info: dict with client name, entity type, city, turnover
            - engagement: dict with key, name, category
            - template: dict with scope_of_work, deliverables, timeline, payment_terms
            - benchmark: dict from FeeEngine
            - final_fee: int, the fee to quote
            - custom_scope: list of str (optional overrides)
            - custom_deliverables: list of str (optional overrides)
            - custom_timeline: str (optional override)
            - custom_payment_terms: str (optional override)
            - additional_terms: list of str (optional)
            - validity_days: int (default 30)

    Returns:
        bytes: PDF file content
    """
    buffer = io.BytesIO()
    styles = _get_styles()

    proposal_ref = get_proposal_number()
    current_fy = get_current_fy()

    firm = proposal_data.get("firm_info", {})
    client = proposal_data.get("client_info", {})
    engagement = proposal_data.get("engagement", {})
    template = proposal_data.get("template", {})
    benchmark = proposal_data.get("benchmark", {})
    final_fee = proposal_data.get("final_fee", 0)
    validity_days = proposal_data.get("validity_days", 30)

    header_footer = _HeaderFooter(firm, proposal_ref)

    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=60,
        bottomMargin=60,
        title=f"Fee Proposal - {engagement.get('name', '')}",
        author=firm.get("firm_name", ""),
    )

    story = []

    # ── Cover section ──
    story.append(Spacer(1, 30))
    story.append(Paragraph(firm.get("firm_name", "Your Firm Name"), styles["FirmName"]))
    story.append(Spacer(1, 4))

    firm_details = []
    if firm.get("firm_address"):
        firm_details.append(firm["firm_address"].replace("\n", " | "))
    contact_parts = []
    if firm.get("firm_phone"):
        contact_parts.append(firm["firm_phone"])
    if firm.get("firm_email"):
        contact_parts.append(firm["firm_email"])
    if contact_parts:
        firm_details.append(" | ".join(contact_parts))
    if firm.get("firm_registration"):
        firm_details.append(firm["firm_registration"])

    for detail in firm_details:
        story.append(Paragraph(detail, styles["FirmDetail"]))

    story.append(Spacer(1, 20))
    story.append(HRFlowable(width="100%", thickness=2, color=NAVY))
    story.append(Spacer(1, 20))

    story.append(Paragraph("PROFESSIONAL FEE PROPOSAL", styles["DocTitle"]))
    story.append(Paragraph(engagement.get("name", ""), styles["DocSubtitle"]))

    # Proposal meta table
    today = datetime.now()
    valid_until = today + timedelta(days=validity_days)

    meta_data = [
        ["Proposal Reference", proposal_ref],
        ["Date", format_date_formal(today)],
        ["Financial Year", f"FY {current_fy}"],
        ["Valid Until", format_date_formal(valid_until)],
    ]
    meta_table = Table(meta_data, colWidths=[150, 300])
    meta_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), NAVY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK_BLUE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("ALIGN", (0, 0), (0, -1), "LEFT"),
        ("ALIGN", (1, 0), (1, -1), "LEFT"),
        ("LINEBELOW", (0, 0), (-1, -2), 0.5, LIGHT_BLUE),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 20))

    # ── Cover Letter (AI-generated) ──
    cover_letter = proposal_data.get("cover_letter")
    if cover_letter:
        story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
        story.append(Spacer(1, 10))
        story.append(Paragraph(cover_letter, styles["BodyText2"]))
        story.append(Spacer(1, 10))

    # ── Prepared For ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
    story.append(Spacer(1, 10))
    story.append(Paragraph("PREPARED FOR", styles["SectionHead"]))

    client_data = [
        ["Client Name", client.get("name", "—")],
        ["Entity Type", client.get("entity_type", "—")],
        ["City / Location", client.get("city", "—")],
    ]
    if client.get("turnover_display"):
        client_data.append(["Turnover (Approx.)", client["turnover_display"]])

    client_table = Table(client_data, colWidths=[150, 300])
    client_table.setStyle(TableStyle([
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (1, 0), (1, -1), "Helvetica"),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("TEXTCOLOR", (0, 0), (0, -1), DARK_GRAY),
        ("TEXTCOLOR", (1, 0), (1, -1), DARK_BLUE),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(client_table)
    story.append(Spacer(1, 15))

    # ── Scope of Work ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
    story.append(Paragraph("SCOPE OF WORK", styles["SectionHead"]))

    scope_items = proposal_data.get("custom_scope") or template.get("scope_of_work", [])
    for item in scope_items:
        story.append(Paragraph(f"\u2022  {item}", styles["BulletItem"]))

    story.append(Spacer(1, 10))

    # ── Deliverables ──
    story.append(Paragraph("DELIVERABLES", styles["SectionHead"]))

    deliverables = proposal_data.get("custom_deliverables") or template.get("deliverables", [])
    for item in deliverables:
        story.append(Paragraph(f"\u2022  {item}", styles["BulletItem"]))

    story.append(Spacer(1, 10))

    # ── Timeline ──
    story.append(Paragraph("TIMELINE", styles["SectionHead"]))
    timeline = proposal_data.get("custom_timeline") or template.get("timeline", "As mutually agreed")
    story.append(Paragraph(timeline, styles["BodyText2"]))
    story.append(Spacer(1, 10))

    # ── Fee Structure ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
    story.append(Paragraph("FEE STRUCTURE", styles["SectionHead"]))

    # Fee highlight box
    billing_basis = benchmark.get("billing_basis", "Per Engagement") if benchmark else "Per Engagement"
    fee_box_data = [[
        Paragraph(format_currency(final_fee), styles["FeeAmount"]),
    ], [
        Paragraph(f"Professional Fee \u2014 {billing_basis} (exclusive of applicable taxes)", styles["FeeLabel"]),
    ]]
    fee_box = Table(fee_box_data, colWidths=[450])
    fee_box.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), LIGHTER_BLUE),
        ("BOX", (0, 0), (-1, -1), 1, ACCENT_BLUE),
        ("TOPPADDING", (0, 0), (0, 0), 15),
        ("BOTTOMPADDING", (0, -1), (0, -1), 12),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
    ]))

    story.append(Spacer(1, 5))
    story.append(fee_box)
    story.append(Spacer(1, 12))

    # Market benchmark comparison
    if benchmark:
        story.append(Paragraph("Market Benchmark Comparison", styles["SubSectionHead"]))

        bench_data = [
            [
                Paragraph("<b>Parameter</b>", styles["SmallText"]),
                Paragraph("<b>Details</b>", styles["SmallText"]),
            ],
            [
                "Market Range",
                f"{format_currency(benchmark['market_low'])} \u2013 {format_currency(benchmark['market_high'])}",
            ],
            [
                "Turnover Slab",
                benchmark.get("turnover_slab_label", ""),
            ],
            [
                "City Tier",
                benchmark.get("city_tier", ""),
            ],
            [
                "Complexity Level",
                f"{benchmark.get('complexity', 'Medium')} (x{benchmark.get('complexity_multiplier', 1.0)})",
            ],
            [
                "Rate Basis",
                benchmark.get("billing_basis", "Per Engagement"),
            ],
            [
                "Your Fee Position",
                _fee_position_text(final_fee, benchmark["market_low"], benchmark["market_high"]),
            ],
        ]
        bench_table = Table(bench_data, colWidths=[150, 300])
        bench_table.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TEXTCOLOR", (0, 0), (-1, -1), DARK_BLUE),
            ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_GRAY]),
            ("BOX", (0, 0), (-1, -1), 0.5, MEDIUM_GRAY),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, MEDIUM_GRAY),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        story.append(bench_table)
        story.append(Spacer(1, 6))
        story.append(Paragraph(
            "<i>Note: Market benchmark ranges are indicative, based on ICAI guidelines and prevailing "
            "industry practice. They do not constitute official or binding rates.</i>",
            styles["SmallText"],
        ))

    story.append(Spacer(1, 10))

    # Fee notes
    if benchmark.get("note"):
        story.append(Paragraph(f"<b>Note:</b> {benchmark['note']}", styles["SmallText"]))
        story.append(Spacer(1, 6))

    story.append(Paragraph(
        "The above fee is exclusive of applicable Goods and Services Tax (GST) at 18%, "
        "out-of-pocket expenses (travel, stay, etc.), and any government fees, stamp duty, "
        "or statutory filing charges which shall be billed at actuals.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 10))

    # ── Fee Justification (AI-generated) ──
    fee_justification = proposal_data.get("fee_justification")
    if fee_justification:
        story.append(Paragraph("FEE JUSTIFICATION", styles["SubSectionHead"]))
        for line in fee_justification.strip().split("\n"):
            line = line.strip()
            if line:
                if line.startswith("\u2022 "):
                    line = line[2:]
                story.append(Paragraph(f"\u2022  {line}", styles["BulletItem"]))
        story.append(Spacer(1, 10))

    # ── Payment Terms ──
    story.append(Paragraph("PAYMENT TERMS", styles["SectionHead"]))
    payment_terms = proposal_data.get("custom_payment_terms") or template.get("payment_terms", "As mutually agreed")
    story.append(Paragraph(payment_terms, styles["BodyText2"]))
    story.append(Spacer(1, 10))

    # ── Terms & Conditions ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
    story.append(Paragraph("TERMS & CONDITIONS", styles["SectionHead"]))

    standard_terms = [
        "This proposal is valid for {validity} days from the date of issue.".format(validity=validity_days),
        "The engagement is subject to timely availability of information and records from the client.",
        "Any additional scope of work beyond what is specified above shall be charged separately after mutual agreement.",
        "The firm reserves the right to revise fees in case of material change in the nature or volume of work.",
        "All information shared during the course of this engagement shall be treated as confidential.",
        "Either party may terminate this engagement with 30 days written notice.",
        "Disputes, if any, shall be subject to the jurisdiction of the courts at the firm's location.",
    ]

    additional_terms = proposal_data.get("additional_terms", [])
    all_terms = standard_terms + additional_terms

    for i, term in enumerate(all_terms, 1):
        story.append(Paragraph(f"{i}. {term}", styles["BulletItem"]))

    story.append(Spacer(1, 20))

    # ── Acceptance ──
    story.append(HRFlowable(width="100%", thickness=0.5, color=MEDIUM_GRAY))
    story.append(Paragraph("ACCEPTANCE", styles["SectionHead"]))

    story.append(Paragraph(
        "We trust this proposal meets your requirements. We look forward to the opportunity "
        "to serve you and assure you of our best professional services at all times.",
        styles["BodyText2"],
    ))
    story.append(Spacer(1, 25))

    # Signature section
    sig_data = [
        [
            Paragraph("<b>For {}</b>".format(firm.get("firm_name", "The Firm")), styles["BodyText2"]),
            Paragraph("<b>Accepted By</b>", styles["BodyText2"]),
        ],
        ["", ""],
        ["", ""],
        [
            Paragraph("_________________________", styles["BodyText2"]),
            Paragraph("_________________________", styles["BodyText2"]),
        ],
        [
            Paragraph(firm.get("signatory_name", "Authorized Signatory"), styles["BodyText2"]),
            Paragraph("Name: ___________________", styles["BodyText2"]),
        ],
        [
            Paragraph(firm.get("signatory_designation", "Partner"), styles["SmallText"]),
            Paragraph("Designation: _____________", styles["SmallText"]),
        ],
        [
            Paragraph(firm.get("signatory_membership", ""), styles["SmallText"]),
            Paragraph("Date: ___________________", styles["SmallText"]),
        ],
    ]
    sig_table = Table(sig_data, colWidths=[225, 225])
    sig_table.setStyle(TableStyle([
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ]))
    story.append(sig_table)

    # Build PDF
    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)

    buffer.seek(0)
    return buffer.getvalue()


def _fee_position_text(fee, market_low, market_high):
    """Return a descriptive text for the fee position."""
    if market_high == market_low:
        return "At Market Rate"
    position = (fee - market_low) / (market_high - market_low)
    if position < 0:
        pct = abs(int(round((1 - fee / market_low) * 100)))
        return f"Below Market (approx. {pct}% below range)"
    elif position <= 0.25:
        return "Lower End of Market Range"
    elif position <= 0.5:
        return "Mid-Market Range"
    elif position <= 0.75:
        return "Above Average in Market Range"
    elif position <= 1.0:
        return "Premium End of Market Range"
    else:
        pct = int(round((fee / market_high - 1) * 100))
        return f"Above Market (approx. {pct}% above range)"
