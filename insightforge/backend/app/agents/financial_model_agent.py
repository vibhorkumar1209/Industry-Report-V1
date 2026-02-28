from __future__ import annotations

from datetime import datetime


class FinancialModelAgent:
    DEFAULT_PEER_CAGR = 7.5

    def run(self, market_size: float | None, cagr_percent: float | None, years: int = 5) -> dict:
        estimated = False
        base_value = market_size
        cagr = cagr_percent

        if base_value is None:
            base_value = 50.0
            estimated = True
        if cagr is None:
            cagr = self.DEFAULT_PEER_CAGR
            estimated = True

        base_year = datetime.utcnow().year
        rows = []
        for year_offset in range(0, years + 1):
            year = base_year + year_offset
            value = base_value * ((1 + (cagr / 100)) ** year_offset)
            rows.append({"year": year, "market_size_usd_billion": round(value, 2)})

        return {
            "base_year": base_year,
            "base_value": round(base_value, 2),
            "cagr_percent": round(cagr, 2),
            "years": years,
            "table": rows,
            "estimated": estimated,
        }
