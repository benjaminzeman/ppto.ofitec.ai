from fastapi import APIRouter

router = APIRouter()

@router.get("/rank/{project_id}")
async def rank(project_id: int):
    return []
