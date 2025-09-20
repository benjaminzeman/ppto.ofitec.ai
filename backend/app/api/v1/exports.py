from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.api.v1.auth import get_current_user
from app.services.exporting import (
    export_budget_excel, export_measurements_excel, export_versions_diff_excel, export_budget_pdf
)

router = APIRouter()


@router.get("/budget/{project_id}.xlsx")
def budget_excel(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        content = export_budget_excel(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=budget_{project_id}.xlsx"})


@router.get("/measurements/{project_id}.xlsx")
def measurements_excel(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    content = export_measurements_excel(db, project_id)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=measurements_{project_id}.xlsx"})


@router.get("/diff.xlsx")
def diff_excel(v_from: int, v_to: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    content = export_versions_diff_excel(db, v_from, v_to)
    return Response(content, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    headers={"Content-Disposition": f"attachment; filename=diff_{v_from}_{v_to}.xlsx"})


@router.get("/budget/{project_id}.pdf")
def budget_pdf(project_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        content = export_budget_pdf(db, project_id)
    except ValueError as e:
        raise HTTPException(404, str(e))
    return Response(content, media_type="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=budget_{project_id}.pdf"})
