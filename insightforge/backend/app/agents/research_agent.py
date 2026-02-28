from __future__ import annotations

from urllib.parse import urlparse

import requests

from app.config import settings


MOCK_LINKS = [
    "https://www.iea.org/reports/electric-vehicle-outlook-2024",
    "https://www.worldbank.org/en/topic/industry",
    "https://www.oecd.org/industry",
    "https://www.imf.org/en/Publications/WEO",
    "https://www.statista.com/topics/",
    "https://www.mckinsey.com/industries",
    "https://www.bcg.com/industries",
    "https://www.gartner.com/en/insights",
    "https://www.goldmansachs.com/insights",
    "https://www.pwc.com/gx/en/industries.html",
    "https://www2.deloitte.com/global/en/industries.html",
    "https://www.fitchsolutions.com/industries",
    "https://www.sedarplus.ca/",
    "https://www.sec.gov/edgar/searchedgar/companysearch",
    "https://www.trade.gov/industry-analysis",
    "https://www.eia.gov/outlooks/steo/",
    "https://ec.europa.eu/eurostat",
    "https://www.unido.org/",
    "https://unctad.org/topic/trade-analysis",
    "https://www.weforum.org/reports/",
]


class ResearchAgent:
    def __init__(self) -> None:
        self.api_key = settings.parallel_api_key

    def run(self, industry: str, geography: str, limit: int = 20) -> list[dict]:
        if not self.api_key:
            return self._mock_results(industry, geography, limit)

        try:
            payload = {
                "query": f"{industry} market size CAGR drivers restraints {geography}",
                "limit": min(limit, settings.max_sources),
            }
            response = requests.post(
                "https://api.parallel.ai/v1/search",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            if response.ok:
                items = response.json().get("results", [])
                if items:
                    return [
                        {
                            "title": i.get("title", "Untitled Source"),
                            "url": i.get("url", "https://example.com"),
                            "domain": urlparse(i.get("url", "https://example.com")).netloc,
                            "published_at": i.get("published_at", ""),
                        }
                        for i in items[: limit]
                    ]
        except Exception:
            pass

        return self._mock_results(industry, geography, limit)

    def _mock_results(self, industry: str, geography: str, limit: int) -> list[dict]:
        results = []
        for idx, url in enumerate(MOCK_LINKS[:limit], start=1):
            results.append(
                {
                    "title": f"{industry} Intelligence Source {idx} ({geography})",
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "published_at": "",
                }
            )
        return results
