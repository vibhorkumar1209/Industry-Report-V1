from __future__ import annotations

from statistics import median


class CrossValidationAgent:
    def run(self, insights: list[dict]) -> dict:
        market_sizes = [i["market_size_usd_billion"] for i in insights if i.get("market_size_usd_billion")]
        cagrs = [i["cagr_percent"] for i in insights if i.get("cagr_percent")]

        consensus_market = round(median(market_sizes), 2) if market_sizes else None
        consensus_cagr = round(median(cagrs), 2) if cagrs else None

        max_dev = 0.0
        if consensus_market and market_sizes:
            max_dev = max(abs(v - consensus_market) / consensus_market for v in market_sizes)

        flags = []
        if max_dev > 0.3:
            flags.append("High variance in market size estimates across sources")
        if len(cagrs) >= 3 and (max(cagrs) - min(cagrs)) > 8:
            flags.append("Wide CAGR spread detected across sources")

        return {
            "consensus_market_size_usd_billion": consensus_market,
            "consensus_cagr_percent": consensus_cagr,
            "inconsistencies": flags,
        }
