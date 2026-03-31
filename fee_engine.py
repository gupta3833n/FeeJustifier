"""Fee benchmarking engine for FeeJustifier."""

import os
from utils.helpers import load_json, get_turnover_slab, get_city_tier
from config import FEE_BENCHMARKS_FILE


class FeeEngine:
    """Engine for computing fee benchmarks based on engagement parameters."""

    def __init__(self):
        self.data = load_json(FEE_BENCHMARKS_FILE)
        self.engagements = self.data["engagements"]
        self.turnover_slabs = self.data["turnover_slabs"]
        self.city_tiers = self.data["city_tiers"]
        self.complexity_levels = self.data["complexity_levels"]
        self.entity_types = self.data["entity_types"]

    def get_engagement_list(self):
        """Return list of all engagement types."""
        return {k: v["name"] for k, v in self.engagements.items()}

    def get_applicable_entities(self, engagement_key):
        """Return applicable entity types for an engagement."""
        eng = self.engagements.get(engagement_key)
        if not eng:
            return self.entity_types
        return eng.get("applicable_entities", self.entity_types)

    def get_fee_benchmark(self, engagement_key, turnover, city, entity_type, complexity="Medium"):
        """
        Calculate fee benchmark for given parameters.

        Returns dict with:
            - market_low: lower end of market range
            - market_high: upper end of market range
            - suggested_fee: recommended fee (midpoint adjusted for complexity)
            - turnover_slab: which slab was matched
            - city_tier: which tier the city falls in
            - complexity_multiplier: multiplier applied
            - note: any special notes for this engagement type
        """
        eng = self.engagements.get(engagement_key)
        if not eng:
            return None

        # Determine slab and tier
        slab_id = get_turnover_slab(turnover, self.turnover_slabs)
        city_tier = get_city_tier(city, self.city_tiers) if city else "Tier-2"

        # Get base fee range
        fees = eng.get("fees", {})
        slab_fees = fees.get(slab_id, {})
        tier_fees = slab_fees.get(city_tier)

        if not tier_fees:
            # Fallback to Tier-3 if specific tier not found
            tier_fees = slab_fees.get("Tier-3", [0, 0])

        base_low, base_high = tier_fees

        # Apply complexity multiplier
        complexity_info = self.complexity_levels.get(complexity, self.complexity_levels["Medium"])
        multiplier = complexity_info["multiplier"]

        adjusted_low = int(round(base_low * multiplier))
        adjusted_high = int(round(base_high * multiplier))

        # Suggested fee is at 60th percentile of the adjusted range
        suggested = int(round(adjusted_low + (adjusted_high - adjusted_low) * 0.6))

        # Round to nearest 500 for cleaner numbers
        suggested = round(suggested / 500) * 500
        adjusted_low = round(adjusted_low / 500) * 500
        adjusted_high = round(adjusted_high / 500) * 500

        # Get slab label
        slab_label = ""
        for s in self.turnover_slabs:
            if s["id"] == slab_id:
                slab_label = s["label"]
                break

        return {
            "market_low": adjusted_low,
            "market_high": adjusted_high,
            "suggested_fee": suggested,
            "base_low": base_low,
            "base_high": base_high,
            "turnover_slab": slab_id,
            "turnover_slab_label": slab_label,
            "city_tier": city_tier,
            "complexity": complexity,
            "complexity_multiplier": multiplier,
            "engagement_name": eng["name"],
            "note": eng.get("note", ""),
            "category": eng.get("category", ""),
            "billing_basis": eng.get("billing_basis", "Per Engagement"),
        }

    def get_fee_position_label(self, fee, market_low, market_high):
        """Return a label for where the fee sits relative to the market range."""
        if market_high == market_low:
            return "At Market Rate"
        position = (fee - market_low) / (market_high - market_low)
        if position < 0:
            return "Below Market"
        elif position <= 0.25:
            return "Lower End"
        elif position <= 0.5:
            return "Mid-Market"
        elif position <= 0.75:
            return "Above Average"
        elif position <= 1.0:
            return "Premium"
        else:
            return "Above Market"

    def get_all_tiers(self):
        """Return list of city tier names."""
        return list(self.city_tiers.keys())

    def get_cities_for_tier(self, tier):
        """Return cities in a given tier."""
        return self.city_tiers.get(tier, [])

    def get_disclaimer(self):
        """Return the fee benchmark disclaimer."""
        return self.data["metadata"]["disclaimer"]
