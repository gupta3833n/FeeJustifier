"""Helper utilities for FeeJustifier."""

import json
import os
from datetime import datetime


def load_json(filepath):
    """Load a JSON file and return its contents."""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def format_currency(amount, with_symbol=True):
    """Format a number as Indian currency (INR)."""
    if amount is None:
        return "N/A"
    amount = int(round(amount))
    s = str(amount)
    # Indian number system grouping: last 3 digits, then groups of 2
    if len(s) <= 3:
        formatted = s
    else:
        last3 = s[-3:]
        remaining = s[:-3]
        groups = []
        while remaining:
            groups.insert(0, remaining[-2:])
            remaining = remaining[:-2]
        formatted = ",".join(groups) + "," + last3

    return f"\u20b9{formatted}" if with_symbol else formatted


def format_currency_range(low, high):
    """Format a fee range."""
    return f"{format_currency(low)} \u2013 {format_currency(high)}"


def get_turnover_slab(turnover, slabs):
    """Determine the turnover slab for a given turnover amount."""
    for slab in slabs:
        max_val = slab.get("max")
        if max_val is None:
            return slab["id"]
        if turnover <= max_val:
            return slab["id"]
    return slabs[-1]["id"]


def get_city_tier(city, city_tiers):
    """Determine the tier of a city."""
    city_lower = city.strip().lower()
    for tier, cities in city_tiers.items():
        if any(c.lower() == city_lower for c in cities):
            return tier
    return "Tier-3"


def get_current_fy():
    """Get the current financial year string."""
    today = datetime.now()
    if today.month >= 4:
        return f"{today.year}-{str(today.year + 1)[-2:]}"
    else:
        return f"{today.year - 1}-{str(today.year)[-2:]}"


def get_proposal_number():
    """Generate a proposal reference number."""
    now = datetime.now()
    return f"FJ/{now.strftime('%Y%m%d')}/{now.strftime('%H%M%S')}"


def ordinal(n):
    """Return ordinal string for a number."""
    if 11 <= (n % 100) <= 13:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def format_date_formal(dt=None):
    """Format date in formal style: 30th March, 2026."""
    if dt is None:
        dt = datetime.now()
    day = ordinal(dt.day)
    return f"{day} {dt.strftime('%B')}, {dt.year}"
