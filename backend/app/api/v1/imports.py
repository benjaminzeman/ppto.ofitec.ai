from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
import tempfile, os
from app.services.excel_io import import_budget_xlsx
from app.services.bc3_parser import import_budget_bc3, BC3ParseError

router = APIRouter()

@router.post("/excel")
async def import_excel(project_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".xlsx") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            project_id = import_budget_xlsx(db, tmp.name, project_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            os.unlink(tmp.name)  # type: ignore
        except Exception:
            pass
    return {"project_id": project_id}

@router.post("/bc3")
async def import_bc3(project_name: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
            tmp.write(await file.read())
            tmp.flush()
            project_id = import_budget_bc3(db, tmp.name, project_name)
    except (ValueError, BC3ParseError) as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        try:
            os.unlink(tmp.name)  # type: ignore
        except Exception:
            pass
    return {"project_id": project_id}
