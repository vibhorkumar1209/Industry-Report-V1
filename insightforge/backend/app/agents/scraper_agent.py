from __future__ import annotations

import re

import requests
from bs4 import BeautifulSoup


class ScraperAgent:
    def run(self, url: str) -> dict:
        try:
            response = requests.get(url, timeout=20, headers={"User-Agent": "InsightForgeBot/1.0"})
            response.raise_for_status()
            html = response.text
            soup = BeautifulSoup(html, "lxml")
            for tag in soup(["script", "style", "noscript"]):
                tag.decompose()
            text = re.sub(r"\s+", " ", soup.get_text(" ")).strip()
            return {
                "raw_text": html[:200000],
                "cleaned_text": text[:12000],
            }
        except Exception:
            fallback = f"Unable to scrape {url}. Using fallback synthesized content for downstream extraction."
            return {"raw_text": fallback, "cleaned_text": fallback}
