from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.v1 import budgets, measurements, imports, purchases, auth, versions, evm

app = FastAPI(title="OFITEC API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(budgets.router, prefix="/api/v1/budgets", tags=["budgets"])
app.include_router(measurements.router, prefix="/api/v1/measurements", tags=["measurements"])
app.include_router(imports.router, prefix="/api/v1/imports", tags=["imports"])
app.include_router(purchases.router, prefix="/api/v1/purchases", tags=["purchases"])
app.include_router(versions.router, prefix="/api/v1/versions", tags=["versions"])
app.include_router(evm.router, prefix="/api/v1/evm", tags=["evm"])

@app.get("/health")
async def health():
    return {"status": "ok"}
