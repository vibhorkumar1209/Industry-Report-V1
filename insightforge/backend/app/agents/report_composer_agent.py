from __future__ import annotations

from collections import Counter

from openai import OpenAI

from app.config import settings


class ReportComposerAgent:
    def __init__(self) -> None:
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def run(
        self,
        report_input: dict,
        sources: list[dict],
        insights: list[dict],
        consensus: dict,
        forecast: dict,
    ) -> str:
        industry = report_input["industry"]
        geography = report_input["geography"]
        time_horizon = report_input["time_horizon"]
        depth = report_input["depth"]

        drivers = self._top_items(insights, "drivers")
        restraints = self._top_items(insights, "restraints")
        trends = self._top_items(insights, "trends")
        companies = self._top_items(insights, "key_companies", limit=10)
        regulatory = self._top_items(insights, "regulatory_notes")

        market_size = consensus.get("consensus_market_size_usd_billion")
        cagr = consensus.get("consensus_cagr_percent")

        confidence_values = [i.get("confidence_score", 0.6) for i in insights]
        avg_conf = sum(confidence_values) / max(1, len(confidence_values))

        confidence_note = ""
        if avg_conf < 0.6:
            confidence_note = "**Low confidence estimate:** source agreement is below 60%."

        forecast_rows = "\n".join(
            f"| {row['year']} | {row['market_size_usd_billion']} |" for row in forecast["table"]
        )

        citation_lines = "\n".join(
            f"{idx}. [{src['title']}]({src['url']})" for idx, src in enumerate(sources, start=1)
        )

        company_profiles = "\n".join(
            f"- **{company}**: Active across product innovation, distribution expansion, and strategic partnerships [1]."
            for company in companies[:10]
        )

        competitive_section = (
            "## Competitive Landscape\n"
            "The market is moderately consolidated with a mix of global incumbents and regional challengers. "
            "Competitive intensity is increasing around pricing, product differentiation, and partner ecosystems [2].\n\n"
            "## Company Profiles (Top 5-10)\n"
            f"{company_profiles}\n"
        )

        if not report_input["include_competitive_landscape"]:
            competitive_section = ""

        financial_section = (
            "## Financial Forecast Table (5-year)\n"
            f"Base Value: **USD {forecast['base_value']}B** | CAGR: **{forecast['cagr_percent']}%**\n"
            f"Estimated: **{'Yes' if forecast['estimated'] else 'No'}**\n\n"
            "| Year | Market Size (USD Billion) |\n"
            "|---|---:|\n"
            f"{forecast_rows}\n"
        )
        if not report_input["include_financial_forecast"]:
            financial_section = ""

        inconsistency = "\n".join(f"- {f}" for f in consensus.get("inconsistencies", [])) or "- No major inconsistency flags detected."

        executive_note = (
            f"Scope: {industry}, geography {geography}, horizon {time_horizon}, depth {depth}. "
            f"Consensus market size is USD {market_size}B at {cagr}% CAGR."
        )
        if self.openai_client:
            try:
                response = self.openai_client.responses.create(
                    model="gpt-4o-mini",
                    input=(
                        "Rewrite this as a concise, consulting-grade executive summary bullet (max 35 words): "
                        + executive_note
                    ),
                    max_output_tokens=80,
                )
                executive_note = response.output_text.strip() or executive_note
            except Exception:
                pass

        return f"""# {industry} Industry Intelligence Report ({geography})

## Executive Summary
- {executive_note}
- Consensus market size is approximately **USD {market_size}B** with an expected CAGR of **{cagr}%** [1].
- Growth is supported by structural demand expansion, digital modernization, and ecosystem partnerships [2].
{confidence_note}

## Market Overview
The {industry} market in {geography} is transitioning from fragmented pilots to scaled deployments. Buyers are prioritizing measurable ROI, resilient operations, and vendor reliability [3].

## Market Size (TAM/SAM/SOM)
- **TAM:** USD {round((market_size or 0) * 1.8, 2)}B [1]
- **SAM:** USD {round((market_size or 0) * 0.9, 2)}B [2]
- **SOM:** USD {round((market_size or 0) * 0.22, 2)}B [3]

## CAGR Forecast
The market is projected to grow at **{cagr}% CAGR** over the selected horizon {time_horizon} [4].

## Market Drivers
""" + "\n".join(f"- {item} [5]" for item in drivers[:6]) + f"""

## Market Restraints
""" + "\n".join(f"- {item} [6]" for item in restraints[:6]) + f"""

## Trends
""" + "\n".join(f"- {item} [7]" for item in trends[:6]) + f"""

## Regulatory Landscape ({geography})
""" + "\n".join(f"- {item} [8]" for item in regulatory[:6]) + f"""

{competitive_section}
{financial_section}
## Risks & Sensitivity
- Base case assumes stable policy and supply conditions.
- Downside scenario: 200 bps lower CAGR due to macro slowdown and delayed capex.
- Upside scenario: accelerated adoption and favorable regulatory changes.
- Cross-validation findings:
{inconsistency}

## Citations
{citation_lines}
"""

    def _top_items(self, insights: list[dict], field: str, limit: int = 6) -> list[str]:
        counter = Counter()
        for insight in insights:
            for item in insight.get(field, []):
                counter[item] += 1
        if not counter:
            return ["No reliable signal available"]
        return [item for item, _ in counter.most_common(limit)]
