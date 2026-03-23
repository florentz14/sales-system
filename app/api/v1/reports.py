from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy.orm import Session

from app.analytics import charts, exports
from app.analytics.service import load_report_bundle
from app.api.deps import require_permission
from app.core import permissions as perms
from app.db.models.user import User
from app.db.session import get_db
from app.schemas.reports import (
    CustomerRankRow,
    DailySalesRow,
    ProductRankRow,
    ReportSummary,
    SalesKpis,
)

router = APIRouter(prefix="/reports", tags=["reports"])


@dataclass
class ReportFilters:
    days: int
    start_date: date | None
    end_date: date | None
    ranking_limit: int


def get_report_filters(
    days: int = Query(30, ge=1, le=366, description="Días hacia atrás si no hay rango"),
    start_date: date | None = Query(None, description="Inicio (YYYY-MM-DD)"),
    end_date: date | None = Query(None, description="Fin (YYYY-MM-DD)"),
    ranking_limit: int = Query(20, ge=1, le=100),
) -> ReportFilters:
    return ReportFilters(days, start_date, end_date, ranking_limit)


def _bundle(db: Session, f: ReportFilters) -> dict:
    return load_report_bundle(
        db,
        days=f.days,
        start=f.start_date,
        end=f.end_date,
        ranking_limit=f.ranking_limit,
    )


@router.get("/summary", response_model=ReportSummary)
def report_summary(
    db: Session = Depends(get_db),
    f: ReportFilters = Depends(get_report_filters),
    _: User = Depends(require_permission(perms.READ_REPORT)),
) -> ReportSummary:
    b = _bundle(db, f)
    return ReportSummary(
        start=b["start"],
        end=b["end"],
        period_label=b["period_label"],
        kpis=SalesKpis.model_validate(b["kpis"]),
        daily=[DailySalesRow.model_validate(r) for r in b["daily"]],
        products=[ProductRankRow.model_validate(r) for r in b["products"]],
        customers=[CustomerRankRow.model_validate(r) for r in b["customers"]],
    )


@router.get("/chart/sales")
def chart_sales_by_day(
    db: Session = Depends(get_db),
    f: ReportFilters = Depends(get_report_filters),
    _: User = Depends(require_permission(perms.READ_REPORT)),
) -> Response:
    b = _bundle(db, f)
    png = charts.sales_by_day_png(
        b["daily"],
        title=f"Ventas por día ({b['period_label']})",
    )
    return Response(content=png, media_type="image/png")


@router.get("/chart/products")
def chart_top_products(
    db: Session = Depends(get_db),
    f: ReportFilters = Depends(get_report_filters),
    _: User = Depends(require_permission(perms.READ_REPORT)),
) -> Response:
    b = _bundle(db, f)
    png = charts.top_products_png(
        b["products"],
        title=f"Top productos ({b['period_label']})",
        limit=min(15, f.ranking_limit),
    )
    return Response(content=png, media_type="image/png")


@router.get("/export/excel")
def export_excel(
    db: Session = Depends(get_db),
    f: ReportFilters = Depends(get_report_filters),
    _: User = Depends(require_permission(perms.READ_REPORT)),
) -> StreamingResponse:
    b = _bundle(db, f)
    data = exports.build_excel_bytes(
        daily=b["daily"],
        products=b["products"],
        customers=b["customers"],
        kpis=b["kpis"],
        period_label=b["period_label"],
    )
    fname = f"reporte_ventas_{date.today().isoformat()}.xlsx"
    return StreamingResponse(
        iter([data]),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )


@router.get("/export/pdf")
def export_pdf(
    db: Session = Depends(get_db),
    f: ReportFilters = Depends(get_report_filters),
    _: User = Depends(require_permission(perms.READ_REPORT)),
) -> StreamingResponse:
    b = _bundle(db, f)
    data = exports.build_pdf_bytes(
        daily=b["daily"],
        products=b["products"],
        customers=b["customers"],
        kpis=b["kpis"],
        period_label=b["period_label"],
    )
    fname = f"reporte_ventas_{date.today().isoformat()}.pdf"
    return StreamingResponse(
        iter([data]),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{fname}"'},
    )
