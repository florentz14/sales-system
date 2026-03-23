from __future__ import annotations

from io import BytesIO
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

sns.set_theme(style="whitegrid", palette="deep")


def sales_by_day_png(daily: list[dict[str, Any]], *, title: str = "Ventas por día") -> bytes:
    if not daily:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "Sin datos en el periodo", ha="center", va="center")
        ax.axis("off")
    else:
        days = [d["day"] for d in daily]
        totals = [d["total"] for d in daily]
        fig, ax = plt.subplots(figsize=(max(8, len(days) * 0.35), 4))
        ax.bar(range(len(days)), totals, color="#2e7d32")
        ax.set_xticks(range(len(days)))
        ax.set_xticklabels(days, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Total (moneda)")
        ax.set_title(title)
        ax.yaxis.grid(True, linestyle=":", alpha=0.6)
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()


def top_products_png(
    products: list[dict[str, Any]],
    *,
    title: str = "Top productos por ingreso",
    limit: int = 10,
) -> bytes:
    rows = products[:limit]
    if not rows:
        fig, ax = plt.subplots(figsize=(8, 3))
        ax.text(0.5, 0.5, "Sin datos en el periodo", ha="center", va="center")
        ax.axis("off")
    else:
        names = [r["name"][:28] + ("…" if len(r["name"]) > 28 else "") for r in rows]
        rev = [r["revenue"] for r in rows]
        fig, ax = plt.subplots(figsize=(8, max(3, len(rows) * 0.45)))
        y = range(len(names))
        ax.barh(y, rev, color="#1565c0")
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=9)
        ax.invert_yaxis()
        ax.set_xlabel("Ingreso (líneas de factura)")
        ax.set_title(title)
        ax.xaxis.grid(True, linestyle=":", alpha=0.6)
    buf = BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    return buf.getvalue()
