"""FeeJustifier — CA Fee Benchmarking & Professional Proposal Generator."""

import streamlit as st
import json
import os

from config import (
    APP_NAME, APP_TAGLINE, APP_VERSION, COLORS,
    ENGAGEMENT_DISPLAY_ORDER, FIRM_DEFAULTS,
    FEE_BENCHMARKS_FILE, ENGAGEMENT_TEMPLATES_FILE,
)
from fee_engine import FeeEngine
from proposal_generator import generate_proposal_pdf
from ai_engine import is_ai_available, generate_cover_letter, generate_fee_justification, enhance_scope_of_work
from utils.helpers import (
    format_currency, format_currency_range, format_date_formal,
    get_proposal_number, get_current_fy, load_json,
)


# ── Page config ──
st.set_page_config(
    page_title=f"{APP_NAME} — {APP_TAGLINE}",
    page_icon="\U0001f4cb",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ── Custom CSS ──
st.markdown("""
<style>
    /* Global */
    .stApp {
        background-color: #f8f9fa;
    }
    .main .block-container {
        max-width: 1000px;
        padding-top: 2rem;
    }

    /* Header */
    .app-header {
        background: linear-gradient(135deg, #1a5276 0%, #2980b9 100%);
        color: white;
        padding: 1.8rem 2rem;
        border-radius: 12px;
        margin-bottom: 1.5rem;
        text-align: center;
    }
    .app-header h1 {
        margin: 0;
        font-size: 2rem;
        font-weight: 700;
        letter-spacing: 0.5px;
    }
    .app-header p {
        margin: 0.3rem 0 0 0;
        font-size: 1rem;
        opacity: 0.9;
    }

    /* Step indicator */
    .step-container {
        display: flex;
        justify-content: center;
        gap: 0;
        margin: 1.2rem 0 1.5rem 0;
    }
    .step-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .step-circle {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .step-active .step-circle {
        background: #2980b9;
        color: white;
    }
    .step-done .step-circle {
        background: #27ae60;
        color: white;
    }
    .step-pending .step-circle {
        background: #dee2e6;
        color: #7f8c8d;
    }
    .step-label {
        font-size: 0.82rem;
        font-weight: 600;
    }
    .step-active .step-label { color: #2980b9; }
    .step-done .step-label { color: #27ae60; }
    .step-pending .step-label { color: #7f8c8d; }
    .step-connector {
        width: 50px;
        height: 2px;
        background: #dee2e6;
        margin: 0 0.3rem;
        align-self: center;
    }
    .step-connector-done {
        background: #27ae60;
    }

    /* Cards */
    .info-card {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.3rem 1.5rem;
        margin-bottom: 1rem;
        box-shadow: 0 1px 3px rgba(0,0,0,0.04);
    }
    .info-card h3 {
        color: #1a5276;
        font-size: 1.1rem;
        margin: 0 0 0.5rem 0;
    }

    /* Fee highlight */
    .fee-highlight {
        background: linear-gradient(135deg, #eaf2f8 0%, #d6eaf8 100%);
        border: 2px solid #2980b9;
        border-radius: 12px;
        padding: 1.5rem;
        text-align: center;
        margin: 1rem 0;
    }
    .fee-highlight .amount {
        font-size: 2.2rem;
        font-weight: 700;
        color: #1a5276;
    }
    .fee-highlight .label {
        font-size: 0.85rem;
        color: #5d6d7e;
        margin-top: 0.2rem;
    }

    /* Benchmark bar */
    .bench-bar-container {
        background: #f4f6f7;
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin: 0.8rem 0;
    }
    .bench-bar {
        height: 12px;
        background: linear-gradient(90deg, #d5f5e3, #82e0aa, #f9e79f, #f5b041);
        border-radius: 6px;
        position: relative;
        margin: 0.5rem 0;
    }

    /* Metric cards */
    .metric-row {
        display: flex;
        gap: 1rem;
        margin: 0.8rem 0;
    }
    .metric-card {
        flex: 1;
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 8px;
        padding: 0.8rem 1rem;
        text-align: center;
    }
    .metric-card .value {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1a5276;
    }
    .metric-card .label {
        font-size: 0.75rem;
        color: #7f8c8d;
        margin-top: 0.1rem;
    }

    /* Engagement category */
    .engagement-category {
        color: #1a5276;
        font-weight: 700;
        font-size: 0.9rem;
        margin: 0.8rem 0 0.3rem 0;
        padding-bottom: 0.2rem;
        border-bottom: 2px solid #d6eaf8;
    }

    /* Preview section */
    .preview-section {
        background: white;
        border: 1px solid #dee2e6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .preview-section h4 {
        color: #1a5276;
        margin: 1rem 0 0.5rem 0;
    }
    .preview-section h4:first-child {
        margin-top: 0;
    }

    /* Buttons */
    .stButton > button {
        border-radius: 8px;
        font-weight: 600;
        padding: 0.5rem 2rem;
    }

    /* Disclaimer */
    .disclaimer {
        background: #fef9e7;
        border-left: 4px solid #f39c12;
        padding: 0.7rem 1rem;
        border-radius: 0 8px 8px 0;
        font-size: 0.82rem;
        color: #7d6608;
        margin: 0.8rem 0;
    }

    /* Demo badge */
    .demo-badge {
        background: #d4efdf;
        color: #1e8449;
        padding: 0.3rem 0.8rem;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 600;
        display: inline-block;
        margin-bottom: 0.5rem;
    }

    /* Hide Streamlit defaults */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)


# ── Init ──
@st.cache_resource
def get_fee_engine():
    return FeeEngine()

@st.cache_data
def get_templates():
    return load_json(ENGAGEMENT_TEMPLATES_FILE)

engine = get_fee_engine()
templates = get_templates()

# Session state defaults
defaults = {
    "step": 1,
    "engagement_key": None,
    "client_name": "",
    "entity_type": "",
    "city": "",
    "city_tier_override": None,
    "turnover": 0,
    "complexity": "Medium",
    "benchmark": None,
    "final_fee": 0,
    "custom_scope": None,
    "custom_deliverables": None,
    "custom_timeline": None,
    "custom_payment_terms": None,
    "additional_terms": [],
    "firm_info": dict(FIRM_DEFAULTS),
    "pdf_bytes": None,
    "fy": get_current_fy(),
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ── Header ──
st.markdown(f"""
<div class="app-header">
    <h1>\U0001f4cb {APP_NAME}</h1>
    <p>{APP_TAGLINE}</p>
</div>
""", unsafe_allow_html=True)

if is_ai_available():
    st.markdown('<div class="demo-badge" style="background:#d6eaf8; color:#1a5276;">\u2728 AI Mode — Gemini API Connected</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="demo-badge">\u2705 Demo Mode — Open sidebar to enter Gemini API Key for AI features</div>', unsafe_allow_html=True)


# ── Step indicator ──
def render_steps():
    step_names = ["Select Service", "Client Details", "Review & Customize", "Generate Proposal"]
    current = st.session_state.step

    html = '<div class="step-container">'
    for i, name in enumerate(step_names, 1):
        if i < current:
            cls = "step-done"
            icon = "\u2713"
        elif i == current:
            cls = "step-active"
            icon = str(i)
        else:
            cls = "step-pending"
            icon = str(i)

        html += f'<div class="step-item {cls}">'
        html += f'<div class="step-circle">{icon}</div>'
        html += f'<div class="step-label">{name}</div>'
        html += '</div>'

        if i < len(step_names):
            conn_cls = "step-connector-done" if i < current else ""
            html += f'<div class="step-connector {conn_cls}"></div>'

    html += '</div>'
    st.markdown(html, unsafe_allow_html=True)

render_steps()


# ────────────────────────────────────────
# STEP 1: Select Service
# ────────────────────────────────────────
if st.session_state.step == 1:
    st.markdown("### Select Engagement Type")
    st.markdown("Choose the professional service you want to create a fee proposal for.")

    selected = None
    for category_name, engagements in ENGAGEMENT_DISPLAY_ORDER:
        st.markdown(f'<div class="engagement-category">{category_name}</div>', unsafe_allow_html=True)
        cols = st.columns(2)
        for idx, (key, display_name) in enumerate(engagements):
            with cols[idx % 2]:
                if st.button(
                    display_name,
                    key=f"eng_{key}",
                    use_container_width=True,
                    type="secondary",
                ):
                    selected = key

    if selected:
        st.session_state.engagement_key = selected
        st.session_state.step = 2
        st.rerun()


# ────────────────────────────────────────
# STEP 2: Client Details
# ────────────────────────────────────────
elif st.session_state.step == 2:
    eng_key = st.session_state.engagement_key
    eng_data = engine.engagements[eng_key]

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("\u2190 Back", key="back_to_1"):
            st.session_state.step = 1
            st.rerun()
    with col_title:
        st.markdown(f"### {eng_data['name']}")

    st.markdown(f'<div class="disclaimer">Category: {eng_data.get("category", "")}'
                + (f' &mdash; {eng_data.get("note", "")}' if eng_data.get("note") else '')
                + f' &nbsp;|&nbsp; FY {st.session_state.get("fy", get_current_fy())}'
                + '</div>', unsafe_allow_html=True)

    st.markdown("#### Client Information")

    col1, col2 = st.columns(2)

    with col1:
        client_name = st.text_input(
            "Client / Business Name",
            value=st.session_state.client_name,
            placeholder="e.g., Sharma Trading Pvt. Ltd.",
        )

        applicable = engine.get_applicable_entities(eng_key)
        current_entity = st.session_state.entity_type if st.session_state.entity_type in applicable else applicable[0]
        entity_type = st.selectbox(
            "Entity Type",
            options=applicable,
            index=applicable.index(current_entity) if current_entity in applicable else 0,
        )

        complexity_options = list(engine.complexity_levels.keys())
        current_complexity = st.session_state.complexity if st.session_state.complexity in complexity_options else "Medium"
        complexity = st.selectbox(
            "Complexity Level",
            options=complexity_options,
            index=complexity_options.index(current_complexity),
            help=engine.complexity_levels[current_complexity]["description"],
        )

    with col2:
        city = st.text_input(
            "City / Location",
            value=st.session_state.city,
            placeholder="e.g., Mumbai, Jaipur, Udaipur",
        )

        # Show detected tier
        if city.strip():
            from utils.helpers import get_city_tier
            detected_tier = get_city_tier(city, engine.city_tiers)
            tier_options = engine.get_all_tiers()

            st.markdown(f"Detected City Tier: **{detected_tier}**")
            tier_override = st.selectbox(
                "Override City Tier (optional)",
                options=["Auto-detect"] + tier_options,
                index=0,
            )
            if tier_override != "Auto-detect":
                detected_tier = tier_override
        else:
            detected_tier = "Tier-2"

        # Turnover input
        is_advisory = eng_key == "advisory_consulting"
        if is_advisory:
            turnover_label = "Estimated Hours"
            turnover = st.number_input(
                turnover_label,
                min_value=1,
                max_value=10000,
                value=max(1, st.session_state.turnover) if st.session_state.turnover else 10,
                step=1,
                help="Estimated number of consulting hours",
            )
        else:
            turnover_label = "Annual Turnover / Revenue (in \u20b9)"
            turnover_presets = {
                "Up to \u20b940 Lakhs": 2000000,
                "\u20b940 Lakhs \u2013 \u20b92 Crore": 10000000,
                "\u20b92 Crore \u2013 \u20b910 Crore": 50000000,
                "\u20b910 Crore \u2013 \u20b950 Crore": 250000000,
                "\u20b950 Crore \u2013 \u20b9250 Crore": 1000000000,
                "Above \u20b9250 Crore": 5000000000,
            }
            turnover_choice = st.selectbox(
                "Turnover Range",
                options=list(turnover_presets.keys()),
            )
            turnover = turnover_presets[turnover_choice]

    st.markdown("---")

    # Firm info section (collapsible)
    with st.expander("Your Firm Details (for proposal letterhead)", expanded=False):
        firm = st.session_state.firm_info
        fc1, fc2 = st.columns(2)
        with fc1:
            firm["firm_name"] = st.text_input("Firm Name", value=firm["firm_name"])
            firm["firm_address"] = st.text_area("Firm Address", value=firm["firm_address"], height=68)
            firm["firm_phone"] = st.text_input("Phone", value=firm["firm_phone"])
            firm["firm_email"] = st.text_input("Email", value=firm["firm_email"])
        with fc2:
            firm["firm_website"] = st.text_input("Website", value=firm["firm_website"])
            firm["firm_registration"] = st.text_input("FRN / Registration No.", value=firm["firm_registration"])
            firm["signatory_name"] = st.text_input("Signatory Name", value=firm["signatory_name"])
            firm["signatory_designation"] = st.text_input("Designation", value=firm["signatory_designation"])
            firm["signatory_membership"] = st.text_input("Membership No.", value=firm["signatory_membership"])

    st.markdown("")
    col_prev, col_spacer, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u2190 Back", key="back_to_1b"):
            st.session_state.step = 1
            st.rerun()
    with col_next:
        if st.button("Review Benchmarks \u2192", type="primary", key="to_step3"):
            st.session_state.client_name = client_name
            st.session_state.entity_type = entity_type
            st.session_state.city = city
            st.session_state.turnover = turnover
            st.session_state.complexity = complexity
            st.session_state.firm_info = firm

            # Calculate benchmark
            benchmark = engine.get_fee_benchmark(
                eng_key, turnover, city, entity_type, complexity
            )

            if is_advisory and benchmark:
                # For advisory, multiply hourly rate by hours
                benchmark["market_low"] = benchmark["market_low"] * turnover
                benchmark["market_high"] = benchmark["market_high"] * turnover
                benchmark["suggested_fee"] = benchmark["suggested_fee"] * turnover
                benchmark["note"] = f"Based on {turnover} estimated hours. " + benchmark.get("note", "")

            st.session_state.benchmark = benchmark
            st.session_state.final_fee = benchmark["suggested_fee"] if benchmark else 0
            st.session_state.step = 3
            st.rerun()


# ────────────────────────────────────────
# STEP 3: Review & Customize
# ────────────────────────────────────────
elif st.session_state.step == 3:
    eng_key = st.session_state.engagement_key
    eng_data = engine.engagements[eng_key]
    benchmark = st.session_state.benchmark
    template = templates.get(eng_key, {})

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("\u2190 Back", key="back_to_2"):
            st.session_state.step = 2
            st.rerun()
    with col_title:
        st.markdown(f"### Review: {eng_data['name']}")

    if not benchmark:
        st.error("Could not calculate benchmark. Please go back and verify inputs.")
        st.stop()

    # Client summary
    st.markdown(f"""
    <div class="info-card">
        <h3>Client Summary</h3>
        <strong>{st.session_state.client_name or '(Client Name)'}</strong> &mdash;
        {st.session_state.entity_type} &mdash;
        {st.session_state.city or '(City)'} ({benchmark['city_tier']}) &mdash;
        Turnover Slab: {benchmark['turnover_slab_label']} &mdash;
        Complexity: {benchmark['complexity']}
    </div>
    """, unsafe_allow_html=True)

    # Fee benchmark display
    mkt_low = benchmark["market_low"]
    mkt_high = benchmark["market_high"]
    suggested = benchmark["suggested_fee"]
    billing_basis = benchmark.get("billing_basis", "Per Engagement")

    # Billing basis badge
    st.markdown(f"""
    <div style="text-align:center; margin:0.5rem 0 0.8rem 0;">
        <span style="background:#1a5276; color:white; padding:0.4rem 1.2rem; border-radius:20px;
        font-size:0.9rem; font-weight:700; letter-spacing:0.5px;">
        \U0001f4b0 Rates shown: {billing_basis}
        </span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="value">{format_currency(mkt_low)}</div>
            <div class="label">Market Low ({billing_basis})</div>
        </div>
        <div class="metric-card">
            <div class="value" style="color:#27ae60;">{format_currency(suggested)}</div>
            <div class="label">Suggested Fee ({billing_basis})</div>
        </div>
        <div class="metric-card">
            <div class="value">{format_currency(mkt_high)}</div>
            <div class="label">Market High ({billing_basis})</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Visual bar
    if mkt_high > mkt_low:
        suggested_pct = min(max((suggested - mkt_low) / (mkt_high - mkt_low) * 100, 0), 100)
    else:
        suggested_pct = 50

    st.markdown(f"""
    <div class="bench-bar-container">
        <div style="display:flex; justify-content:space-between; font-size:0.75rem; color:#7f8c8d;">
            <span>{format_currency(mkt_low)}</span>
            <span>Market Benchmark Range</span>
            <span>{format_currency(mkt_high)}</span>
        </div>
        <div class="bench-bar">
            <div style="position:absolute; left:{suggested_pct}%; top:-6px; transform:translateX(-50%);">
                <div style="width:3px; height:24px; background:#1a5276; margin:0 auto;"></div>
                <div style="font-size:0.7rem; color:#1a5276; font-weight:700; text-align:center; white-space:nowrap;">Suggested</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown(f"""
    <div class="disclaimer">
        {engine.get_disclaimer()}
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Fee customization ──
    st.markdown("#### Customize Your Fee")

    final_fee = st.number_input(
        f"Your Fee \u20b9 ({billing_basis})",
        min_value=0,
        value=int(st.session_state.final_fee),
        step=500,
        help=f"Override the suggested fee. Rate basis: {billing_basis}. The market benchmark range will be shown for reference.",
    )
    st.session_state.final_fee = final_fee

    # Position indicator
    position = engine.get_fee_position_label(final_fee, mkt_low, mkt_high)
    if "Below" in position:
        color = "#e74c3c"
    elif "Premium" in position or "Above" in position:
        color = "#f39c12"
    else:
        color = "#27ae60"
    st.markdown(f"Fee Position: <span style='color:{color}; font-weight:700;'>{position}</span>",
                unsafe_allow_html=True)

    # AI Fee Justification
    if is_ai_available():
        st.markdown("")
        if st.button("\u2728 AI: Generate Fee Justification", key="ai_justify"):
            with st.spinner("Generating AI-powered justification..."):
                try:
                    justification = generate_fee_justification(
                        eng_data["name"], final_fee, mkt_low, mkt_high,
                        benchmark["complexity"], st.session_state.entity_type,
                        benchmark["turnover_slab_label"], benchmark["city_tier"],
                    )
                    st.session_state["ai_justification"] = justification
                except Exception as e:
                    st.error(f"AI generation failed: {e}")

        if st.session_state.get("ai_justification"):
            st.markdown(f"""
            <div class="info-card">
                <h3>\u2728 AI Fee Justification</h3>
                <p style="font-size:0.9rem; color:#2c3e50; white-space:pre-line;">{st.session_state['ai_justification']}</p>
                <p style="font-size:0.75rem; color:#7f8c8d; margin-top:0.5rem;"><em>This justification will be included in your PDF proposal.</em></p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    # ── Scope customization ──
    st.markdown("#### Customize Proposal Content")

    with st.expander("Scope of Work", expanded=False):
        scope_items = template.get("scope_of_work", [])

        if is_ai_available():
            if st.button("\u2728 AI: Enhance Scope for this Client", key="ai_scope"):
                with st.spinner("Enhancing scope with AI..."):
                    try:
                        enhanced = enhance_scope_of_work(
                            scope_items, eng_data["name"],
                            st.session_state.client_name, st.session_state.entity_type,
                            st.session_state.complexity,
                        )
                        st.session_state["ai_enhanced_scope"] = enhanced
                    except Exception as e:
                        st.error(f"AI enhancement failed: {e}")

        display_scope = st.session_state.get("ai_enhanced_scope", scope_items)
        scope_text = st.text_area(
            "Edit scope items (one per line)",
            value="\n".join(display_scope),
            height=200,
            key="scope_edit",
        )
        custom_scope = [s.strip() for s in scope_text.strip().split("\n") if s.strip()]
        st.session_state.custom_scope = custom_scope if custom_scope != scope_items else None

    with st.expander("Deliverables", expanded=False):
        del_items = template.get("deliverables", [])
        del_text = st.text_area(
            "Edit deliverables (one per line)",
            value="\n".join(del_items),
            height=150,
            key="del_edit",
        )
        custom_del = [s.strip() for s in del_text.strip().split("\n") if s.strip()]
        st.session_state.custom_deliverables = custom_del if custom_del != del_items else None

    with st.expander("Timeline & Payment Terms", expanded=False):
        custom_timeline = st.text_input(
            "Timeline",
            value=template.get("timeline", "As mutually agreed"),
            key="timeline_edit",
        )
        st.session_state.custom_timeline = custom_timeline if custom_timeline != template.get("timeline") else None

        custom_payment = st.text_input(
            "Payment Terms",
            value=template.get("payment_terms", "As mutually agreed"),
            key="payment_edit",
        )
        st.session_state.custom_payment_terms = custom_payment if custom_payment != template.get("payment_terms") else None

    with st.expander("Additional Terms & Conditions", expanded=False):
        add_terms_text = st.text_area(
            "Add custom terms (one per line, these will be appended to standard terms)",
            value="\n".join(st.session_state.additional_terms),
            height=100,
            key="add_terms_edit",
        )
        st.session_state.additional_terms = [s.strip() for s in add_terms_text.strip().split("\n") if s.strip()]

    st.markdown("")
    col_prev, col_spacer, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("\u2190 Back", key="back_to_2b"):
            st.session_state.step = 2
            st.rerun()
    with col_next:
        if st.button("Preview & Generate \u2192", type="primary", key="to_step4"):
            st.session_state.step = 4
            st.rerun()


# ────────────────────────────────────────
# STEP 4: Preview & Generate
# ────────────────────────────────────────
elif st.session_state.step == 4:
    eng_key = st.session_state.engagement_key
    eng_data = engine.engagements[eng_key]
    benchmark = st.session_state.benchmark
    template = templates.get(eng_key, {})
    final_fee = st.session_state.final_fee
    firm = st.session_state.firm_info

    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("\u2190 Back", key="back_to_3"):
            st.session_state.step = 3
            st.rerun()
    with col_title:
        st.markdown(f"### Proposal Preview: {eng_data['name']}")

    # ── On-screen preview ──
    st.markdown(f"""
    <div class="preview-section">
        <div style="text-align:center; margin-bottom:1rem;">
            <div style="font-size:1.3rem; font-weight:700; color:#1a5276;">{firm.get('firm_name', '')}</div>
            <div style="font-size:0.8rem; color:#7f8c8d;">{firm.get('firm_address', '').replace(chr(10), ' | ')}</div>
            <div style="font-size:0.8rem; color:#7f8c8d;">{firm.get('firm_phone', '')} | {firm.get('firm_email', '')}</div>
        </div>
        <hr style="border:1px solid #1a5276;">
        <div style="text-align:center;">
            <div style="font-size:1.5rem; font-weight:700; color:#1a5276; margin:0.8rem 0 0.2rem 0;">PROFESSIONAL FEE PROPOSAL</div>
            <div style="font-size:1rem; color:#5d6d7e;">{eng_data['name']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Client info
    turnover_display = format_currency(st.session_state.turnover)
    if eng_key == "advisory_consulting":
        turnover_display = f"{st.session_state.turnover} hours (estimated)"

    st.markdown(f"""
    <div class="info-card">
        <h3>Prepared For</h3>
        <table style="width:100%; font-size:0.9rem;">
            <tr><td style="width:140px; color:#7f8c8d; padding:4px 0;"><strong>Client Name</strong></td><td>{st.session_state.client_name or '—'}</td></tr>
            <tr><td style="color:#7f8c8d; padding:4px 0;"><strong>Entity Type</strong></td><td>{st.session_state.entity_type}</td></tr>
            <tr><td style="color:#7f8c8d; padding:4px 0;"><strong>City</strong></td><td>{st.session_state.city or '—'}</td></tr>
            <tr><td style="color:#7f8c8d; padding:4px 0;"><strong>Turnover</strong></td><td>{turnover_display}</td></tr>
        </table>
    </div>
    """, unsafe_allow_html=True)

    # Scope
    scope = st.session_state.custom_scope or template.get("scope_of_work", [])
    scope_html = "".join(f"<li style='margin-bottom:4px;'>{item}</li>" for item in scope)
    st.markdown(f"""
    <div class="info-card">
        <h3>Scope of Work</h3>
        <ul style="font-size:0.9rem; color:#2c3e50; padding-left:1.2rem;">{scope_html}</ul>
    </div>
    """, unsafe_allow_html=True)

    # Deliverables
    deliverables = st.session_state.custom_deliverables or template.get("deliverables", [])
    del_html = "".join(f"<li style='margin-bottom:4px;'>{item}</li>" for item in deliverables)
    st.markdown(f"""
    <div class="info-card">
        <h3>Deliverables</h3>
        <ul style="font-size:0.9rem; color:#2c3e50; padding-left:1.2rem;">{del_html}</ul>
    </div>
    """, unsafe_allow_html=True)

    # Timeline
    timeline = st.session_state.custom_timeline or template.get("timeline", "As mutually agreed")
    st.markdown(f"""
    <div class="info-card">
        <h3>Timeline</h3>
        <p style="font-size:0.9rem; color:#2c3e50;">{timeline}</p>
    </div>
    """, unsafe_allow_html=True)

    # Fee
    billing_basis = benchmark.get("billing_basis", "Per Engagement")
    st.markdown(f"""
    <div class="fee-highlight">
        <div class="amount">{format_currency(final_fee)}</div>
        <div class="label">Professional Fee — {billing_basis} (exclusive of GST @ 18%)</div>
    </div>
    """, unsafe_allow_html=True)

    # Benchmark comparison
    if benchmark:
        st.markdown(f"""
        <div class="info-card">
            <h3>Market Benchmark Comparison</h3>
            <table style="width:100%; font-size:0.85rem;">
                <tr style="background:#eaf2f8;"><td style="padding:6px;"><strong>Market Range</strong></td><td style="padding:6px;">{format_currency_range(benchmark['market_low'], benchmark['market_high'])}</td></tr>
                <tr><td style="padding:6px;"><strong>Turnover Slab</strong></td><td style="padding:6px;">{benchmark['turnover_slab_label']}</td></tr>
                <tr style="background:#eaf2f8;"><td style="padding:6px;"><strong>City Tier</strong></td><td style="padding:6px;">{benchmark['city_tier']}</td></tr>
                <tr><td style="padding:6px;"><strong>Complexity</strong></td><td style="padding:6px;">{benchmark['complexity']} (x{benchmark['complexity_multiplier']})</td></tr>
                <tr style="background:#eaf2f8;"><td style="padding:6px;"><strong>Rate Basis</strong></td><td style="padding:6px; font-weight:700;">{benchmark.get('billing_basis', 'Per Engagement')}</td></tr>
            </table>
        </div>
        """, unsafe_allow_html=True)

    # Payment terms
    payment = st.session_state.custom_payment_terms or template.get("payment_terms", "As mutually agreed")
    st.markdown(f"""
    <div class="info-card">
        <h3>Payment Terms</h3>
        <p style="font-size:0.9rem; color:#2c3e50;">{payment}</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")

    # ── AI Cover Letter ──
    if is_ai_available():
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button("\u2728 AI: Generate Cover Letter", use_container_width=True, key="ai_cover"):
                with st.spinner("Writing personalized cover letter..."):
                    try:
                        cover = generate_cover_letter(
                            st.session_state.client_name or "the Client",
                            st.session_state.entity_type, eng_data["name"],
                            st.session_state.city, final_fee,
                            firm.get("firm_name", "Our Firm"),
                        )
                        st.session_state["ai_cover_letter"] = cover
                    except Exception as e:
                        st.error(f"AI generation failed: {e}")

        if st.session_state.get("ai_cover_letter"):
            st.markdown(f"""
            <div class="info-card">
                <h3>\u2728 AI Cover Letter</h3>
                <p style="font-size:0.9rem; color:#2c3e50; font-style:italic;">{st.session_state['ai_cover_letter']}</p>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("")

    # ── Generate PDF ──
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001f4c4 Generate PDF Proposal", type="primary", use_container_width=True, key="gen_pdf"):
            with st.spinner("Generating professional proposal..."):
                proposal_data = {
                    "firm_info": firm,
                    "client_info": {
                        "name": st.session_state.client_name,
                        "entity_type": st.session_state.entity_type,
                        "city": st.session_state.city,
                        "turnover_display": turnover_display,
                    },
                    "engagement": {
                        "key": eng_key,
                        "name": eng_data["name"],
                        "category": eng_data.get("category", ""),
                    },
                    "template": template,
                    "benchmark": benchmark,
                    "final_fee": final_fee,
                    "custom_scope": st.session_state.custom_scope,
                    "custom_deliverables": st.session_state.custom_deliverables,
                    "custom_timeline": st.session_state.custom_timeline,
                    "custom_payment_terms": st.session_state.custom_payment_terms,
                    "additional_terms": st.session_state.additional_terms,
                    "validity_days": 30,
                    "financial_year": st.session_state.get("fy", get_current_fy()),
                    "cover_letter": st.session_state.get("ai_cover_letter"),
                    "fee_justification": st.session_state.get("ai_justification"),
                }

                pdf_bytes = generate_proposal_pdf(proposal_data)
                st.session_state.pdf_bytes = pdf_bytes

            st.success("Proposal generated successfully!")

    if st.session_state.pdf_bytes:
        st.markdown("")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            safe_client = (st.session_state.client_name or "Client").replace(" ", "_")
            safe_eng = eng_data["name"].replace(" ", "_").replace("/", "-")
            filename = f"Fee_Proposal_{safe_client}_{safe_eng}.pdf"

            st.download_button(
                label="\u2b07\ufe0f Download PDF Proposal",
                data=st.session_state.pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True,
            )

    # ── Share Proposal ──
    if st.session_state.pdf_bytes:
        st.markdown("---")
        st.markdown("### Share Proposal")

        share_tab_email, share_tab_whatsapp = st.tabs(["\u2709\ufe0f Email to Client", "\U0001f4f1 WhatsApp"])

        with share_tab_email:
            email_configured = st.session_state.get("email_sender") and st.session_state.get("email_password")

            if not email_configured:
                st.info("Configure your email credentials in the sidebar (Email Settings) to send proposals directly.")
            else:
                ec1, ec2 = st.columns(2)
                with ec1:
                    recipient_email = st.text_input(
                        "Client's Email Address",
                        placeholder="client@company.com",
                        key="recipient_email",
                    )
                    cc_email = st.text_input(
                        "CC (optional)",
                        placeholder="partner@yourfirm.com",
                        key="cc_email",
                    )
                with ec2:
                    email_subject = st.text_input(
                        "Subject",
                        value=f"Fee Proposal — {eng_data['name']} | {firm.get('firm_name', '')}",
                        key="email_subject",
                    )

                default_body = (
                    f"Dear Sir/Madam,\n\n"
                    f"Thank you for the opportunity to present our professional fee proposal for "
                    f"{eng_data['name']} services.\n\n"
                    f"Please find attached our detailed fee proposal for your kind review and consideration. "
                    f"The proposal includes the scope of work, deliverables, timeline, fee structure with "
                    f"market benchmark comparison, and terms & conditions.\n\n"
                    f"We would be happy to discuss the proposal at your convenience and address any "
                    f"queries you may have.\n\n"
                    f"Looking forward to your positive response.\n\n"
                    f"Warm regards,\n"
                    f"{firm.get('signatory_name', 'CA')}\n"
                    f"{firm.get('signatory_designation', '')}\n"
                    f"{firm.get('firm_name', '')}\n"
                    f"{firm.get('firm_phone', '')} | {firm.get('firm_email', '')}"
                )
                email_body = st.text_area(
                    "Email Body",
                    value=default_body,
                    height=220,
                    key="email_body",
                )

                if st.button("\u2709\ufe0f Send Proposal via Email", type="primary", use_container_width=True, key="send_email"):
                    if not recipient_email or not recipient_email.strip():
                        st.error("Please enter the client's email address.")
                    else:
                        with st.spinner("Sending email..."):
                            try:
                                import smtplib
                                from email.mime.multipart import MIMEMultipart
                                from email.mime.text import MIMEText
                                from email.mime.application import MIMEApplication

                                msg = MIMEMultipart()
                                msg["From"] = st.session_state["email_sender"]
                                msg["To"] = recipient_email.strip()
                                if cc_email and cc_email.strip():
                                    msg["Cc"] = cc_email.strip()
                                msg["Subject"] = email_subject

                                msg.attach(MIMEText(email_body, "plain"))

                                pdf_attachment = MIMEApplication(st.session_state.pdf_bytes, _subtype="pdf")
                                pdf_attachment.add_header(
                                    "Content-Disposition", "attachment",
                                    filename=filename,
                                )
                                msg.attach(pdf_attachment)

                                recipients = [recipient_email.strip()]
                                if cc_email and cc_email.strip():
                                    recipients.append(cc_email.strip())

                                with smtplib.SMTP(st.session_state["email_smtp"], st.session_state["email_port"]) as server:
                                    server.starttls()
                                    server.login(st.session_state["email_sender"], st.session_state["email_password"])
                                    server.sendmail(st.session_state["email_sender"], recipients, msg.as_string())

                                st.success(f"Proposal sent successfully to {recipient_email}!")
                                st.balloons()
                            except smtplib.SMTPAuthenticationError:
                                st.error("Authentication failed. Please check your email and App Password in the sidebar. For Gmail, you need an App Password (not your regular password).")
                            except Exception as e:
                                st.error(f"Failed to send email: {e}")

        with share_tab_whatsapp:
            wa_phone = st.text_input(
                "Client's WhatsApp Number (with country code)",
                placeholder="919876543210",
                key="wa_phone",
                help="Enter number without + or spaces. Example: 919876543210 for India",
            )

            wa_message = st.text_area(
                "WhatsApp Message",
                value=(
                    f"Dear Sir/Madam,\n\n"
                    f"Please find our professional fee proposal for *{eng_data['name']}* services.\n\n"
                    f"*Proposed Fee:* {format_currency(final_fee)} (exclusive of GST)\n"
                    f"*Service:* {eng_data['name']}\n\n"
                    f"We have also emailed the detailed PDF proposal. "
                    f"Please review at your convenience.\n\n"
                    f"Regards,\n"
                    f"{firm.get('signatory_name', 'CA')}\n"
                    f"{firm.get('firm_name', '')}"
                ),
                height=180,
                key="wa_message",
            )

            if wa_phone:
                import urllib.parse
                wa_encoded = urllib.parse.quote(wa_message)
                wa_link = f"https://wa.me/{wa_phone.strip()}?text={wa_encoded}"
                st.markdown(
                    f'<a href="{wa_link}" target="_blank" style="display:inline-block; width:100%; '
                    f'text-align:center; background:#25D366; color:white; padding:0.6rem 1.5rem; '
                    f'border-radius:8px; text-decoration:none; font-weight:600; font-size:0.95rem;">'
                    f'\U0001f4f1 Open WhatsApp & Send Message</a>',
                    unsafe_allow_html=True,
                )
                st.markdown("")
                st.caption("This will open WhatsApp with the pre-filled message. You can then attach the downloaded PDF manually in the chat.")
            else:
                st.info("Enter the client's WhatsApp number to generate a shareable link.")

    st.markdown("")

    # Start over
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("\U0001f504 Create New Proposal", use_container_width=True, key="restart"):
            for k, v in defaults.items():
                st.session_state[k] = v
            st.rerun()


# ── Sidebar ──
with st.sidebar:
    st.markdown(f"### {APP_NAME}")
    st.markdown(f"*{APP_TAGLINE}*")
    st.markdown("---")

    # AI Settings
    st.markdown("#### \u2728 AI Settings")
    gemini_key_input = st.text_input(
        "Gemini API Key",
        value=st.session_state.get("gemini_api_key", ""),
        type="password",
        placeholder="Paste your Gemini API key here",
        help="Your key is never stored. Get a free key at ai.google.dev",
    )
    if gemini_key_input:
        st.session_state["gemini_api_key"] = gemini_key_input
        import ai_engine
        import google.generativeai as genai
        ai_engine.GEMINI_API_KEY = gemini_key_input
        genai.configure(api_key=gemini_key_input)
        st.markdown(
            '<div style="background:#d4efdf; color:#1e8449; padding:0.4rem 0.8rem; '
            'border-radius:6px; font-size:0.8rem; font-weight:600;">'
            '\u2705 AI Connected — Gemini features enabled</div>',
            unsafe_allow_html=True,
        )
    else:
        st.session_state["gemini_api_key"] = ""
        st.markdown(
            '<div style="background:#fef9e7; color:#7d6608; padding:0.4rem 0.8rem; '
            'border-radius:6px; font-size:0.78rem;">'
            'No API key = Demo mode (all features work except AI).<br>'
            'Your key is never stored. Get a free key at <b>ai.google.dev</b></div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Email Settings
    st.markdown("#### \u2709\ufe0f Email Settings")
    st.markdown(
        '<div style="font-size:0.78rem; color:#5d6d7e; margin-bottom:0.5rem;">'
        'Configure to send proposals directly to clients via email.</div>',
        unsafe_allow_html=True,
    )
    email_sender = st.text_input("Your Email", value=st.session_state.get("email_sender", ""), placeholder="ca@yourfirm.com", key="sb_email")
    email_password = st.text_input("App Password", value=st.session_state.get("email_password", ""), type="password", placeholder="Gmail App Password", key="sb_email_pw",
                                    help="For Gmail: Go to myaccount.google.com > Security > 2-Step Verification > App passwords. Generate one for 'Mail'.")
    email_smtp = st.text_input("SMTP Server", value=st.session_state.get("email_smtp", "smtp.gmail.com"), key="sb_smtp")
    email_port = st.number_input("SMTP Port", value=int(st.session_state.get("email_port", 587)), min_value=1, max_value=65535, key="sb_port")
    st.session_state["email_sender"] = email_sender
    st.session_state["email_password"] = email_password
    st.session_state["email_smtp"] = email_smtp
    st.session_state["email_port"] = int(email_port)

    if email_sender and email_password:
        st.markdown(
            '<div style="background:#d4efdf; color:#1e8449; padding:0.4rem 0.8rem; '
            'border-radius:6px; font-size:0.8rem; font-weight:600;">'
            '\u2705 Email configured</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")
    st.markdown(f"**Version:** {APP_VERSION}")
    fy_options = [get_current_fy()]
    # Ensure FY 2026-27 and 2025-26 are available
    for fy in ["2026-27", "2025-26"]:
        if fy not in fy_options:
            fy_options.append(fy)
    fy_options = sorted(set(fy_options), reverse=True)
    selected_fy = st.selectbox("Financial Year", options=fy_options, index=0, key="selected_fy")
    st.session_state["fy"] = selected_fy
    st.markdown("---")

    st.markdown("#### About")
    st.markdown(
        "FeeJustifier helps Chartered Accountants create professional "
        "fee proposals backed by market benchmark data. Select an engagement "
        "type, enter client details, and generate a Big-4 quality proposal PDF."
    )

    st.markdown("---")
    st.markdown("#### AI Features")
    st.markdown(
        "With Gemini API key:\n"
        "- \u2728 AI Fee Justification\n"
        "- \u2728 AI Scope Enhancement\n"
        "- \u2728 AI Cover Letter\n\n"
        "All AI content is included in the PDF."
    )

    st.markdown("---")
    st.markdown("#### Data Sources")
    st.markdown(
        "Fee benchmarks are based on:\n"
        "- ICAI Suggested Minimum Fees\n"
        "- Regional Council Guidelines\n"
        "- Industry Practice Surveys\n\n"
        "*Ranges are indicative and not official rates.*"
    )

    st.markdown("---")
    st.markdown(
        "<div style='font-size:0.75rem; color:#7f8c8d;'>"
        "FeeJustifier &mdash; Professional Fee Benchmarking for CAs<br>"
        "Powered by ICAI Guidelines &amp; Industry Data"
        "</div>",
        unsafe_allow_html=True,
    )
