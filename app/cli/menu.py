"""Menú CLI en español: CRUD de productos, clientes, facturas, inventario y proveedores."""

from __future__ import annotations

from pathlib import Path

from sqlalchemy import select
from sqlalchemy.orm import Session
from tabulate import tabulate  # pyright: ignore[reportMissingModuleSource]

from app.analytics import charts, exports
from app.analytics.service import load_report_bundle
from app.core.config import get_settings
from app.db.models.user import User
from app.db.session import SessionLocal
from app.schemas.customer import CustomerCreate, CustomerUpdate
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import (
    customer_service,
    invoice_service,
    inventory_service,
    product_service,
    supplier_service,
)


def _read_line(prompt: str, default: str | None = None) -> str:
    raw = input(prompt).strip()
    if not raw and default is not None:
        return default
    return raw


def _read_int(prompt: str, *, min_v: int | None = None) -> int | None:
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        print("  Introduce un número entero válido.")
        return None
    if min_v is not None and n < min_v:
        print(f"  El valor debe ser >= {min_v}.")
        return None
    return n


def _read_float(prompt: str, *, min_exclusive: float = 0) -> float | None:
    raw = input(prompt).strip()
    if not raw:
        return None
    try:
        x = float(raw)
    except ValueError:
        print("  Introduce un número válido.")
        return None
    if x <= min_exclusive:
        print(f"  El valor debe ser > {min_exclusive}.")
        return None
    return x


def _actor_id(db: Session) -> int | None:
    return db.scalar(
        select(User.id).where(
            User.username == "admin",
            User.deleted_at.is_(None),
        ).limit(1)
    )


def _session(fn) -> None:
    db = SessionLocal()
    try:
        fn(db)
    finally:
        db.close()


def _menu_products() -> None:
    while True:
        print(
            "\n--- Productos ---\n"
            "1 Listar   2 Ver   3 Crear   4 Editar   5 Eliminar   0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(_products_list)
        elif op == "2":
            pid = _read_int("ID producto: ", min_v=1)
            if pid is not None:
                _session(lambda db, i=pid: _product_show(db, i))
        elif op == "3":
            _session(_product_create)
        elif op == "4":
            pid = _read_int("ID producto: ", min_v=1)
            if pid is not None:
                _session(lambda db, i=pid: _product_edit(db, i))
        elif op == "5":
            pid = _read_int("ID producto: ", min_v=1)
            if pid is not None:
                _session(lambda db, i=pid: _product_delete(db, i))
        else:
            print("  Opción no válida.")


def _products_list(db: Session) -> None:
    rows = product_service.list_products(db)
    table = [
        [p.id, p.sku or "", p.name, f"{p.price:.2f}", stock]
        for p, stock in rows
    ]
    print(
        tabulate(
            table,
            headers=["ID", "SKU", "Nombre", "Precio", "Stock"],
            tablefmt="github",
        )
    )


def _product_show(db: Session, product_id: int) -> None:
    row = product_service.get_product(db, product_id)
    if row is None:
        print("  Producto no encontrado.")
        return
    p, stock = row
    print(
        tabulate(
            [
                ["ID", p.id],
                ["SKU", p.sku or ""],
                ["Nombre", p.name],
                ["Descripción", (p.description or "")[:200]],
                ["Precio", f"{p.price:.2f}"],
                ["Stock", stock],
            ],
            tablefmt="github",
        )
    )


def _product_create(db: Session) -> None:
    name = _read_line("Nombre: ")
    if not name:
        print("  El nombre es obligatorio.")
        return
    price = _read_float("Precio: ", min_exclusive=0)
    if price is None:
        return
    sku = _read_line("SKU (opcional): ") or None
    desc = _read_line("Descripción (opcional): ") or None
    stock = _read_int("Stock inicial [0]: ", min_v=0)
    if stock is None:
        stock = 0
    data = ProductCreate(
        name=name,
        price=price,
        sku=sku,
        description=desc,
        initial_stock=stock,
    )
    try:
        p, st = product_service.create_product(db, data, actor_id=_actor_id(db))
        print(f"  Creado producto id={p.id}, stock={st}.")
    except Exception as e:
        print(f"  Error: {e}")


def _product_edit(db: Session, product_id: int) -> None:
    row = product_service.get_product(db, product_id)
    if row is None:
        print("  Producto no encontrado.")
        return
    p, _ = row
    print(f"  Editando #{p.id} — vacío = no cambiar.")
    name = _read_line(f"Nombre [{p.name}]: ")
    sku_in = _read_line(f"SKU [{p.sku or ''}]: ")
    desc_in = _read_line(f"Descripción [{p.description or ''}]: ")
    price_in = input(f"Precio [{p.price}] (vacío = no cambiar): ").strip()
    upd = ProductUpdate()
    if name:
        upd.name = name
    if sku_in:
        upd.sku = sku_in
    if desc_in:
        upd.description = desc_in
    if price_in:
        try:
            pf = float(price_in)
            if pf > 0:
                upd.price = pf
            else:
                print("  Precio debe ser > 0.")
        except ValueError:
            print("  Precio ignorado (no válido).")
    if all(
        getattr(upd, f) is None for f in ("name", "price", "sku", "description")
    ):
        print("  Nada que actualizar.")
        return
    try:
        product_service.update_product(
            db, product_id, upd, actor_id=_actor_id(db)
        )
        print("  Actualizado.")
    except Exception as e:
        print(f"  Error: {e}")


def _product_delete(db: Session, product_id: int) -> None:
    if _read_line("¿Seguro? (s/N): ").lower() != "s":
        return
    try:
        ok = product_service.delete_product(
            db, product_id, actor_id=_actor_id(db)
        )
        print("  Eliminado." if ok else "  No encontrado.")
    except ValueError as e:
        print(f"  {e}")


def _menu_customers() -> None:
    while True:
        print(
            "\n--- Clientes ---\n"
            "1 Listar   2 Ver   3 Crear   4 Editar   5 Eliminar   0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(_customers_list)
        elif op == "2":
            cid = _read_int("ID cliente: ", min_v=1)
            if cid is not None:
                _session(lambda db, i=cid: _customer_show(db, i))
        elif op == "3":
            _session(_customer_create)
        elif op == "4":
            cid = _read_int("ID cliente: ", min_v=1)
            if cid is not None:
                _session(lambda db, i=cid: _customer_edit(db, i))
        elif op == "5":
            cid = _read_int("ID cliente: ", min_v=1)
            if cid is not None:
                _session(lambda db, i=cid: _customer_delete(db, i))
        else:
            print("  Opción no válida.")


def _customers_list(db: Session) -> None:
    rows = customer_service.list_customers(db)
    table = [[c.id, c.name, c.email or "", c.phone or ""] for c in rows]
    print(
        tabulate(
            table,
            headers=["ID", "Nombre", "Email", "Teléfono"],
            tablefmt="github",
        )
    )


def _customer_show(db: Session, customer_id: int) -> None:
    c = customer_service.get_customer(db, customer_id)
    if c is None:
        print("  Cliente no encontrado.")
        return
    print(
        tabulate(
            [
                ["ID", c.id],
                ["Nombre", c.name],
                ["Email", c.email or ""],
                ["Teléfono", c.phone or ""],
                ["Dirección", c.address or ""],
            ],
            tablefmt="github",
        )
    )


def _customer_create(db: Session) -> None:
    name = _read_line("Nombre: ")
    if not name:
        print("  El nombre es obligatorio.")
        return
    data = CustomerCreate(
        name=name,
        email=_read_line("Email (opcional): ") or None,
        phone=_read_line("Teléfono (opcional): ") or None,
        address=_read_line("Dirección (opcional): ") or None,
    )
    c = customer_service.create_customer(db, data, actor_id=_actor_id(db))
    print(f"  Creado cliente id={c.id}.")


def _customer_edit(db: Session, customer_id: int) -> None:
    c = customer_service.get_customer(db, customer_id)
    if c is None:
        print("  Cliente no encontrado.")
        return
    print("  Vacío = no cambiar.")
    name = _read_line(f"Nombre [{c.name}]: ")
    email = _read_line(f"Email [{c.email or ''}]: ")
    phone = _read_line(f"Teléfono [{c.phone or ''}]: ")
    address = _read_line(f"Dirección [{c.address or ''}]: ")
    upd = CustomerUpdate()
    if name:
        upd.name = name
    if email:
        upd.email = email
    if phone:
        upd.phone = phone
    if address:
        upd.address = address
    if all(
        getattr(upd, f) is None for f in ("name", "email", "phone", "address")
    ):
        print("  Nada que actualizar.")
        return
    customer_service.update_customer(
        db, customer_id, upd, actor_id=_actor_id(db)
    )
    print("  Actualizado.")


def _customer_delete(db: Session, customer_id: int) -> None:
    if _read_line("¿Seguro? (s/N): ").lower() != "s":
        return
    try:
        ok = customer_service.soft_delete_customer(
            db, customer_id, actor_id=_actor_id(db)
        )
        print("  Eliminado." if ok else "  No encontrado.")
    except ValueError as e:
        print(f"  {e}")


def _menu_invoices() -> None:
    while True:
        print(
            "\n--- Facturas ---\n"
            "1 Listar   2 Ver   3 Crear   4 Anular (soft delete)   0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(_invoices_list)
        elif op == "2":
            iid = _read_int("ID factura: ", min_v=1)
            if iid is not None:
                _session(lambda db, i=iid: _invoice_show(db, i))
        elif op == "3":
            _session(_invoice_create)
        elif op == "4":
            iid = _read_int("ID factura: ", min_v=1)
            if iid is not None:
                _session(lambda db, i=iid: _invoice_void(db, i))
        else:
            print("  Opción no válida.")


def _invoices_list(db: Session) -> None:
    rows = invoice_service.list_invoices(db, limit=200)
    table = [
        [
            i.id,
            i.invoice_number or "",
            i.status,
            i.customer_id,
            f"{i.subtotal:.2f}",
            f"{i.discount_amount:.2f}",
            f"{i.tax_rate:.1f}%",
            f"{i.tax_amount:.2f}",
            f"{i.total:.2f}",
        ]
        for i in rows
    ]
    print(
        tabulate(
            table,
            headers=[
                "ID",
                "Número",
                "Estado",
                "Cliente",
                "Subtotal",
                "Dto.",
                "IVA%",
                "IVA",
                "Total",
            ],
            tablefmt="github",
        )
    )


def _invoice_show(db: Session, invoice_id: int) -> None:
    inv = invoice_service.get_invoice(db, invoice_id)
    if inv is None:
        print("  Factura no encontrada.")
        return
    print(
        tabulate(
            [
                ["ID", inv.id],
                ["Número", inv.invoice_number or ""],
                ["Estado", inv.status],
                ["Cliente", inv.customer_id],
                ["Subtotal", f"{inv.subtotal:.2f}"],
                ["Descuento global", f"{inv.discount_amount:.2f}"],
                ["Tipo IVA (%)", f"{inv.tax_rate:.2f}"],
                ["Cuota IVA", f"{inv.tax_amount:.2f}"],
                ["Total", f"{inv.total:.2f}"],
                ["Notas", (inv.notes or "")[:120]],
            ],
            tablefmt="github",
        )
    )
    lines = [
        [
            li.id,
            li.product_id,
            li.quantity,
            f"{li.price:.2f}",
            f"{li.discount_percent:.1f}%",
        ]
        for li in inv.items
        if li.deleted_at is None
    ]
    if lines:
        print("\nLíneas:")
        print(
            tabulate(
                lines,
                headers=["Línea", "Producto", "Cant.", "P. unit.", "Dto.%"],
                tablefmt="github",
            )
        )


def _invoice_create(db: Session) -> None:
    cid = _read_int("ID cliente: ", min_v=1)
    if cid is None:
        return
    if customer_service.get_customer(db, cid) is None:
        print("  Cliente no encontrado.")
        return
    notes = _read_line("Notas (opcional): ") or None
    disc_global = _read_line("Descuento global (importe) [0]: ").strip()
    try:
        discount_amount = float(disc_global) if disc_global else 0.0
    except ValueError:
        print("  Descuento global inválido, se usa 0.")
        discount_amount = 0.0
    if discount_amount < 0:
        discount_amount = 0.0
    tax_in = _read_line("Tipo impositivo IVA % [0]: ").strip()
    try:
        tax_rate = float(tax_in) if tax_in else 0.0
    except ValueError:
        print("  IVA inválido, se usa 0.")
        tax_rate = 0.0
    if tax_rate < 0:
        tax_rate = 0.0
    if tax_rate > 100:
        tax_rate = 100.0
    items: list[dict] = []
    print(
        "Líneas: product_id cantidad [dto_%] "
        "(ej. 1 2 o 1 2 10 para 10% dto. en línea; vacío = terminar)"
    )
    while True:
        line = _read_line("Línea: ")
        if not line:
            break
        parts = line.split()
        if len(parts) not in (2, 3):
            print("  Formato: product_id cantidad [descuento_%]")
            continue
        try:
            pid, qty = int(parts[0]), int(parts[1])
            line_dto = float(parts[2]) if len(parts) == 3 else 0.0
        except ValueError:
            print("  Números inválidos.")
            continue
        if qty < 1:
            print("  Cantidad >= 1.")
            continue
        if line_dto < 0:
            line_dto = 0.0
        if line_dto > 100:
            line_dto = 100.0
        items.append(
            {
                "product_id": pid,
                "quantity": qty,
                "discount_percent": line_dto,
            }
        )
    if not items:
        print("  Debe haber al menos una línea.")
        return
    try:
        inv = invoice_service.create_invoice(
            db,
            cid,
            items,
            notes=notes,
            discount_amount=discount_amount,
            tax_rate=tax_rate,
            actor_id=_actor_id(db),
        )
        inv = invoice_service.get_invoice(db, inv.id)
        assert inv is not None
        print(f"  Factura creada id={inv.id} número={inv.invoice_number} total={inv.total:.2f}")
    except ValueError as e:
        print(f"  {e}")


def _invoice_void(db: Session, invoice_id: int) -> None:
    if _read_line("¿Anular factura? (s/N): ").lower() != "s":
        return
    ok = invoice_service.soft_delete_invoice(
        db, invoice_id, actor_id=_actor_id(db)
    )
    print("  Anulada." if ok else "  No encontrada.")


def _menu_inventory() -> None:
    while True:
        print(
            "\n--- Inventario ---\n"
            "1 Ver stock de todos   2 Fijar stock de un producto   0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(_products_list)
        elif op == "2":
            pid = _read_int("ID producto: ", min_v=1)
            if pid is not None:
                _session(lambda db, i=pid: _inventory_set(db, i))
        else:
            print("  Opción no válida.")


def _inventory_set(db: Session, product_id: int) -> None:
    if product_service.get_product(db, product_id) is None:
        print("  Producto no encontrado.")
        return
    qty = _read_int("Nueva cantidad en stock: ", min_v=0)
    if qty is None:
        return
    try:
        row = inventory_service.set_product_stock(
            db, product_id, qty, actor_id=_actor_id(db)
        )
        if row is None:
            print("  Sin fila de inventario activa para ese producto.")
        else:
            print(f"  Stock actualizado: {row.quantity}.")
    except ValueError as e:
        print(f"  {e}")


def _menu_suppliers() -> None:
    while True:
        print(
            "\n--- Proveedores ---\n"
            "1 Listar   2 Ver   3 Crear   4 Editar   5 Eliminar   0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(_suppliers_list)
        elif op == "2":
            sid = _read_int("ID proveedor: ", min_v=1)
            if sid is not None:
                _session(lambda db, i=sid: _supplier_show(db, i))
        elif op == "3":
            _session(_supplier_create)
        elif op == "4":
            sid = _read_int("ID proveedor: ", min_v=1)
            if sid is not None:
                _session(lambda db, i=sid: _supplier_edit(db, i))
        elif op == "5":
            sid = _read_int("ID proveedor: ", min_v=1)
            if sid is not None:
                _session(lambda db, i=sid: _supplier_delete(db, i))
        else:
            print("  Opción no válida.")


def _suppliers_list(db: Session) -> None:
    rows = supplier_service.list_suppliers(db)
    table = [[s.id, s.name, s.email or "", s.phone or ""] for s in rows]
    print(
        tabulate(
            table,
            headers=["ID", "Nombre", "Email", "Teléfono"],
            tablefmt="github",
        )
    )


def _supplier_show(db: Session, supplier_id: int) -> None:
    s = supplier_service.get_supplier(db, supplier_id)
    if s is None:
        print("  Proveedor no encontrado.")
        return
    print(
        tabulate(
            [
                ["ID", s.id],
                ["Nombre", s.name],
                ["Email", s.email or ""],
                ["Teléfono", s.phone or ""],
                ["Dirección", s.address or ""],
            ],
            tablefmt="github",
        )
    )


def _supplier_create(db: Session) -> None:
    name = _read_line("Nombre: ")
    if not name:
        print("  El nombre es obligatorio.")
        return
    s = supplier_service.create_supplier(
        db,
        name,
        email=_read_line("Email (opcional): ") or None,
        phone=_read_line("Teléfono (opcional): ") or None,
        address=_read_line("Dirección (opcional): ") or None,
        actor_id=_actor_id(db),
    )
    print(f"  Creado proveedor id={s.id}.")


def _supplier_edit(db: Session, supplier_id: int) -> None:
    s = supplier_service.get_supplier(db, supplier_id)
    if s is None:
        print("  Proveedor no encontrado.")
        return
    print("  Vacío = no cambiar.")
    name = _read_line(f"Nombre [{s.name}]: ")
    email = _read_line(f"Email [{s.email or ''}]: ")
    phone = _read_line(f"Teléfono [{s.phone or ''}]: ")
    address = _read_line(f"Dirección [{s.address or ''}]: ")
    if not any((name, email, phone, address)):
        print("  Nada que actualizar.")
        return
    supplier_service.update_supplier(
        db,
        supplier_id,
        name=name or None,
        email=email or None,
        phone=phone or None,
        address=address or None,
        actor_id=_actor_id(db),
    )
    print("  Actualizado.")


def _supplier_delete(db: Session, supplier_id: int) -> None:
    if _read_line("¿Seguro? (s/N): ").lower() != "s":
        return
    ok = supplier_service.soft_delete_supplier(
        db, supplier_id, actor_id=_actor_id(db)
    )
    print("  Eliminado." if ok else "  No encontrado.")


def _parse_report_days() -> int:
    raw = _read_line("Días hacia atrás [30]: ")
    if not raw:
        return 30
    try:
        return max(1, min(366, int(raw)))
    except ValueError:
        print("  Valor no válido, se usa 30.")
        return 30


def _ensure_reports_dir() -> Path:
    p = Path(get_settings().reports_output_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p


def _menu_reports() -> None:
    while True:
        print(
            "\n--- Reportes y análisis ---\n"
            "1 Resumen KPI + ventas diarias (tabla)\n"
            "2 Top productos y clientes (tablas)\n"
            "3 Gráfico ventas/día (PNG)\n"
            "4 Gráfico top productos (PNG)\n"
            "5 Exportar Excel (.xlsx)\n"
            "6 Exportar PDF\n"
            "0 Volver"
        )
        op = _read_line("Opción: ")
        if op == "0":
            return
        if op == "1":
            _session(lambda db: _reports_kpi_table(db))
        elif op == "2":
            _session(lambda db: _reports_rankings_table(db))
        elif op == "3":
            _session(lambda db: _reports_save_chart_sales(db))
        elif op == "4":
            _session(lambda db: _reports_save_chart_products(db))
        elif op == "5":
            _session(lambda db: _reports_save_excel(db))
        elif op == "6":
            _session(lambda db: _reports_save_pdf(db))
        else:
            print("  Opción no válida.")


def _reports_kpi_table(db: Session) -> None:
    days = _parse_report_days()
    b = load_report_bundle(db, days=days)
    k = b["kpis"]
    print(
        tabulate(
            [
                ["Facturas", k["invoice_count"]],
                ["Ingresos totales", f"{k['total_revenue']:.2f}"],
                ["IVA total", f"{k['total_tax']:.2f}"],
                ["Ticket medio", f"{k['avg_ticket']:.2f}"],
                ["Periodo", b["period_label"]],
            ],
            tablefmt="github",
        )
    )
    print("\nVentas por día:")
    print(
        tabulate(
            [[r["day"], f"{r['total']:.2f}", r["invoices"]] for r in b["daily"]],
            headers=["Día", "Total", "Facturas"],
            tablefmt="github",
        )
    )


def _reports_rankings_table(db: Session) -> None:
    days = _parse_report_days()
    lim_s = _read_line("Filas ranking [20]: ")
    try:
        lim = int(lim_s) if lim_s.strip() else 20
        lim = max(1, min(100, lim))
    except ValueError:
        lim = 20
    b = load_report_bundle(db, days=days, ranking_limit=lim)
    print("\nTop productos (ingreso líneas):")
    print(
        tabulate(
            [
                [r["product_id"], r["name"][:40], r["units"], f"{r['revenue']:.2f}"]
                for r in b["products"]
            ],
            headers=["ID", "Producto", "Uds.", "Ingreso"],
            tablefmt="github",
        )
    )
    print("\nTop clientes:")
    print(
        tabulate(
            [
                [r["customer_id"], r["name"][:40], r["invoices"], f"{r['total']:.2f}"]
                for r in b["customers"]
            ],
            headers=["ID", "Cliente", "Fact.", "Total"],
            tablefmt="github",
        )
    )


def _reports_save_chart_sales(db: Session) -> None:
    days = _parse_report_days()
    b = load_report_bundle(db, days=days)
    out = _ensure_reports_dir() / f"ventas_diarias_{b['period_label'].replace(' ', '_')}.png"
    data = charts.sales_by_day_png(b["daily"], title=f"Ventas ({b['period_label']})")
    out.write_bytes(data)
    print(f"  Guardado: {out.resolve()}")


def _reports_save_chart_products(db: Session) -> None:
    days = _parse_report_days()
    b = load_report_bundle(db, days=days)
    out = _ensure_reports_dir() / f"top_productos_{b['period_label'].replace(' ', '_')}.png"
    data = charts.top_products_png(b["products"], limit=12)
    out.write_bytes(data)
    print(f"  Guardado: {out.resolve()}")


def _reports_save_excel(db: Session) -> None:
    days = _parse_report_days()
    b = load_report_bundle(db, days=days)
    out = _ensure_reports_dir() / f"reporte_{b['period_label'].replace(' ', '_')}.xlsx"
    out.write_bytes(
        exports.build_excel_bytes(
            daily=b["daily"],
            products=b["products"],
            customers=b["customers"],
            kpis=b["kpis"],
            period_label=b["period_label"],
        )
    )
    print(f"  Guardado: {out.resolve()}")


def _reports_save_pdf(db: Session) -> None:
    days = _parse_report_days()
    b = load_report_bundle(db, days=days)
    out = _ensure_reports_dir() / f"reporte_{b['period_label'].replace(' ', '_')}.pdf"
    out.write_bytes(
        exports.build_pdf_bytes(
            daily=b["daily"],
            products=b["products"],
            customers=b["customers"],
            kpis=b["kpis"],
            period_label=b["period_label"],
        )
    )
    print(f"  Guardado: {out.resolve()}")


def run_cli() -> None:
    print("Sistema de ventas — menú CLI (Ctrl+C para salir).")
    while True:
        print(
            "\n=== MENÚ PRINCIPAL ===\n"
            "1 Productos\n"
            "2 Clientes\n"
            "3 Facturas\n"
            "4 Inventario\n"
            "5 Proveedores\n"
            "6 Reportes / gráficos / exportar\n"
            "0 Salir"
        )
        op = _read_line("Opción: ")
        if op == "0":
            print("Hasta luego.")
            return
        if op == "1":
            _menu_products()
        elif op == "2":
            _menu_customers()
        elif op == "3":
            _menu_invoices()
        elif op == "4":
            _menu_inventory()
        elif op == "5":
            _menu_suppliers()
        elif op == "6":
            _menu_reports()
        else:
            print("  Opción no válida.")


def main_menu() -> None:
    """Compatibilidad con entradas que llaman main_menu()."""
    run_cli()
