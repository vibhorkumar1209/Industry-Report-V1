from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    reports = relationship("Report", back_populates="user")


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)

    industry: Mapped[str] = mapped_column(String(255), nullable=False)
    geography: Mapped[str] = mapped_column(String(255), nullable=False)
    time_horizon: Mapped[str] = mapped_column(String(100), nullable=False)
    depth: Mapped[str] = mapped_column(String(50), nullable=False)

    include_financial_forecast: Mapped[bool] = mapped_column(Boolean, default=True)
    include_competitive_landscape: Mapped[bool] = mapped_column(Boolean, default=True)

    status: Mapped[str] = mapped_column(String(32), default="Queued")
    progress_message: Mapped[str] = mapped_column(String(255), default="Queued for processing")

    markdown_content: Mapped[str] = mapped_column(Text, default="")
    html_content: Mapped[str] = mapped_column(Text, default="")
    pdf_path: Mapped[str] = mapped_column(String(500), default="")

    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="reports")
    sources = relationship("Source", back_populates="report", cascade="all, delete-orphan")
    insights = relationship("ExtractedInsight", back_populates="report", cascade="all, delete-orphan")
    forecasts = relationship("Forecast", back_populates="report", cascade="all, delete-orphan")
    citations = relationship("Citation", back_populates="report", cascade="all, delete-orphan")


class Source(Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)

    title: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)
    domain: Mapped[str] = mapped_column(String(255), default="")
    published_at: Mapped[str] = mapped_column(String(100), default="")

    raw_text: Mapped[str] = mapped_column(Text, default="")
    cleaned_text: Mapped[str] = mapped_column(Text, default="")
    relevance_score: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="sources")


class ExtractedInsight(Base):
    __tablename__ = "extracted_insights"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)

    market_size_usd_billion: Mapped[float | None] = mapped_column(Float, nullable=True)
    cagr_percent: Mapped[float | None] = mapped_column(Float, nullable=True)
    drivers: Mapped[list] = mapped_column(JSON, default=list)
    restraints: Mapped[list] = mapped_column(JSON, default=list)
    trends: Mapped[list] = mapped_column(JSON, default=list)
    key_companies: Mapped[list] = mapped_column(JSON, default=list)
    regulatory_notes: Mapped[list] = mapped_column(JSON, default=list)

    confidence_score: Mapped[float] = mapped_column(Float, default=0.7)
    extracted_payload: Mapped[dict] = mapped_column(JSON, default=dict)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="insights")


class Forecast(Base):
    __tablename__ = "forecasts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)

    base_year: Mapped[int] = mapped_column(Integer)
    base_value: Mapped[float] = mapped_column(Float)
    cagr_percent: Mapped[float] = mapped_column(Float)
    years: Mapped[int] = mapped_column(Integer, default=5)
    table_json: Mapped[list] = mapped_column(JSON, default=list)
    estimated: Mapped[bool] = mapped_column(Boolean, default=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="forecasts")


class Citation(Base):
    __tablename__ = "citations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    report_id: Mapped[int] = mapped_column(ForeignKey("reports.id"), nullable=False)
    source_id: Mapped[int | None] = mapped_column(ForeignKey("sources.id"), nullable=True)

    citation_index: Mapped[int] = mapped_column(Integer, nullable=False)
    label: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str] = mapped_column(String(1000), nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    report = relationship("Report", back_populates="citations")
