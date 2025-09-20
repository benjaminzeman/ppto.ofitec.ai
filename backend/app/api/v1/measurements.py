from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db

router = APIRouter()

@router.get("/{project_id}/summary")
async def summary(project_id: int, db: Session = Depends(get_db)):
    # Placeholder: devolver lista vacía hasta implementar servicio
    return []
