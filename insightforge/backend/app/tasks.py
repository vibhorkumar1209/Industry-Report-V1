from __future__ import annotations

from pathlib import Path

from sqlalchemy import delete

from app.agents.analysis_agent import AnalysisAgent
from app.agents.cross_validation_agent import CrossValidationAgent
from app.agents.financial_model_agent import FinancialModelAgent
from app.agents.report_composer_agent import ReportComposerAgent
from app.agents.research_agent import ResearchAgent
from app.agents.scraper_agent import ScraperAgent
from app.celery_app import celery_app
from app.config import settings
from app.database import SessionLocal
from app.models import Citation, ExtractedInsight, Forecast, Report, Source
from app.services.pdf_service import write_pdf
from app.utils.markdown_utils import markdown_to_html


def _set_report_status(db, report: Report, status: str, message: str) -> None:
    report.status = status
    report.progress_message = message
    db.add(report)
    db.commit()


def run_report_pipeline(report_id: int) -> None:
    _generate_report_impl(report_id)


@celery_app.task(name="app.tasks.generate_report_task")
def generate_report_task(report_id: int) -> None:
    _generate_report_impl(report_id)


def _generate_report_impl(report_id: int) -> None:
    db = SessionLocal()
    try:
        report = db.get(Report, report_id)
        if not report:
            return

        _set_report_status(db, report, "Running", "Researching sources")

        research_agent = ResearchAgent()
        scraper_agent = ScraperAgent()
        analysis_agent = AnalysisAgent()
        validation_agent = CrossValidationAgent()
        financial_agent = FinancialModelAgent()
        composer_agent = ReportComposerAgent()

        sources_payload = research_agent.run(report.industry, report.geography, limit=settings.max_sources)

        db.execute(delete(Source).where(Source.report_id == report.id))
        db.execute(delete(ExtractedInsight).where(ExtractedInsight.report_id == report.id))
        db.execute(delete(Forecast).where(Forecast.report_id == report.id))
        db.execute(delete(Citation).where(Citation.report_id == report.id))
        db.commit()

        persisted_sources: list[Source] = []
        for src in sources_payload[: settings.max_sources]:
            scraped = scraper_agent.run(src["url"])
            source = Source(
                report_id=report.id,
                title=src["title"],
                url=src["url"],
                domain=src.get("domain", ""),
                published_at=src.get("published_at", ""),
                raw_text=scraped["raw_text"],
                cleaned_text=scraped["cleaned_text"],
                relevance_score=src.get("relevance_score", 0.5),
            )
            db.add(source)
            db.flush()
            persisted_sources.append(source)

        _set_report_status(db, report, "Running", "Analyzing source documents")

        all_insights: list[dict] = []
        for source in persisted_sources:
            insight = analysis_agent.run(source.cleaned_text, report.industry, report.geography)
            all_insights.append(insight)
            db.add(
                ExtractedInsight(
                    report_id=report.id,
                    source_id=source.id,
                    market_size_usd_billion=insight.get("market_size_usd_billion"),
                    cagr_percent=insight.get("cagr_percent"),
                    drivers=insight.get("drivers", []),
                    restraints=insight.get("restraints", []),
                    trends=insight.get("trends", []),
                    key_companies=insight.get("key_companies", []),
                    regulatory_notes=insight.get("regulatory_notes", []),
                    confidence_score=insight.get("confidence_score", 0.6),
                    extracted_payload=insight,
                )
            )

        consensus = validation_agent.run(all_insights)

        _set_report_status(db, report, "Running", "Building financial forecast")

        forecast = financial_agent.run(
            market_size=consensus.get("consensus_market_size_usd_billion"),
            cagr_percent=consensus.get("consensus_cagr_percent"),
            years=5,
        )
        db.add(
            Forecast(
                report_id=report.id,
                base_year=forecast["base_year"],
                base_value=forecast["base_value"],
                cagr_percent=forecast["cagr_percent"],
                years=forecast["years"],
                table_json=forecast["table"],
                estimated=forecast["estimated"],
            )
        )

        _set_report_status(db, report, "Running", "Composing report")

        source_dicts = [
            {"title": s.title, "url": s.url, "domain": s.domain, "published_at": s.published_at}
            for s in persisted_sources
        ]

        compose_result = composer_agent.run(
            report_input={
                "industry": report.industry,
                "geography": report.geography,
                "time_horizon": report.time_horizon,
                "depth": report.depth,
                "include_financial_forecast": report.include_financial_forecast,
                "include_competitive_landscape": report.include_competitive_landscape,
            },
            sources=source_dicts,
            insights=all_insights,
            consensus=consensus,
            forecast=forecast,
        )
        markdown_report = compose_result["markdown"]
        visuals_payload = compose_result["visuals"]

        html_report = markdown_to_html(markdown_report)

        reports_dir = Path(settings.reports_dir)
        reports_dir.mkdir(parents=True, exist_ok=True)
        pdf_path = reports_dir / f"report_{report.id}.pdf"
        md_path = reports_dir / f"report_{report.id}.md"
        html_path = reports_dir / f"report_{report.id}.html"

        md_path.write_text(markdown_report, encoding="utf-8")
        html_path.write_text(html_report, encoding="utf-8")
        generated_pdf_path = write_pdf(html_report, str(pdf_path))

        for idx, src in enumerate(persisted_sources, start=1):
            db.add(
                Citation(
                    report_id=report.id,
                    source_id=src.id,
                    citation_index=idx,
                    label=src.title,
                    url=src.url,
                )
            )

        report.markdown_content = markdown_report
        report.html_content = html_report
        report.pdf_path = generated_pdf_path
        report.metadata_json = {
            "consensus": consensus,
            "forecast": forecast,
            "source_count": len(persisted_sources),
            "visuals": visuals_payload,
        }
        _set_report_status(db, report, "Complete", "Report generated successfully")

    except Exception as exc:
        if report_id:
            report = db.get(Report, report_id)
            if report:
                report.status = "Failed"
                report.progress_message = f"Generation failed: {str(exc)[:200]}"
                db.add(report)
                db.commit()
        raise
    finally:
        db.close()
