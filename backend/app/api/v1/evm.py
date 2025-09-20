from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.project import Project
from app.db.models.versioning import BudgetVersion, BudgetVersionItem
from app.db.models.budget import Item, Chapter
from app.db.models.measurement import Measurement
from decimal import Decimal, DivisionByZero

router = APIRouter()


def _get_baseline_version(db: Session, project: Project):
    if not project.baseline_version_id:
        raise HTTPException(400, "Proyecto sin baseline definida")
    return db.get(BudgetVersion, project.baseline_version_id)


@router.get("/{project_id}/summary")
def evm_summary(project_id: int, db: Session = Depends(get_db)):
    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(404, "Proyecto no encontrado")
    baseline = _get_baseline_version(db, project)
    # Obtener líneas baseline
    bl_items = db.query(BudgetVersionItem).filter(BudgetVersionItem.version_id == baseline.id).all()
    bl_map = {b.item_code: b for b in bl_items}

    # Costo planificado total (BAC)
    BAC = Decimal("0")
    for b in bl_items:
        qty = Decimal(str(b.qty or 0))
        pu = Decimal(str(b.unit_price or 0))
        BAC += qty * pu

    # Actual (ítems vivos actuales)
    current_items = db.query(Item).join(Chapter, Chapter.id == Item.chapter_id).filter(Chapter.project_id == project_id).all()
    AC = Decimal("0")  # Actual Cost usando precio actual * qty medida
    EV = Decimal("0")  # Earned Value
    PV = BAC            # Simplificación: PV = BAC (sin distribución temporal todavía)

    for it in current_items:
        measured_qty = sum(Decimal(str(m.qty)) for m in db.query(Measurement).filter(Measurement.item_id == it.id))
        price_current = Decimal(str(it.price or 0))
        AC += measured_qty * price_current
        if it.code in bl_map:
            bl_line = bl_map[it.code]
            bl_qty = Decimal(str(bl_line.qty or 0))
            bl_price = Decimal(str(bl_line.unit_price or 0))
            earned_qty = measured_qty if measured_qty < bl_qty else bl_qty
            EV += earned_qty * bl_price

    CPI = (EV / AC) if AC > 0 else None
    SPI = (EV / PV) if PV > 0 else None
    ETC = (BAC - EV) / CPI if CPI and CPI != 0 else None
    EAC = AC + ETC if ETC is not None else None

    def _d(val):
        return float(val) if val is not None else None

    return {
        "project_id": project_id,
        "baseline_version_id": project.baseline_version_id,
        "BAC": _d(BAC),
        "AC": _d(AC),
        "EV": _d(EV),
        "PV": _d(PV),
        "CPI": _d(CPI),
        "SPI": _d(SPI),
        "ETC": _d(ETC),
        "EAC": _d(EAC)
    }
