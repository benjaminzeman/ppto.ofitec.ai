"""Importación / exportación Excel para Presupuestos.

Formato esperado columnas (header exacto):
CapituloCodigo,CapituloNombre,PartidaCodigo,PartidaNombre,Unidad,Cantidad,RecursoTipo,RecursoCodigo,RecursoNombre,Coef,CostoUnitRecurso
"""
from sqlalchemy.orm import Session
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from app.services.kpis import compute_item_price
import pandas as pd

BUDGET_COLUMNS = [
	"CapituloCodigo","CapituloNombre","PartidaCodigo","PartidaNombre","Unidad","Cantidad",
	"RecursoTipo","RecursoCodigo","RecursoNombre","Coef","CostoUnitRecurso"
]

def import_budget_xlsx(db: Session, file_path: str, project_name: str) -> int:
	df = pd.read_excel(file_path)
	missing = [c for c in BUDGET_COLUMNS if c not in df.columns]
	if missing:
		raise ValueError(f"Faltan columnas en Excel: {missing}")
	df = df[BUDGET_COLUMNS]
	project = Project(name=project_name)
	db.add(project); db.flush()
	# Agrupamos por Capitulo + Partida para construir estructura
	for (ccod, cnom, pcod, pnom, unit), grp in df.groupby([
		"CapituloCodigo","CapituloNombre","PartidaCodigo","PartidaNombre","Unidad"
	]):
		chapter = Chapter(project_id=project.id, code=ccod, name=cnom)
		db.add(chapter); db.flush()
		item = Item(chapter_id=chapter.id, code=pcod, name=pnom, unit=unit, quantity=float(grp.iloc[0]["Cantidad"] or 0), price=0)
		db.add(item); db.flush()
		apu_payload = []
		for _, r in grp.iterrows():
			res = Resource(type=r.RecursoTipo, code=r.RecursoCodigo, name=r.RecursoNombre, unit="u", unit_cost=float(r.CostoUnitRecurso))
			db.add(res); db.flush()
			db.add(APU(item_id=item.id, resource_id=res.id, coeff=float(r.Coef)))
			apu_payload.append({"coeff": float(r.Coef), "unit_cost": float(r.CostoUnitRecurso)})
		item.price = compute_item_price(apu_payload)
	db.commit()
	return project.id

