from pydantic import BaseModel, Field


class ReportCreate(BaseModel):
    industry: str = Field(..., min_length=2)
    geography: str = Field(..., min_length=2)
    time_horizon: str = Field(..., min_length=3)
    depth: str = Field(..., pattern="^(Basic|Professional|Investor-grade)$")
    include_financial_forecast: bool = True
    include_competitive_landscape: bool = True


class ReportSectionRegenerate(BaseModel):
    section_name: str


class ReportResponse(BaseModel):
    id: int
    industry: str
    geography: str
    time_horizon: str
    depth: str
    status: str
    progress_message: str
    created_at: str

    class Config:
        from_attributes = True
