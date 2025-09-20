from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from app.services.kpis import compute_item_price

router = APIRouter()

class ProjectIn(BaseModel):
    name: str
    currency: str = "CLP"

@router.get("/projects")
async def list_projects(db: Session = Depends(get_db)):
    return db.query(Project).all()

@router.post("/projects")
async def create_project(p: ProjectIn, db: Session = Depends(get_db)):
    obj = Project(name=p.name, currency=p.currency)
    db.add(obj)
    db.commit(); db.refresh(obj)
    return obj

class ChapterIn(BaseModel):
    project_id: int
    code: str
    name: str

@router.post("/chapters")
async def create_chapter(c: ChapterIn, db: Session = Depends(get_db)):
    obj = Chapter(**c.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

class ItemIn(BaseModel):
    chapter_id: int
    code: str
    name: str
    unit: str = "m2"
    quantity: float = 0

@router.post("/items")
async def create_item(i: ItemIn, db: Session = Depends(get_db)):
    obj = Item(**i.dict())
    db.add(obj); db.commit(); db.refresh(obj)
    return obj

class APULineIn(BaseModel):
    resource_code: str
    resource_name: str
    resource_type: str
    unit: str = "u"
    unit_cost: float
    coeff: float

@router.post("/items/{item_id}/apu")
async def set_apu(item_id: int, lines: list[APULineIn], db: Session = Depends(get_db)):
    item = db.get(Item, item_id)
    if not item:
        raise HTTPException(404, "Item not found")
    apu_payload = []
    for l in lines:
        r = db.query(Resource).filter(Resource.code==l.resource_code).first()
        if not r:
            r = Resource(code=l.resource_code, name=l.resource_name, type=l.resource_type, unit=l.unit, unit_cost=l.unit_cost)
            db.add(r); db.flush()
        apu = APU(item_id=item.id, resource_id=r.id, coeff=l.coeff)
        db.add(apu)
        apu_payload.append({"coeff": l.coeff, "unit_cost": l.unit_cost})
    item.price = compute_item_price(apu_payload)
    db.commit(); db.refresh(item)
    return {"item_id": item.id, "price": str(item.price), "lines": len(lines)}
