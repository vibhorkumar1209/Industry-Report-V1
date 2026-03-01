from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ExecutionMode(str, Enum):
    SAAS = "saas"
    API = "api"


AGENT_ORDER = [
    "market_sizing",
    "segmentation",
    "trends",
    "technology_intelligence",
    "competitive_intelligence",
    "validation_credibility",
]


@dataclass
class ResearchScope:
    industry: str
    geography: str
    start_year: int
    end_year: int
    currency: str = "USD"


@dataclass
class AgentPromptPacket:
    agent_name: str
    objective: str
    prompt: str
    expected_output_contract: dict[str, Any]


@dataclass
class AgentRunResult:
    agent_name: str
    payload: dict[str, Any]


ALLOWED_SOURCE_PATTERNS = [
    ".gov",
    "worldbank.org",
    "oecd.org",
    "imf.org",
    "gartner.com",
    "idc.com",
    "mckinsey.com",
    "bcg.com",
    "deloitte.com",
    "frost.com",
    "annual report",
    "10-k",
]

DISALLOWED_SOURCE_PATTERNS = [
    "wikipedia.org",
    "blogspot.com",
    "medium.com",
    "substack.com",
]

SEGMENT_DIMENSIONS = [
    "application",
    "product_type",
    "category_subcategory",
    "end_use_verticals",
    "service_type",
    "geography_subregions",
    "buyer_type",
    "deployment_model",
    "technology_generation",
    "distribution_channel",
    "price_tier",
    "regulatory_classification",
]
