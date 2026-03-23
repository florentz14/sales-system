from __future__ import annotations

from datetime import datetime
from io import BytesIO
from typing import Any, cast

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def build_excel_bytes(
    *,
    daily: list[dict[str, Any]],
    products: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    kpis: dict[str, Any],
    period_label: str,
) -> bytes:
    buf = BytesIO()
    # BytesIO es válido en tiempo de ejecución; los stubs de pandas exigen WriteExcelBuffer.
    with pd.ExcelWriter(cast(Any, buf), engine="openpyxl") as writer:
        pd.DataFrame([kpis]).to_excel(
            writer, sheet_name="Resumen", index=False
        )
        meta = pd.DataFrame([{"periodo": period_label, "generado": datetime.now().isoformat()}])
        meta.to_excel(writer, sheet_name="Metadatos", index=False)
        pd.DataFrame(daily).to_excel(writer, sheet_name="Ventas_diarias", index=False)
        pd.DataFrame(products).to_excel(writer, sheet_name="Productos", index=False)
        pd.DataFrame(customers).to_excel(writer, sheet_name="Clientes", index=False)
    buf.seek(0)
    return buf.getvalue()


def build_pdf_bytes(
    *,
    daily: list[dict[str, Any]],
    products: list[dict[str, Any]],
    customers: list[dict[str, Any]],
    kpis: dict[str, Any],
    period_label: str,
) -> bytes:
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        rightMargin=2 * cm,
        leftMargin=2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )
    styles = getSampleStyleSheet()
    story: list[Any] = [
        Paragraph("Reporte de ventas", styles["Title"]),
        Spacer(1, 0.5 * cm),
        Paragraph(f"<b>Periodo:</b> {period_label}", styles["Normal"]),
        Paragraph(
            f"<b>Facturas:</b> {kpis.get('invoice_count', 0)} &nbsp; "
            f"<b>Ingresos:</b> {kpis.get('total_revenue', 0):.2f} &nbsp; "
            f"<b>IVA:</b> {kpis.get('total_tax', 0):.2f} &nbsp; "
            f"<b>Ticket medio:</b> {kpis.get('avg_ticket', 0):.2f}",
            styles["Normal"],
        ),
        Spacer(1, 0.8 * cm),
        Paragraph("Ventas por día", styles["Heading2"]),
        Spacer(1, 0.2 * cm),
    ]

    if daily:
        tdata = [["Día", "Total", "Facturas"]] + [
            [r["day"], f"{r['total']:.2f}", str(r["invoices"])] for r in daily[:31]
        ]
    else:
        tdata = [["Sin filas en el periodo"]]
    tw = doc.width
    t = Table(tdata, colWidths=[tw * 0.35, tw * 0.35, tw * 0.2])
    t.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#eceff1")]),
            ]
        )
    )
    story.append(t)
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Top productos (ingreso líneas)", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    if products:
        pdata = [["Producto", "Uds.", "Ingreso"]] + [
            [r["name"][:40], str(r["units"]), f"{r['revenue']:.2f}"] for r in products[:15]
        ]
    else:
        pdata = [["Sin datos"]]
    tp = Table(pdata, colWidths=[tw * 0.5, tw * 0.15, tw * 0.25])
    tp.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(tp)
    story.append(Spacer(1, 0.6 * cm))
    story.append(Paragraph("Top clientes (total facturas)", styles["Heading2"]))
    story.append(Spacer(1, 0.2 * cm))

    if customers:
        cdata = [["Cliente", "Facturas", "Total"]] + [
            [r["name"][:40], str(r["invoices"]), f"{r['total']:.2f}"]
            for r in customers[:15]
        ]
    else:
        cdata = [["Sin datos"]]
    tc = Table(cdata, colWidths=[tw * 0.5, tw * 0.15, tw * 0.25])
    tc.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#37474f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
            ]
        )
    )
    story.append(tc)
    doc.build(story)
    buf.seek(0)
    return buf.getvalue()
