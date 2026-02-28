from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Report
from app.schemas.report import ReportCreate, ReportSectionRegenerate
from app.tasks import generate_report_task


router = APIRouter(prefix="/api", tags=["reports"])


@router.post("/reports")
def create_report(payload: ReportCreate, db: Session = Depends(get_db)):
    report = Report(
        industry=payload.industry,
        geography=payload.geography,
        time_horizon=payload.time_horizon,
        depth=payload.depth,
        include_financial_forecast=payload.include_financial_forecast,
        include_competitive_landscape=payload.include_competitive_landscape,
        status="Queued",
        progress_message="Queued for processing",
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    generate_report_task.delay(report.id)
    return {"id": report.id, "status": report.status}


@router.get("/reports")
def list_reports(db: Session = Depends(get_db)):
    rows = db.execute(select(Report).order_by(Report.created_at.desc())).scalars().all()
    return rows


@router.get("/reports/{report_id}")
def get_report(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.get("/reports/{report_id}/status")
def get_report_status(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return {"id": report.id, "status": report.status, "message": report.progress_message}


@router.get("/reports/{report_id}/pdf")
def download_report_pdf(report_id: int, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report or not report.pdf_path:
        raise HTTPException(status_code=404, detail="PDF not available")

    pdf_path = Path(report.pdf_path)
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail="PDF file missing")

    return FileResponse(pdf_path, media_type="application/pdf", filename=f"insightforge_report_{report.id}.pdf")


@router.post("/reports/{report_id}/regenerate-section")
def regenerate_section(report_id: int, payload: ReportSectionRegenerate, db: Session = Depends(get_db)):
    report = db.get(Report, report_id)
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")

    report.status = "Queued"
    report.progress_message = f"Regenerating section: {payload.section_name}"
    db.add(report)
    db.commit()

    generate_report_task.delay(report.id)
    return {"id": report.id, "status": report.status, "message": report.progress_message}
