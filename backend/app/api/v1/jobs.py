from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.jobs import enqueue_job, get_job_status
from app.services.excel_io import import_budget_xlsx
from app.services.bc3_parser import import_budget_bc3
from app.services.exporting import export_budget_excel, export_measurements_excel, export_versions_diff_excel, export_budget_pdf
from app.db.models.job import Job
import os

router = APIRouter()

@router.post("/import/excel")
def queue_import_excel(project_name: str, file_path: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "import_excel", import_budget_xlsx, file_path=file_path, project_name=project_name)
    return {"job_id": job.id, "rq_id": job.rq_id}

@router.post("/import/bc3")
def queue_import_bc3(project_name: str, file_path: str, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "import_bc3", import_budget_bc3, file_path=file_path, project_name=project_name)
    return {"job_id": job.id, "rq_id": job.rq_id}

@router.post("/export/budget/{project_id}")
def queue_export_budget(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "export_budget_excel", export_budget_excel, project_id=project_id)
    return {"job_id": job.id}

@router.post("/export/budget_pdf/{project_id}")
def queue_export_budget_pdf(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "export_budget_pdf", export_budget_pdf, project_id=project_id)
    return {"job_id": job.id}

@router.post("/export/measurements/{project_id}")
def queue_export_measurements(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "export_measurements_excel", export_measurements_excel, project_id=project_id)
    return {"job_id": job.id}

@router.post("/export/diff")
def queue_export_diff(v_from: int, v_to: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job = enqueue_job(db, "export_versions_diff_excel", export_versions_diff_excel, v_from=v_from, v_to=v_to)
    return {"job_id": job.id}

@router.get("/{job_id}")
def job_status(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job: Job | None = get_job_status(db, job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado")
    return {"id": job.id, "type": job.type, "status": job.status, "error": job.error, "result_path": job.result_path}

@router.get("/{job_id}/download")
def job_download(job_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    job: Job | None = get_job_status(db, job_id)
    if not job:
        raise HTTPException(404, "Job no encontrado")
    if job.status != "finished" or not job.result_path or not os.path.exists(job.result_path):
        raise HTTPException(400, "Resultado no disponible")
    # Heurística de media-type básica
    if job.result_path.endswith('.xlsx'):
        media_type = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    elif job.result_path.endswith('.pdf'):
        media_type = 'application/pdf'
    else:
        media_type = 'application/octet-stream'
    with open(job.result_path, 'rb') as f:
        data = f.read()
    filename = os.path.basename(job.result_path)
    return Response(data, media_type=media_type, headers={"Content-Disposition": f"attachment; filename={filename}"})
