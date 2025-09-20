"""Servicios de exportación a Excel / PDF.

Exporta:
 - Presupuesto consolidado (capítulo, item, qty, unit, price, total)
 - Resumen de mediciones
 - Diff de versiones (added/removed/changed)
"""
from __future__ import annotations
from io import BytesIO
from decimal import Decimal
import pandas as pd
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from sqlalchemy.orm import Session
from app.db.models.budget import Chapter, Item
from app.db.models.project import Project
from app.db.models.measurement import Measurement
from app.db.models.versioning import BudgetVersionItem
from app.api.v1.versions import diff_logic


def export_budget_excel(db: Session, project_id: int) -> bytes:
    project = db.get(Project, project_id)
    if not project:
        raise ValueError("Proyecto no encontrado")
    rows = []
    chapters = db.query(Chapter).filter(Chapter.project_id == project_id).all()
    for ch in chapters:
        items = db.query(Item).filter(Item.chapter_id == ch.id).all()
        for it in items:
            total = (Decimal(str(it.quantity or 0)) * Decimal(str(it.price or 0))) if it.quantity and it.price else Decimal("0")
            rows.append({
                "Capítulo": ch.code,
                "Capítulo Nombre": ch.name,
                "Ítem Código": it.code,
                "Ítem Nombre": it.name,
                "Unidad": it.unit,
                "Cantidad": float(it.quantity or 0),
                "Precio Unit": float(it.price or 0),
                "Total": float(total)
            })
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Presupuesto")
    buffer.seek(0)
    return buffer.read()


def export_measurements_excel(db: Session, project_id: int) -> bytes:
    # Similar a /measurements/{project_id}/summary
    from app.db.models.budget import Item, Chapter
    rows = []
    q_items = db.query(Item).join(Chapter, Chapter.id == Item.chapter_id).filter(Chapter.project_id == project_id).all()
    for it in q_items:
        qty_total = sum(float(m.qty) for m in db.query(Measurement).filter(Measurement.item_id == it.id))
        rows.append({
            "Item Código": it.code,
            "Item Nombre": it.name,
            "Unidad": it.unit,
            "Cantidad Medida": qty_total,
            "Precio Unit": float(it.price or 0),
            "Valor": qty_total * float(it.price or 0)
        })
    df = pd.DataFrame(rows)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Mediciones")
    buffer.seek(0)
    return buffer.read()


def export_versions_diff_excel(db: Session, v_from: int, v_to: int) -> bytes:
    diff = diff_logic(db, v_from, v_to)
    rows_added = [{"code": c, "status": "added"} for c in diff["added"]]
    rows_removed = [{"code": c, "status": "removed"} for c in diff["removed"]]
    rows_changed = [{
        "code": c["code"],
        "qty_from": c["qty_from"],
        "qty_to": c["qty_to"],
        "pu_from": c["pu_from"],
        "pu_to": c["pu_to"],
        "delta_total": c["delta_total"],
        "status": "changed"
    } for c in diff["changed"]]
    df = pd.DataFrame(rows_added + rows_removed + rows_changed)
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Diff")
    buffer.seek(0)
    return buffer.read()


def export_budget_pdf(db: Session, project_id: int) -> bytes:
    project = db.get(Project, project_id)
    if not project:
        raise ValueError("Proyecto no encontrado")
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y = height - 40
    c.setFont("Helvetica-Bold", 14)
    c.drawString(40, y, f"Presupuesto Proyecto: {project.name}")
    y -= 30
    c.setFont("Helvetica", 9)
    headers = ["Cap", "Item", "Nombre", "Qty", "Unit", "PU", "Total"]
    c.drawString(40, y, " | ".join(headers))
    y -= 15
    chapters = db.query(Chapter).filter(Chapter.project_id == project_id).all()
    for ch in chapters:
        items = db.query(Item).filter(Item.chapter_id == ch.id).all()
        for it in items:
            total = (Decimal(str(it.quantity or 0)) * Decimal(str(it.price or 0))) if it.quantity and it.price else Decimal("0")
            line = [ch.code, it.code, it.name[:25], f"{float(it.quantity or 0):.2f}", it.unit, f"{float(it.price or 0):.2f}", f"{float(total):.2f}"]
            c.drawString(40, y, " | ".join(line))
            y -= 12
            if y < 60:
                c.showPage()
                y = height - 40
                c.setFont("Helvetica", 9)
    c.showPage(); c.save()
    buffer.seek(0)
    return buffer.read()
