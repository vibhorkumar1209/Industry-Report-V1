from __future__ import annotations

from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup

from app.config import settings


CURATED_FALLBACK_LINKS = [
    "https://www.worldbank.org/en/topic/industry",
    "https://www.oecd.org/industry",
    "https://www.imf.org/en/Publications/WEO",
    "https://ec.europa.eu/eurostat",
    "https://www.unido.org/",
    "https://unctad.org/topic/trade-analysis",
    "https://www.weforum.org/reports/",
    "https://www.trade.gov/industry-analysis",
    "https://www.eia.gov/outlooks/steo/",
    "https://www.sec.gov/edgar/searchedgar/companysearch",
]


class ResearchAgent:
    def __init__(self) -> None:
        self.api_key = settings.parallel_api_key
        self.max_sources = settings.max_sources

    def run(self, industry: str, geography: str, limit: int = 20) -> list[dict]:
        size = min(limit, self.max_sources)

        # Preferred mode: Parallel API
        if self.api_key:
            parallel_results = self._parallel_results(industry, geography, size)
            if parallel_results:
                return parallel_results

        # Dynamic fallback mode: live web search without API key
        dynamic_results = self._dynamic_web_results(industry, geography, size)
        if dynamic_results:
            return dynamic_results

        # Final fallback if search providers are inaccessible
        return self._curated_fallback(industry, geography, size)

    def _parallel_results(self, industry: str, geography: str, limit: int) -> list[dict]:
        try:
            payload = {
                "query": f"{industry} market size CAGR forecast trends drivers restraints {geography}",
                "limit": limit,
            }
            response = requests.post(
                "https://api.parallel.ai/v1/search",
                json=payload,
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=20,
            )
            response.raise_for_status()
            items = response.json().get("results", [])
            return self._normalize_results(items, limit)
        except Exception:
            return []

    def _dynamic_web_results(self, industry: str, geography: str, limit: int) -> list[dict]:
        query_variants = [
            f"{industry} market size {geography}",
            f"{industry} CAGR forecast {geography}",
            f"{industry} trends regulatory landscape {geography}",
            f"{industry} competitive landscape key players {geography}",
        ]

        combined: list[dict] = []
        for query in query_variants:
            combined.extend(self._search_google_news_rss(query, per_query=8))
            combined.extend(self._search_duckduckgo_html(query, per_query=8))

        deduped = self._dedupe(combined)
        scored = self._score_relevance(deduped, industry, geography)
        return scored[:limit]

    def _search_google_news_rss(self, query: str, per_query: int = 8) -> list[dict]:
        try:
            resp = requests.get(
                "https://news.google.com/rss/search",
                params={"q": query, "hl": "en-US", "gl": "US", "ceid": "US:en"},
                timeout=15,
                headers={"User-Agent": "InsightForgeResearchBot/1.0"},
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "xml")
            items = soup.find_all("item")[:per_query]

            out = []
            for item in items:
                link = (item.link.text or "").strip()
                clean_url = self._extract_redirect_target(link)
                title = (item.title.text or "Untitled Source").strip()
                pub_date = (item.pubDate.text or "").strip()
                if not clean_url:
                    continue
                out.append(
                    {
                        "title": title,
                        "url": clean_url,
                        "domain": urlparse(clean_url).netloc,
                        "published_at": pub_date,
                    }
                )
            return out
        except Exception:
            return []

    def _search_duckduckgo_html(self, query: str, per_query: int = 8) -> list[dict]:
        try:
            resp = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                timeout=15,
                headers={"User-Agent": "InsightForgeResearchBot/1.0"},
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "lxml")
            links = soup.select("a.result__a")[:per_query]

            out = []
            for anchor in links:
                href = (anchor.get("href") or "").strip()
                clean_url = self._extract_redirect_target(href)
                title = anchor.get_text(" ", strip=True) or "Untitled Source"
                if not clean_url:
                    continue
                out.append(
                    {
                        "title": title,
                        "url": clean_url,
                        "domain": urlparse(clean_url).netloc,
                        "published_at": "",
                    }
                )
            return out
        except Exception:
            return []

    def _extract_redirect_target(self, url: str) -> str:
        if not url:
            return ""

        parsed = urlparse(url)

        # Handle DDG redirect wrappers (/l/?uddg=...)
        if parsed.netloc.endswith("duckduckgo.com") and parsed.path.startswith("/l/"):
            qs = parse_qs(parsed.query)
            uddg = qs.get("uddg", [""])[0]
            return unquote(uddg) if uddg else ""

        if parsed.scheme in {"http", "https"}:
            return url
        return ""

    def _normalize_results(self, items: list[dict], limit: int) -> list[dict]:
        normalized = []
        for i in items[:limit]:
            url = i.get("url", "")
            if not url:
                continue
            normalized.append(
                {
                    "title": i.get("title", "Untitled Source"),
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "published_at": i.get("published_at", ""),
                }
            )
        return self._dedupe(normalized)[:limit]

    def _dedupe(self, items: list[dict]) -> list[dict]:
        seen = set()
        out = []
        for item in items:
            url = item.get("url", "").strip()
            if not url:
                continue
            key = url.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
        return out

    def _score_relevance(self, items: list[dict], industry: str, geography: str) -> list[dict]:
        industry_terms = {t.lower() for t in industry.split() if t.strip()}
        geo_terms = {t.lower() for t in geography.split() if t.strip()}
        intent_terms = {"market", "size", "forecast", "cagr", "industry", "analysis", "trend"}

        def score(item: dict) -> float:
            title = item.get("title", "").lower()
            url = item.get("url", "").lower()
            text = f"{title} {url}"

            token_hits = sum(1 for t in industry_terms if t in text)
            token_hits += sum(1 for t in geo_terms if t in text)
            token_hits += sum(1 for t in intent_terms if t in text)

            authority_boost = 0
            domain = item.get("domain", "")
            if any(x in domain for x in ["gov", "oecd", "worldbank", "imf", "europa", "un", "statista", "mckinsey", "deloitte", "pwc"]):
                authority_boost = 2

            freshness_boost = 0
            published = item.get("published_at", "")
            if str(datetime.utcnow().year) in str(published):
                freshness_boost = 1

            return float(token_hits + authority_boost + freshness_boost)

        return sorted(items, key=score, reverse=True)

    def _curated_fallback(self, industry: str, geography: str, limit: int) -> list[dict]:
        results = []
        for idx, url in enumerate(CURATED_FALLBACK_LINKS[:limit], start=1):
            results.append(
                {
                    "title": f"{industry} Research Source {idx} ({geography})",
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "published_at": "",
                }
            )
        return results
