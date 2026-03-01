from __future__ import annotations

from app.market_intel.contracts import AgentPromptPacket, ResearchScope, SEGMENT_DIMENSIONS


def _years(scope: ResearchScope) -> list[int]:
    return list(range(scope.start_year, scope.end_year + 1))


def build_agent_prompt_packets(scope: ResearchScope) -> list[AgentPromptPacket]:
    years = _years(scope)
    common_rules = (
        "Use only credible, citable sources. No Wikipedia, no uncited blogs, no unverifiable summaries. "
        "Return strict JSON only. Include source citations inside JSON with title, publisher, year, url, and page_ref when available."
    )

    return [
        AgentPromptPacket(
            agent_name="market_sizing",
            objective="Top-down and bottom-up market sizing with 5-year history and CAGR",
            prompt=(
                f"You are the Market Sizing Agent for {scope.industry} in {scope.geography} ({scope.start_year}-{scope.end_year}). "
                f"{common_rules} Build top_down, bottom_up, reconciliation, historical_market, cagr_calculation, chart_notes. "
                "Historical table must include each year and market_size_usd_bn. "
                "CAGR formula: ((Latest / Earliest)^(1/Years)-1)."
            ),
            expected_output_contract={
                "top_down": {"macro_base": "", "sector_extraction": "", "penetration_ratio": 0.0, "final_estimate_usd_bn": 0.0},
                "bottom_up": {"company_revenue_basis": "", "association_basis": "", "scale_up_logic": "", "final_estimate_usd_bn": 0.0},
                "reconciliation": {"reconciled_market_size_usd_bn": 0.0, "logic": ""},
                "historical_market": [{"year": years[0], "market_size_usd_bn": 0.0, "source": ""}],
                "cagr_percent": 0.0,
                "chart_notes": "",
                "citations": [{"title": "", "publisher": "", "year": 0, "url": "", "page_ref": ""}],
            },
        ),
        AgentPromptPacket(
            agent_name="segmentation",
            objective="Build complete segmentation tree and reconcile totals",
            prompt=(
                f"You are the Segmentation Agent for {scope.industry} in {scope.geography} across years {years}. "
                f"Cover all dimensions: {', '.join(SEGMENT_DIMENSIONS)}. "
                f"{common_rules} Return full segmentation_tree and yearly tables per dimension with CAGR and reconciliation flags."
            ),
            expected_output_contract={
                "segmentation_tree": {"root": scope.industry, "children": []},
                "dimension_tables": [
                    {
                        "dimension": "application",
                        "rows": [
                            {
                                "segment": "",
                                "year_values": {str(year): 0.0 for year in years},
                                "cagr_percent": 0.0,
                            }
                        ],
                        "reconciles_with_market": True,
                    }
                ],
                "missing_dimension_checks": [],
                "citations": [{"title": "", "publisher": "", "year": 0, "url": "", "page_ref": ""}],
            },
        ),
        AgentPromptPacket(
            agent_name="trends",
            objective="Major trends, key drivers, key barriers with dimensional coverage",
            prompt=(
                f"You are the Trends Agent for {scope.industry} in {scope.geography} ({scope.start_year}-{scope.end_year}). "
                f"{common_rules} Build major_trends, key_drivers, key_barriers with table fields: trigger, scenario_type, impact, examples (3-5). "
                "Ensure coverage: overall, demand, supply, technology, macro/VUCA, regulatory, commercial, competitive, regional, sub-segment."
            ),
            expected_output_contract={
                "major_trends": [{"trigger": "", "scenario_type": "", "impact": "", "examples": ["", "", ""]}],
                "key_drivers": [{"trigger": "", "scenario_type": "", "impact": "", "examples": ["", "", ""]}],
                "key_barriers": [{"trigger": "", "scenario_type": "", "impact": "", "examples": ["", "", ""]}],
                "coverage_check": {"covered_dimensions": [], "missing_dimensions": []},
                "citations": [{"title": "", "publisher": "", "year": 0, "url": "", "page_ref": ""}],
            },
        ),
        AgentPromptPacket(
            agent_name="technology_intelligence",
            objective="Traditional and emerging technology mapping, vendors, geo variation",
            prompt=(
                f"You are the Technology Intelligence Agent for {scope.industry} in {scope.geography}. "
                f"{common_rules} Provide traditional_technologies (8-12 rows) and emerging_technologies (10-15 rows). "
                "Each row: technology, category, impact, examples (3-5), key_companies_and_solutions, geo_variation, subsegment_impact. "
                "Mention at least 20 unique technology companies across all rows."
            ),
            expected_output_contract={
                "traditional_technologies": [
                    {
                        "technology": "",
                        "category": "",
                        "impact": "",
                        "examples": ["", "", ""],
                        "key_companies_and_solutions": [""],
                        "geo_variation": "",
                        "subsegment_impact": "",
                    }
                ],
                "emerging_technologies": [
                    {
                        "technology": "",
                        "category": "",
                        "impact": "",
                        "examples": ["", "", ""],
                        "key_companies_and_solutions": [""],
                        "geo_variation": "",
                        "subsegment_impact": "",
                    }
                ],
                "unique_companies": [],
                "citations": [{"title": "", "publisher": "", "year": 0, "url": "", "page_ref": ""}],
            },
        ),
        AgentPromptPacket(
            agent_name="competitive_intelligence",
            objective="Top players, shares, strategic positioning, M&A",
            prompt=(
                f"You are the Competitive Intelligence Agent for {scope.industry} in {scope.geography}. "
                f"{common_rules} Build top_players table (top 10), regional leaders, recent_ma_activity, product_differentiation, strategic_positioning."
            ),
            expected_output_contract={
                "top_players": [
                    {
                        "company": "",
                        "revenue": "",
                        "market_share_percent": 0.0,
                        "segment_leadership": "",
                        "strategic_focus": "",
                    }
                ],
                "regional_leaders": [],
                "recent_ma_activity": [{"deal": "", "year": 0, "rationale": ""}],
                "product_differentiation": [],
                "strategic_positioning": [],
                "citations": [{"title": "", "publisher": "", "year": 0, "url": "", "page_ref": ""}],
            },
        ),
        AgentPromptPacket(
            agent_name="validation_credibility",
            objective="Score source credibility and identify weak logic",
            prompt=(
                f"You are the Validation & Credibility Agent for {scope.industry} in {scope.geography}. "
                f"{common_rules} Score each source 1-5 with justification, flag weak citations, and challenge estimation assumptions."
            ),
            expected_output_contract={
                "source_credibility": [
                    {"source": "", "type": "", "credibility_score": 1, "justification": ""}
                ],
                "weak_citations": [],
                "estimation_logic_flags": [],
                "assumptions_and_adjustments": {
                    "exchange_rates": "",
                    "inflation_adjustments": "",
                    "estimation_logic": "",
                    "interpolation_logic": "",
                    "data_gaps": "",
                },
            },
        ),
    ]
