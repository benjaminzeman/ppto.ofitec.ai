from fastapi import FastAPI

from app.api.v1 import workflows as workflows_router

app = FastAPI()

app.include_router(workflows_router.router, prefix="/api/v1/workflows", tags=["workflows"])