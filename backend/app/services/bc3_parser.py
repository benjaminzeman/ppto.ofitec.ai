"""Parser BC3 extendido (FIEBDC-3) con soporte jerárquico y validaciones básicas.

Reglas implementadas:
- ~V: versión (ignorada para ahora, se puede almacenar metadata futura).
- ~K: capítulo (code|name)
- ~C: item (code|name|unit|<opcional otros campos>)
- ~R: recurso (code|name|unit|cost)
- ~D: descompuesto APU (item_code|res_code|coeff)

Validaciones básicas:
- Código capítulo único por proyecto (en carga actual in-memory antes de persistir).
- Item debe referenciar capítulo válido si se usa codificación jerárquica (ej: 1.1.1). (Placeholder simple: no enforced strictly, pero se podría extender).
- Recursos duplicados por code se consolidan (último costo prevalece).
- APU: ignora líneas cuyo item o recurso no se haya definido previamente.

Salida estructurada para proceso de importación a la BD.
"""
from __future__ import annotations
from typing import List, Dict, Any, cast

class BC3ParseResult:
    def __init__(self):
        self.chapters: List[Dict[str, Any]] = []
        self.items: List[Dict[str, Any]] = []
        self.resources: Dict[str, Dict[str, Any]] = {}
        self.apus: List[Dict[str, Any]] = []
        self.errors: List[str] = []

    def to_dict(self):
        return {
            "chapters": self.chapters,
            "items": self.items,
            "resources": list(self.resources.values()),
            "apus": self.apus,
            "errors": self.errors,
        }


def parse_bc3_extended(file_path: str) -> BC3ParseResult:
    res = BC3ParseResult()
    try:
        with open(file_path, encoding="latin-1") as f:
            for ln, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line or not line.startswith("~"):
                    continue
                prefix = line[:2]
                payload = line[2:]
                try:
                    if prefix == "~V":
                        # versión -> ignorar de momento
                        continue
                    elif prefix == "~K":  # Capítulo
                        parts = payload.split("|")
                        code, name = parts[0].strip(), (parts[1].strip() if len(parts) > 1 else "")
                        if any(c["code"] == code for c in res.chapters):
                            res.errors.append(f"Capítulo duplicado {code} (línea {ln})")
                        else:
                            res.chapters.append({"code": code, "name": name})
                    elif prefix == "~C":  # Item
                        parts = payload.split("|")
                        if len(parts) < 3:
                            res.errors.append(f"Item incompleto (línea {ln})")
                            continue
                        code, name, unit = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        res.items.append({"code": code, "name": name, "unit": unit})
                    elif prefix == "~R":  # Recurso
                        parts = payload.split("|")
                        if len(parts) < 4:
                            res.errors.append(f"Recurso incompleto (línea {ln})")
                            continue
                        rcode, rname, runit, rcost = parts[0].strip(), parts[1].strip(), parts[2].strip(), parts[3].strip()
                        try:
                            cost = float(rcost.replace(",", "."))
                        except ValueError:
                            cost = 0.0
                            res.errors.append(f"Costo recurso inválido {rcode} (línea {ln})")
                        res.resources[rcode] = {"code": rcode, "name": rname, "unit": runit, "unit_cost": cost}
                    elif prefix == "~D":  # Descompuesto APU
                        parts = payload.split("|")
                        if len(parts) < 3:
                            res.errors.append(f"APU incompleto (línea {ln})")
                            continue
                        item_code, res_code, coeff_raw = parts[0].strip(), parts[1].strip(), parts[2].strip()
                        try:
                            coeff = float(coeff_raw.replace(",", "."))
                        except ValueError:
                            coeff = 0.0
                            res.errors.append(f"Coeficiente inválido APU {item_code}-{res_code} (línea {ln})")
                        # Validar existencia previa
                        if not any(i["code"] == item_code for i in res.items):
                            res.errors.append(f"Item no definido para APU {item_code} (línea {ln})")
                            continue
                        if res_code not in res.resources:
                            res.errors.append(f"Recurso no definido para APU {res_code} (línea {ln})")
                            continue
                        res.apus.append({"item_code": item_code, "res_code": res_code, "coeff": coeff})
                except Exception as e:  # Captura robusta de parsing línea a línea
                    res.errors.append(f"Error línea {ln}: {e}")
    except FileNotFoundError:
        res.errors.append("Archivo no encontrado")
    return res
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
    """Importa un presupuesto desde un archivo BC3.

    Autodetección de formato:
      - Formato extendido (~K/~C/~R/~D) -> usa parse_bc3_extended
      - Formato simple (C/I/R separados por ;) -> usa read_bc3

    Reglas / Suposiciones adicionales para formato extendido:
      - Si un ítem no puede mapearse a un capítulo existente se asigna a capítulo implícito "GENERAL".
      - Quantity no está en el formato extendido actual -> se asigna 0 por defecto (futuro: derivar de mediciones externas).
      - Si existen errores de parseo pero hay al menos un ítem válido se continúa; si no hay ítems se lanza BC3ParseError.
    """
    from app.db.models.project import Project
    from app.db.models.budget import Chapter, Item, Resource, APU
    from app.services.kpis import compute_item_price

    # Detección rápida del formato leyendo primeras líneas
    is_extended = False
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            for _ in range(20):
                l = fh.readline()
                if not l:
                    break
                if l.startswith("~"):
                    is_extended = True
                    break
    except FileNotFoundError:
        raise BC3ParseError("Archivo BC3 no encontrado")

    project = Project(name=project_name)
    db.add(project); db.flush()

    if is_extended:
        result = parse_bc3_extended(path)
        # Crear capítulos declarados
        chapter_ids: dict[str, int] = {}
        for ch in result.chapters:
            code = ch["code"]
            chapter = Chapter(project_id=project.id, code=code, name=ch.get("name") or code)
            db.add(chapter); db.flush()
            chapter_ids[code] = cast(int, chapter.id)
        # Capítulo fallback
        if "GENERAL" not in chapter_ids:
            general = Chapter(project_id=project.id, code="GENERAL", name="GENERAL")
            db.add(general); db.flush()
            chapter_ids["GENERAL"] = cast(int, general.id)
        # Crear recursos primero (para map rápido por code)
        resource_ids: dict[str, int] = {}
        for rcode, r in result.resources.items():
            res = Resource(type="GEN", code=rcode, name=r.get("name") or rcode, unit=r.get("unit") or "u", unit_cost=r.get("unit_cost", 0.0))
            db.add(res); db.flush()
            resource_ids[rcode] = cast(int, res.id)
        # Crear ítems
        item_ids: dict[str, int] = {}
        for it in result.items:
            icode = it["code"]
            # Heurística de mapeo capítulo: prefijo antes del primer punto si coincide con capítulo existente
            chapter_code = "GENERAL"
            if "." in icode:
                pref = icode.split(".", 1)[0]
                if pref in chapter_ids:
                    chapter_code = pref
            # Si existe capítulo con mismo código que ítem (raro) preferirlo
            if icode in chapter_ids:
                chapter_code = icode
            item = Item(chapter_id=chapter_ids[chapter_code], code=icode, name=it.get("name") or icode, unit=it.get("unit") or "u", quantity=0, price=0)
            db.add(item); db.flush()
            item_ids[icode] = cast(int, item.id)
        # APU (descompuestos)
        for apu in result.apus:
            icode, rcode, coeff = apu["item_code"], apu["res_code"], apu["coeff"]
            if icode not in item_ids or rcode not in resource_ids:
                continue  # ya se registró error en parseo
            db.add(APU(item_id=item_ids[icode], resource_id=resource_ids[rcode], coeff=coeff))
        # Calcular precios ítem según APU
        from collections import defaultdict
        apu_map: dict[int, list[dict]] = defaultdict(list)
        from app.db.models.budget import APU as APUModel
        # Cargar de la sesión los APU recién agregados filtrando por los item_ids creados
        db.flush()
        apus_session = db.query(APUModel).filter(APUModel.item_id.in_(list(item_ids.values()))).all()  # type: ignore
        for a in apus_session:
            res_obj = db.query(Resource).filter(Resource.id == a.resource_id).first()
            if res_obj:
                apu_map[a.item_id].append({"coeff": a.coeff, "unit_cost": res_obj.unit_cost})
        for item_id, lines in apu_map.items():
            price = compute_item_price(lines)
            it_db = db.query(Item).filter(Item.id == item_id).first()
            if it_db:
                it_db.price = price  # type: ignore[assignment]
        if not result.items:
            raise BC3ParseError("Archivo BC3 extendido sin items válidos")
        db.commit()
        return project.id
    else:
        # Formato simple existente
        parsed = read_bc3(path)
        validate_bc3_structure(parsed)
        # Map chapter code to db id
        chapter_ids: dict[str, int] = {}
        for ccode, c in parsed["chapters"].items():
            ch = Chapter(project_id=project.id, code=ccode, name=c["name"])
            db.add(ch); db.flush()
            chapter_ids[ccode] = cast(int, ch.id)
        for icode, it in parsed["items"].items():
            chapter_code = it["chapter_code"]
            if chapter_code not in chapter_ids:
                # crear capítulo implícito
                ch = Chapter(project_id=project.id, code=chapter_code, name=chapter_code)
                db.add(ch); db.flush()
                chapter_ids[chapter_code] = cast(int, ch.id)
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
                # compute_item_price devuelve Decimal -> asignar directamente
                from typing import Any
                item.price = cast(Any, compute_item_price(apu_payload))
        db.commit()
        return project.id

