from __future__ import annotations

from app.market_intel.contracts import SEGMENT_DIMENSIONS


def check_dimension_coverage(segmentation_payload: dict) -> dict:
    present = set()
    for entry in segmentation_payload.get("dimension_tables", []):
        dim = str(entry.get("dimension", "")).strip()
        if dim:
            present.add(dim)

    missing = [d for d in SEGMENT_DIMENSIONS if d not in present]
    return {"covered_dimensions": sorted(present), "missing_dimensions": missing}


def reconcile_dimension_totals(segmentation_payload: dict, overall_market_by_year: dict[str, float], tolerance: float = 0.08) -> list[dict]:
    reconciliation_flags = []
    for table in segmentation_payload.get("dimension_tables", []):
        dimension = table.get("dimension", "unknown")
        rows = table.get("rows", [])

        for year, market_total in overall_market_by_year.items():
            segment_sum = 0.0
            for row in rows:
                year_values = row.get("year_values", {})
                try:
                    segment_sum += float(year_values.get(year, 0.0))
                except Exception:
                    continue

            if market_total <= 0:
                continue
            deviation = abs(segment_sum - market_total) / market_total
            if deviation > tolerance:
                reconciliation_flags.append(
                    {
                        "dimension": dimension,
                        "year": year,
                        "market_total": market_total,
                        "segment_sum": round(segment_sum, 3),
                        "deviation_percent": round(deviation * 100, 2),
                        "status": "out_of_tolerance",
                    }
                )

    return reconciliation_flags
