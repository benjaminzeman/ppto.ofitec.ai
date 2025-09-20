#!/usr/bin/env python
"""Seed de datos demo para presupuesto básico."""
import os
from sqlalchemy.orm import Session
from sqlalchemy import create_engine
from app.db.models.project import Project
from app.db.models.budget import Chapter, Item, Resource, APU
from app.db.base import Base

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
engine = create_engine(DATABASE_URL, pool_pre_ping=True)

session = Session(bind=engine)

def seed():
    proj = Project(name="Proyecto Demo", currency="CLP")
    session.add(proj); session.flush()
    ch1 = Chapter(project_id=proj.id, code="C01", name="Obras Preliminares")
    session.add(ch1); session.flush()
    it1 = Item(chapter_id=ch1.id, code="IT-001", name="Excavación", unit="m3", quantity=100, price=0)
    session.add(it1); session.flush()
    r1 = Resource(type="MO", code="R-MO-01", name="Operario", unit="h", unit_cost=5000)
    session.add(r1); session.flush()
    session.add(APU(item_id=it1.id, resource_id=r1.id, coeff=0.2))
    it1.price = 0.2 * 5000
    session.commit()
    print("Seed completado. Proyecto ID:", proj.id)

if __name__ == "__main__":
    seed()
