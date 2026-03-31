"""AI-powered enhancements using Gemini API for FeeJustifier."""

import google.generativeai as genai
from config import GEMINI_API_KEY as _ENV_KEY, GEMINI_MODEL
from utils.helpers import format_currency

# Module-level key that can be updated at runtime from the UI
GEMINI_API_KEY = _ENV_KEY


def is_ai_available():
    """Check if Gemini API key is configured (from env or UI input)."""
    try:
        import streamlit as st
        ui_key = st.session_state.get("gemini_api_key", "")
        if ui_key:
            return True
    except Exception:
        pass
    return bool(GEMINI_API_KEY and GEMINI_API_KEY.strip())


def _get_active_key():
    """Get the currently active API key (UI takes priority over env)."""
    try:
        import streamlit as st
        ui_key = st.session_state.get("gemini_api_key", "")
        if ui_key:
            return ui_key
    except Exception:
        pass
    return GEMINI_API_KEY


def _get_model():
    """Initialize and return the Gemini model."""
    key = _get_active_key()
    genai.configure(api_key=key)
    return genai.GenerativeModel(GEMINI_MODEL)


def generate_cover_letter(client_name, entity_type, engagement_name, city, fee, firm_name):
    """Generate a personalized cover letter paragraph for the proposal."""
    model = _get_model()
    prompt = f"""You are a senior Chartered Accountant in India writing a professional cover letter
for a fee proposal. Write a SHORT (3-4 sentences), warm yet professional opening paragraph.

Details:
- Firm: {firm_name}
- Client: {client_name} ({entity_type})
- Service: {engagement_name}
- City: {city}
- Proposed Fee: {format_currency(fee)}

Rules:
- Address the client by name
- Mention the specific service
- Express confidence in delivering value
- Keep it formal but warm, like a Big-4 engagement letter
- Do NOT mention the fee amount in the cover letter
- Do NOT use placeholder brackets like [Name] — use the actual details provided
- Return ONLY the paragraph text, nothing else"""

    response = model.generate_content(prompt)
    return response.text.strip()


def generate_fee_justification(engagement_name, fee, market_low, market_high, complexity,
                                entity_type, turnover_slab, city_tier):
    """Generate an AI-powered justification for the quoted fee."""
    model = _get_model()

    if market_high > market_low:
        position = (fee - market_low) / (market_high - market_low)
    else:
        position = 0.5

    prompt = f"""You are a senior Chartered Accountant in India. Write a SHORT fee justification
(3-4 bullet points) explaining why the quoted fee is reasonable and fair.

Details:
- Service: {engagement_name}
- Quoted Fee: {format_currency(fee)}
- Market Benchmark Range: {format_currency(market_low)} to {format_currency(market_high)}
- Fee is at {position*100:.0f}% of market range ({'below average' if position < 0.4 else 'mid-range' if position < 0.6 else 'above average' if position < 0.8 else 'premium'})
- Client Entity Type: {entity_type}
- Turnover Slab: {turnover_slab}
- City Tier: {city_tier}
- Complexity: {complexity}

Rules:
- Each bullet should be 1 sentence
- Reference the market benchmark range to show the fee is competitive
- Mention the value and expertise the CA brings
- If fee is above average, justify with quality/experience/complexity
- If fee is below average, position it as competitive/value-for-money
- Be specific to the engagement type, not generic
- Return ONLY the bullet points (use • symbol), nothing else"""

    response = model.generate_content(prompt)
    return response.text.strip()


def enhance_scope_of_work(scope_items, engagement_name, client_name, entity_type, complexity):
    """Enhance the scope of work with client-specific details using AI."""
    scope_text = "\n".join(f"- {item}" for item in scope_items)

    model = _get_model()
    prompt = f"""You are a senior Chartered Accountant in India. Enhance the following scope of work
to make it more specific and professional for this particular client.

Service: {engagement_name}
Client: {client_name} ({entity_type})
Complexity: {complexity}

Current scope items:
{scope_text}

Rules:
- Keep the same number of items (do not add or remove)
- Make each item slightly more detailed and client-specific
- Use professional language suitable for an engagement letter
- Keep each item to 1-2 lines maximum
- Do NOT change the fundamental meaning of any item
- Return ONLY the enhanced items, one per line, starting with a dash (-)
- No introductory text, headers, or explanations"""

    response = model.generate_content(prompt)
    lines = response.text.strip().split("\n")
    enhanced = []
    for line in lines:
        line = line.strip()
        if line.startswith("- "):
            line = line[2:]
        elif line.startswith("• "):
            line = line[2:]
        if line:
            enhanced.append(line)
    return enhanced if enhanced else scope_items
