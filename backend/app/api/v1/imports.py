from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.session import get_db
import tempfile, os

router = APIRouter()

@router.post("/excel")
async def import_excel(project_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    # TODO: implementar importación real
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
        tmp.write(await file.read())
        tmp.flush()
    os.unlink(tmp.name)
    return {"status": "pending", "project_name": project_name}
