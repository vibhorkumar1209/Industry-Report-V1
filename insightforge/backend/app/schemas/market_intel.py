from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator


class MarketIntelScopeInput(BaseModel):
    industry: str = Field(..., min_length=2)
    geography: str = Field(..., min_length=2)
    start_year: int = Field(..., ge=1900, le=2100)
    end_year: int = Field(..., ge=1900, le=2100)
    currency: str = Field(default="USD", min_length=3, max_length=8)

    @model_validator(mode="after")
    def validate_years(self):
        if self.end_year < self.start_year:
            raise ValueError("end_year must be greater than or equal to start_year")
        return self


class MarketIntelRunRequest(MarketIntelScopeInput):
    execution_mode: Literal["saas", "api"] = "saas"


class MarketIntelComposeRequest(MarketIntelScopeInput):
    agent_outputs: dict[str, dict[str, Any]] = Field(default_factory=dict)
