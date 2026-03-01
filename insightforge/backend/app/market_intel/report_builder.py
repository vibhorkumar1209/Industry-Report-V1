from __future__ import annotations

from dataclasses import asdict

from app.market_intel.contracts import ResearchScope


def build_word_style_report(scope: ResearchScope, payloads: dict[str, dict], credibility_rows: list[dict]) -> str:
    market = payloads.get("market_sizing", {})
    segmentation = payloads.get("segmentation", {})
    trends = payloads.get("trends", {})
    tech = payloads.get("technology_intelligence", {})
    comp = payloads.get("competitive_intelligence", {})
    validation = payloads.get("validation_credibility", {})

    historical_rows = _render_historical_rows(market)
    top_segments = _guess_top_segments(segmentation)
    top_drivers = _top_items(trends.get("key_drivers", []), "impact")
    top_risks = _top_items(trends.get("key_barriers", []), "impact")

    dimension_tables = _render_dimension_tables(segmentation)
    trend_table = _render_trigger_table(trends.get("major_trends", []))
    driver_table = _render_trigger_table(trends.get("key_drivers", []))
    barrier_table = _render_trigger_table(trends.get("key_barriers", []))

    traditional_table = _render_tech_table(tech.get("traditional_technologies", []))
    emerging_table = _render_tech_table(tech.get("emerging_technologies", []))
    company_table = _render_company_table(comp.get("top_players", []))

    credibility_table = _render_credibility_table(credibility_rows)
    assumptions = validation.get("assumptions_and_adjustments", {})
    citation_list = _render_citation_list(credibility_rows)

    reconciled = market.get("reconciliation", {}).get("reconciled_market_size_usd_bn", "N/A")
    cagr_percent = market.get("cagr_percent", "N/A")

    return f"""# {scope.industry} Industry Report - {scope.geography} ({scope.start_year}-{scope.end_year})

## 1. Executive Summary
- Total Market Size (latest year): USD {reconciled} Bn
- 5-Year CAGR: {cagr_percent}%
- Top 3 Growth Segments: {', '.join(top_segments) if top_segments else 'Data pending'}
- Top 3 Key Drivers: {', '.join(top_drivers) if top_drivers else 'Data pending'}
- Top 3 Key Risks: {', '.join(top_risks) if top_risks else 'Data pending'}
- Strategic Outlook: The market remains shaped by technology migration, regulatory pressure, and competitive repositioning.

## 2. Market Definition & Scope
- Industry boundaries: {scope.industry} value chain and adjacent services in {scope.geography}.
- NAICS/SIC codes: To be finalized by analyst using official statistical mappings.
- Inclusions & exclusions: Core commercial activities included; unrelated adjacent categories excluded.
- Currency normalization: {scope.currency}, nominal values.
- Data alignment year: {scope.end_year}

## 3. Market Size Estimation
### 3.1 Top-Down Approach
- Macro economic base: {market.get('top_down', {}).get('macro_base', 'N/A')}
- Sector extraction: {market.get('top_down', {}).get('sector_extraction', 'N/A')}
- Penetration ratios: {market.get('top_down', {}).get('penetration_ratio', 'N/A')}
- Final estimate: USD {market.get('top_down', {}).get('final_estimate_usd_bn', 'N/A')} Bn

### 3.2 Bottom-Up Approach
- Aggregated company revenues: {market.get('bottom_up', {}).get('company_revenue_basis', 'N/A')}
- Association data: {market.get('bottom_up', {}).get('association_basis', 'N/A')}
- Scale-up logic: {market.get('bottom_up', {}).get('scale_up_logic', 'N/A')}
- Final estimate: USD {market.get('bottom_up', {}).get('final_estimate_usd_bn', 'N/A')} Bn

### 3.3 Reconciliation Analysis
- Reconciled market size: USD {reconciled} Bn
- Reconciliation logic: {market.get('reconciliation', {}).get('logic', 'N/A')}

### 3.4 Historical Market Size (5 Years)
| Year | Market Size (USD Bn) | Source |
|---|---:|---|
{historical_rows}

CAGR Calculation:

CAGR = ((Latest / Earliest)^(1/Years) - 1)

### 3.5 Visualization
[Chart Placeholder: Combination Chart]
- Column: Market Size
- Line: CAGR
- Dual Axis: Enabled
- Sources listed under chart in Appendix C.

## 4. Comprehensive Market Segmentation
{dimension_tables}

## 5. Market Trends Section
### 5.1 Major Trends
| Trigger | Scenario Type | Impact | Examples (3-5) |
|---|---|---|---|
{trend_table}

### 5.2 Key Drivers
| Trigger | Scenario Type | Impact | Examples (3-5) |
|---|---|---|---|
{driver_table}

### 5.3 Key Barriers
| Trigger | Scenario Type | Impact | Examples (3-5) |
|---|---|---|---|
{barrier_table}

## 6. Technology Trends Impacting Industry
### 6.1 Traditional Technologies
| Technology | Category | Impact | Examples (3-5) | Key Companies & Solutions |
|---|---|---|---|---|
{traditional_table}

### 6.2 Emerging & Disruptive Technologies
| Technology | Category | Impact | Examples (3-5) | Key Companies & Solutions |
|---|---|---|---|---|
{emerging_table}

## 7. Competitive Landscape
| Company | Revenue | Market Share | Segment Leadership | Strategic Focus |
|---|---:|---:|---|---|
{company_table}

- Regional leaders: {', '.join(comp.get('regional_leaders', [])) if comp.get('regional_leaders') else 'N/A'}
- Recent M&A: {_render_ma_summary(comp.get('recent_ma_activity', []))}
- Product differentiation: {', '.join(comp.get('product_differentiation', [])) if comp.get('product_differentiation') else 'N/A'}

## 8. Strategic Insights
- White spaces: Underserved segments with low digital penetration and weak incumbent specialization.
- Disruption risks: Margin pressure from low-cost entrants and rapid tech substitution.
- Investment hotspots: High-growth subsegments with favorable regulation and adoption momentum.
- Consolidation outlook: Selective M&A likely in fragmented categories with platform economics.

## Notes
### Appendix A: Source Credibility Table
| Source | Type | Credibility Score (1-5) | Justification |
|---|---|---:|---|
{credibility_table}

### Appendix B: Assumptions & Adjustments
- Exchange rates: {assumptions.get('exchange_rates', 'N/A')}
- Inflation adjustments: {assumptions.get('inflation_adjustments', 'N/A')}
- Estimation logic: {assumptions.get('estimation_logic', 'N/A')}
- Interpolation logic: {assumptions.get('interpolation_logic', 'N/A')}
- Data gaps: {assumptions.get('data_gaps', 'N/A')}

### Appendix C: Citation List
| Title | Publisher | Year | URL / DOI | Page Reference |
|---|---|---:|---|---|
{citation_list}
"""


def _render_historical_rows(market_payload: dict) -> str:
    rows = market_payload.get("historical_market", [])
    if not rows:
        return "| N/A | N/A | N/A |"
    return "\n".join(
        f"| {row.get('year', 'N/A')} | {row.get('market_size_usd_bn', 'N/A')} | {row.get('source', 'N/A')} |"
        for row in rows
    )


def _render_dimension_tables(segmentation_payload: dict) -> str:
    tables = segmentation_payload.get("dimension_tables", [])
    if not tables:
        return "No segmentation table data provided."

    blocks = []
    for table in tables:
        dimension = table.get("dimension", "unknown").replace("_", " ").title()
        rows = table.get("rows", [])
        year_columns = []
        if rows:
            year_columns = sorted(rows[0].get("year_values", {}).keys())
        header = "| Segment | " + " | ".join(year_columns) + " | CAGR |"
        divider = "|---|" + "|".join(["---:" for _ in year_columns]) + "|---:|"
        body = "\n".join(
            f"| {row.get('segment', 'N/A')} | "
            + " | ".join(str(row.get("year_values", {}).get(year, "N/A")) for year in year_columns)
            + f" | {row.get('cagr_percent', 'N/A')}% |"
            for row in rows
        ) or "| N/A | N/A |"
        blocks.append(f"### {dimension}\n{header}\n{divider}\n{body}")
    return "\n\n".join(blocks)


def _render_trigger_table(items: list[dict]) -> str:
    if not items:
        return "| N/A | N/A | N/A | N/A |"
    return "\n".join(
        f"| {item.get('trigger', 'N/A')} | {item.get('scenario_type', 'N/A')} | {item.get('impact', 'N/A')} | {', '.join(item.get('examples', [])[:5]) or 'N/A'} |"
        for item in items
    )


def _render_tech_table(items: list[dict]) -> str:
    if not items:
        return "| N/A | N/A | N/A | N/A | N/A |"
    return "\n".join(
        f"| {row.get('technology', 'N/A')} | {row.get('category', 'N/A')} | {row.get('impact', 'N/A')} | {', '.join(row.get('examples', [])[:5]) or 'N/A'} | {', '.join(row.get('key_companies_and_solutions', [])[:8]) or 'N/A'} |"
        for row in items
    )


def _render_company_table(items: list[dict]) -> str:
    if not items:
        return "| N/A | N/A | N/A | N/A | N/A |"
    return "\n".join(
        f"| {row.get('company', 'N/A')} | {row.get('revenue', 'N/A')} | {row.get('market_share_percent', 'N/A')}% | {row.get('segment_leadership', 'N/A')} | {row.get('strategic_focus', 'N/A')} |"
        for row in items
    )


def _render_ma_summary(items: list[dict]) -> str:
    if not items:
        return "N/A"
    return "; ".join(f"{item.get('year', 'N/A')}: {item.get('deal', 'N/A')} ({item.get('rationale', 'N/A')})" for item in items)


def _render_credibility_table(rows: list[dict]) -> str:
    if not rows:
        return "| N/A | N/A | N/A | N/A |"
    return "\n".join(
        f"| {row.get('source', 'N/A')} | {row.get('type', 'N/A')} | {row.get('credibility_score', 'N/A')} | {row.get('justification', 'N/A')} |"
        for row in rows
    )


def _render_citation_list(rows: list[dict]) -> str:
    if not rows:
        return "| N/A | N/A | N/A | N/A | N/A |"
    return "\n".join(
        f"| {row.get('source', 'N/A')} | {row.get('publisher', 'N/A')} | {row.get('year', 'N/A')} | {row.get('url', 'N/A')} | {row.get('page_ref', 'N/A')} |"
        for row in rows
    )


def _top_items(items: list[dict], field: str, limit: int = 3) -> list[str]:
    picked = []
    for item in items[:limit]:
        value = str(item.get(field, "")).strip()
        if value:
            picked.append(value)
    return picked


def _guess_top_segments(segmentation_payload: dict) -> list[str]:
    for table in segmentation_payload.get("dimension_tables", []):
        rows = table.get("rows", [])
        if not rows:
            continue
        sorted_rows = sorted(
            rows,
            key=lambda r: float(r.get("cagr_percent", 0.0) or 0.0),
            reverse=True,
        )
        segments = [str(row.get("segment", "")).strip() for row in sorted_rows if row.get("segment")]
        if segments:
            return segments[:3]
    return []
