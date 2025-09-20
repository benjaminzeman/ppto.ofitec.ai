"""Parser simplificado de archivos BC3 (subset FIEBDC-3) para cargar presupuesto.

Formato asumido (simplificado) línea a línea, separado por punto y coma ';':
  C;CHAPTER_CODE;CHAPTER_NAME
  I;CHAPTER_CODE;ITEM_CODE;ITEM_NAME;UNIT;QUANTITY
  R;ITEM_CODE;RESOURCE_TYPE;RESOURCE_CODE;RESOURCE_NAME;COEFF;UNIT_COST

Se ignoran líneas vacías o que comienzan con '#'. Si aparece un código duplicado se reutiliza.
Este parser NO cubre la totalidad del estándar BC3, solo un subconjunto mínimo útil para el flujo inicial.

Devuelve estructura:
{
  "chapters": {code: {"code":..., "name":...}},
  "items": {item_code: {"chapter_code":..., "code":..., "name":..., "unit":..., "quantity": float, "apu": [ {resource...} ]}},
}
"""
from __future__ import annotations
from typing import Dict, Any
from decimal import Decimal


class BC3ParseError(Exception):
    pass


def read_bc3(path: str) -> dict[str, Any]:
    chapters: Dict[str, dict] = {}
    items: Dict[str, dict] = {}
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(";")]
            tag = parts[0].upper()
            try:
                if tag == "C":
                    _, ccode, cname = parts
                    chapters.setdefault(ccode, {"code": ccode, "name": cname})
                elif tag == "I":
                    _, ccode, icode, iname, unit, qty = parts
                    if ccode not in chapters:
                        chapters.setdefault(ccode, {"code": ccode, "name": ccode})
                    items.setdefault(icode, {
                        "chapter_code": ccode,
                        "code": icode,
                        "name": iname,
                        "unit": unit or "m2",
                        "quantity": float(qty or 0),
                        "apu": []
                    })
                elif tag == "R":
                    _, icode, rtype, rcode, rname, coeff, unit_cost = parts
                    if icode not in items:
                        # crear ítem fantasma si recurso aparece antes 
                        items[icode] = {
                            "chapter_code": "UNASSIGNED",
                            "code": icode,
                            "name": icode,
                            "unit": "m2",
                            "quantity": 0.0,
                            "apu": []
                        }
                    items[icode]["apu"].append({
                        "resource_type": rtype,
                        "resource_code": rcode,
                        "resource_name": rname,
                        "coeff": float(coeff or 0),
                        "unit_cost": float(unit_cost or 0)
                    })
                else:
                    # Ignorar etiquetas desconocidas
                    continue
            except ValueError as e:
                raise BC3ParseError(f"Error parseando línea: '{line}': {e}")
    return {"chapters": chapters, "items": items}


def validate_bc3_structure(data: dict[str, Any]):
    if not data["items"]:
        raise BC3ParseError("Archivo BC3 sin ítems")
    # Asegurar que cada item tenga APU (si no, dejar lista vacía aceptable)
    # Validaciones adicionales se pueden agregar aquí.


def import_budget_bc3(db, path: str, project_name: str):
    """Crea un nuevo proyecto a partir de un archivo BC3 ya parseado."""
    from app.db.models.project import Project
    from app.db.models.budget import Chapter, Item, Resource, APU
    from app.services.kpis import compute_item_price
    parsed = read_bc3(path)
    validate_bc3_structure(parsed)
    project = Project(name=project_name)
    db.add(project); db.flush()

    # Map chapter code to db id
    chapter_ids: dict[str, int] = {}
    for ccode, c in parsed["chapters"].items():
        ch = Chapter(project_id=project.id, code=ccode, name=c["name"])
        db.add(ch); db.flush()
        chapter_ids[ccode] = ch.id

    for icode, it in parsed["items"].items():
        chapter_code = it["chapter_code"]
        if chapter_code not in chapter_ids:
            # crear capítulo implícito
            ch = Chapter(project_id=project.id, code=chapter_code, name=chapter_code)
            db.add(ch); db.flush()
            chapter_ids[chapter_code] = ch.id
        item = Item(chapter_id=chapter_ids[chapter_code], code=icode, name=it["name"], unit=it["unit"], quantity=it["quantity"], price=0)
        db.add(item); db.flush()
        apu_payload = []
        for r in it["apu"]:
            from app.db.models.budget import Resource as ResModel
            res = ResModel(type=r["resource_type"], code=r["resource_code"], name=r["resource_name"], unit="u", unit_cost=r["unit_cost"])
            db.add(res); db.flush()
            db.add(APU(item_id=item.id, resource_id=res.id, coeff=r["coeff"]))
            apu_payload.append({"coeff": r["coeff"], "unit_cost": r["unit_cost"]})
        if apu_payload:
            item.price = compute_item_price(apu_payload)
    db.commit()
    return project.id

