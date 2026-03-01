from __future__ import annotations

from urllib.parse import urlparse

from app.market_intel.contracts import ALLOWED_SOURCE_PATTERNS, DISALLOWED_SOURCE_PATTERNS


def score_source_credibility(url: str, publisher: str = "") -> tuple[int, str]:
    candidate = f"{url} {publisher}".lower()

    if any(pattern in candidate for pattern in DISALLOWED_SOURCE_PATTERNS):
        return 1, "Blocked or weak source class (blog/wiki/non-verifiable)."

    if any(pattern in candidate for pattern in ALLOWED_SOURCE_PATTERNS):
        return 5, "High-authority institutional/industry source pattern matched."

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    if host.endswith(".gov") or host.endswith(".edu"):
        return 5, "Government or academic domain."

    if host:
        return 3, "Source is usable but requires corroboration from higher-authority references."

    return 2, "Insufficient source metadata."


def merge_and_score_citations(agent_payloads: dict[str, dict]) -> list[dict]:
    seen = set()
    merged = []
    for payload in agent_payloads.values():
        citations = payload.get("citations", []) if isinstance(payload, dict) else []
        for citation in citations:
            url = str(citation.get("url", "")).strip()
            title = str(citation.get("title", "")).strip()
            key = (title, url)
            if not url or key in seen:
                continue
            seen.add(key)
            score, justification = score_source_credibility(url, str(citation.get("publisher", "")))
            merged.append(
                {
                    "source": title or url,
                    "type": citation.get("publisher", "Unknown"),
                    "credibility_score": score,
                    "justification": justification,
                    "publisher": citation.get("publisher", ""),
                    "year": citation.get("year", ""),
                    "url": url,
                    "page_ref": citation.get("page_ref", ""),
                }
            )

    merged.sort(key=lambda row: row["credibility_score"], reverse=True)
    return merged


def detect_weak_citations(credibility_rows: list[dict]) -> list[dict]:
    return [row for row in credibility_rows if row.get("credibility_score", 0) <= 2]
