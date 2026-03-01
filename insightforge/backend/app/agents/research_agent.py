from __future__ import annotations

import json
import re
from datetime import datetime
from urllib.parse import parse_qs, unquote, urlparse

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

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

BLOCKED_DOMAINS = {
    "youtube.com",
    "facebook.com",
    "instagram.com",
    "tiktok.com",
    "x.com",
    "twitter.com",
    "linkedin.com",
    "pinterest.com",
    "reddit.com",
}

AUTHORITY_HINTS = [
    ".gov",
    "worldbank",
    "oecd",
    "imf",
    "europa",
    "un",
    "statista",
    "mckinsey",
    "deloitte",
    "pwc",
    "fitch",
    "gartner",
    "bloomberg",
    "reuters",
]

STRICT_AUTHORITY_DOMAINS = [
    ".gov",
    "oecd.org",
    "worldbank.org",
    "imf.org",
    "europa.eu",
    "europa.ec",
    "un.org",
    "unctad.org",
    "unido.org",
    "sec.gov",
    "sedarplus.ca",
    "fca.org.uk",
    "esma.europa.eu",
    "ec.europa.eu",
]

STRICT_SITE_FILTERS = [
    "site:.gov",
    "site:oecd.org",
    "site:worldbank.org",
    "site:imf.org",
    "site:ec.europa.eu",
    "site:europa.eu",
    "site:un.org",
    "site:unctad.org",
    "site:unido.org",
    "site:sec.gov",
    "site:sedarplus.ca",
]


class ResearchAgent:
    def __init__(self) -> None:
        self.api_key = settings.parallel_api_key
        self.max_sources = settings.max_sources
        self.openai_client = OpenAI(api_key=settings.openai_api_key) if settings.openai_api_key else None

    def run(self, industry: str, geography: str, limit: int = 20) -> list[dict]:
        size = min(limit, self.max_sources)

        if self.openai_client:
            openai_results = self._openai_web_results(
                industry=industry,
                geography=geography,
                queries=self._query_variants(industry, geography),
                limit=size,
            )
            if openai_results:
                return openai_results

        if self.api_key:
            parallel_results = self._parallel_results(industry, geography, size)
            if parallel_results:
                return parallel_results

        if settings.strict_no_key_research:
            strict_results = self._strict_no_key_results(industry, geography, size)
            if strict_results:
                return strict_results

        dynamic_results = self._dynamic_web_results(industry, geography, size)
        if dynamic_results:
            return dynamic_results

        return self._curated_fallback(industry, geography, size)

    def run_for_section(self, industry: str, geography: str, section: str, limit: int = 6) -> list[dict]:
        size = min(limit, self.max_sources)
        queries = self._query_variants_for_section(industry, geography, section)

        if self.openai_client:
            openai_results = self._openai_web_results(industry, geography, queries, size, section=section)
            if openai_results:
                for item in openai_results:
                    item["section"] = section
                return openai_results

        combined: list[dict] = []
        if self.api_key:
            for query in queries:
                try:
                    payload = {"query": query, "limit": max(3, size)}
                    response = requests.post(
                        "https://api.parallel.ai/v1/search",
                        json=payload,
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        timeout=20,
                    )
                    response.raise_for_status()
                    items = response.json().get("results", [])
                    combined.extend(self._normalize_results(items, max(3, size)))
                except Exception:
                    continue

        if not combined:
            if settings.strict_no_key_research:
                strict = self._strict_no_key_results(industry, geography, size, section=section)
                if strict:
                    for item in strict:
                        item["section"] = section
                    return strict
            for query in queries:
                combined.extend(self._search_google_news_rss(query, per_query=max(5, size)))
                combined.extend(self._search_duckduckgo_html(query, per_query=max(5, size)))

        finalized = self._finalize_results(combined, industry, geography, size)
        for item in finalized:
            item["section"] = section
        return finalized

    def _strict_no_key_results(
        self,
        industry: str,
        geography: str,
        limit: int,
        section: str | None = None,
    ) -> list[dict]:
        base_queries = self._query_variants_for_section(industry, geography, section) if section else self._query_variants(industry, geography)
        authority_queries = []
        for q in base_queries[:4]:
            for filt in STRICT_SITE_FILTERS:
                authority_queries.append(f"{q} {filt}")

        combined: list[dict] = []
        for query in authority_queries[: min(len(authority_queries), 24)]:
            combined.extend(self._search_duckduckgo_html(query, per_query=max(4, limit)))
            combined.extend(self._search_google_news_rss(query, per_query=max(3, limit)))

        finalized = self._finalize_results(combined, industry, geography, limit, strict_authority_only=True)
        if not finalized:
            # Strict curated fallback retains high-authority institutions and filings.
            fallback = self._curated_fallback(industry, geography, limit)
            return self._finalize_results(fallback, industry, geography, limit, strict_authority_only=True)
        return finalized

    def _openai_web_results(
        self,
        industry: str,
        geography: str,
        queries: list[str],
        limit: int,
        section: str | None = None,
    ) -> list[dict]:
        if not self.openai_client:
            return []

        prompt = (
            "Perform web research and return strict JSON array only. "
            "Each object keys: title, url, published_at, snippet. "
            f"Industry: {industry}. Geography: {geography}. "
            f"Section: {section or 'general'}. "
            f"Use these search intents: {queries[:4]}. "
            f"Return up to {limit} high-quality sources."
        )
        try:
            response = self.openai_client.responses.create(
                model="gpt-4.1-mini",
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                temperature=0.1,
                max_output_tokens=1400,
            )
            output_text = (response.output_text or "").strip()
            items = self._parse_openai_items(output_text)
            if not items:
                return []
            normalized = self._normalize_results(items, limit * 2)
            return self._finalize_results(normalized, industry, geography, limit)
        except Exception:
            return []

    def _parse_openai_items(self, text: str) -> list[dict]:
        if not text:
            return []
        try:
            parsed = json.loads(text)
            if isinstance(parsed, list):
                return [x for x in parsed if isinstance(x, dict)]
        except Exception:
            pass

        # Fallback parser if model does not return strict JSON.
        urls = re.findall(r"https?://[^\s\]\)\"'>]+", text)
        items = []
        for idx, url in enumerate(urls[:20], start=1):
            items.append(
                {
                    "title": f"Web Source {idx}",
                    "url": url,
                    "published_at": "",
                    "snippet": "",
                }
            )
        return items

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
            normalized = self._normalize_results(items, limit)
            return self._finalize_results(normalized, industry, geography, limit)
        except Exception:
            return []

    def _dynamic_web_results(self, industry: str, geography: str, limit: int) -> list[dict]:
        queries = self._query_variants(industry, geography)

        combined: list[dict] = []
        for query in queries:
            combined.extend(self._search_google_news_rss(query, per_query=10))
            combined.extend(self._search_duckduckgo_html(query, per_query=10))

        return self._finalize_results(combined, industry, geography, limit)

    def _query_variants(self, industry: str, geography: str) -> list[str]:
        return [
            f"{industry} market size {geography}",
            f"{industry} CAGR forecast {geography}",
            f"{industry} market trends {geography}",
            f"{industry} competitive landscape key players {geography}",
            f"{industry} regulatory landscape {geography}",
            f"{industry} TAM SAM SOM {geography}",
            f"{industry} annual report market outlook {geography}",
        ]

    def _query_variants_for_section(self, industry: str, geography: str, section: str) -> list[str]:
        section_map = {
            "market_overview": [
                f"{industry} market overview {geography}",
                f"{industry} industry outlook {geography}",
                f"{industry} market trends and adoption {geography}",
            ],
            "market_size_forecast": [
                f"{industry} market size {geography}",
                f"{industry} CAGR forecast {geography}",
                f"{industry} TAM SAM SOM {geography}",
            ],
            "market_dynamics": [
                f"{industry} market drivers restraints {geography}",
                f"{industry} key trends barriers {geography}",
                f"{industry} opportunities threats {geography}",
            ],
            "regulatory_landscape": [
                f"{industry} regulatory landscape {geography}",
                f"{industry} compliance requirements {geography}",
                f"{industry} policy framework {geography}",
            ],
            "competitive_landscape": [
                f"{industry} competitive landscape key players {geography}",
                f"{industry} market share companies {geography}",
                f"{industry} company profiles {geography}",
            ],
            "financial_outlook": [
                f"{industry} revenue forecast {geography}",
                f"{industry} investment outlook {geography}",
                f"{industry} demand forecast {geography}",
            ],
        }
        return section_map.get(section, self._query_variants(industry, geography))

    def _search_google_news_rss(self, query: str, per_query: int = 10) -> list[dict]:
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
                        "snippet": "",
                    }
                )
            return out
        except Exception:
            return []

    def _search_duckduckgo_html(self, query: str, per_query: int = 10) -> list[dict]:
        try:
            resp = requests.get(
                "https://duckduckgo.com/html/",
                params={"q": query},
                timeout=15,
                headers={"User-Agent": "InsightForgeResearchBot/1.0"},
            )
            resp.raise_for_status()

            soup = BeautifulSoup(resp.text, "html.parser")
            result_nodes = soup.select(".result")[:per_query]

            out = []
            for node in result_nodes:
                anchor = node.select_one("a.result__a")
                if not anchor:
                    continue
                href = (anchor.get("href") or "").strip()
                clean_url = self._extract_redirect_target(href)
                title = anchor.get_text(" ", strip=True) or "Untitled Source"
                snippet_node = node.select_one(".result__snippet")
                snippet = snippet_node.get_text(" ", strip=True) if snippet_node else ""
                if not clean_url:
                    continue
                out.append(
                    {
                        "title": title,
                        "url": clean_url,
                        "domain": urlparse(clean_url).netloc,
                        "published_at": "",
                        "snippet": snippet,
                    }
                )
            return out
        except Exception:
            return []

    def _extract_redirect_target(self, url: str) -> str:
        if not url:
            return ""

        parsed = urlparse(url)
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
                    "snippet": i.get("snippet", ""),
                }
            )
        return normalized

    def _finalize_results(
        self,
        items: list[dict],
        industry: str,
        geography: str,
        limit: int,
        strict_authority_only: bool = False,
    ) -> list[dict]:
        deduped = self._dedupe(items)
        filtered = [x for x in deduped if self._is_valid_source(x, strict_authority_only=strict_authority_only)]
        ranked = self._score_relevance(filtered, industry, geography)
        diversified = self._enforce_domain_diversity(ranked, per_domain_limit=2)

        if len(diversified) < max(6, limit // 2):
            fallback = self._curated_fallback(industry, geography, limit)
            fallback = [x for x in fallback if self._is_valid_source(x, strict_authority_only=strict_authority_only)]
            diversified.extend(fallback)
            diversified = self._dedupe(diversified)
            diversified = self._score_relevance(diversified, industry, geography)
            diversified = self._enforce_domain_diversity(diversified, per_domain_limit=2)

        return diversified[:limit]

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

    def _is_valid_source(self, item: dict, strict_authority_only: bool = False) -> bool:
        domain = (item.get("domain") or "").lower()
        title = (item.get("title") or "").lower()
        url = (item.get("url") or "").lower()

        if not domain:
            return False
        if any(blocked in domain for blocked in BLOCKED_DOMAINS):
            return False
        if any(x in url for x in ["/login", "/signin", "subscribe", "paywall", "accounts."]):
            return False

        market_signals = ["market", "cagr", "forecast", "industry", "analysis", "trend", "outlook", "report"]
        if not any(sig in title or sig in url for sig in market_signals):
            return False

        if strict_authority_only and not any(hint in domain for hint in STRICT_AUTHORITY_DOMAINS):
            return False

        return True

    def _score_relevance(self, items: list[dict], industry: str, geography: str) -> list[dict]:
        industry_terms = {t.lower() for t in industry.split() if t.strip()}
        geo_terms = {t.lower() for t in geography.split() if t.strip()}
        intent_terms = {"market", "size", "forecast", "cagr", "industry", "analysis", "trend", "regulatory"}

        scored = []
        for item in items:
            title = item.get("title", "").lower()
            url = item.get("url", "").lower()
            snippet = item.get("snippet", "").lower()
            text = f"{title} {snippet} {url}"

            token_hits = sum(1 for t in industry_terms if t in text)
            token_hits += sum(1 for t in geo_terms if t in text)
            token_hits += sum(1 for t in intent_terms if t in text)

            domain = (item.get("domain") or "").lower()
            authority_boost = 2 if any(h in domain for h in AUTHORITY_HINTS) else 0

            freshness_boost = 0
            published = item.get("published_at", "")
            if str(datetime.utcnow().year) in str(published):
                freshness_boost = 1

            raw_score = float(token_hits + authority_boost + freshness_boost)
            relevance_score = max(0.0, min(1.0, round(raw_score / 18.0, 3)))

            scored_item = dict(item)
            scored_item["relevance_score"] = relevance_score
            scored.append(scored_item)

        return sorted(scored, key=lambda x: x.get("relevance_score", 0), reverse=True)

    def _enforce_domain_diversity(self, items: list[dict], per_domain_limit: int = 2) -> list[dict]:
        out = []
        domain_counts: dict[str, int] = {}
        for item in items:
            domain = item.get("domain", "")
            cnt = domain_counts.get(domain, 0)
            if cnt >= per_domain_limit:
                continue
            out.append(item)
            domain_counts[domain] = cnt + 1
        return out

    def _curated_fallback(self, industry: str, geography: str, limit: int) -> list[dict]:
        results = []
        for idx, url in enumerate(CURATED_FALLBACK_LINKS[:limit], start=1):
            results.append(
                {
                    "title": f"{industry} Research Source {idx} ({geography})",
                    "url": url,
                    "domain": urlparse(url).netloc,
                    "published_at": "",
                    "snippet": "",
                    "relevance_score": 0.5,
                }
            )
        return results
