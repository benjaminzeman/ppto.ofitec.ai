# OFITEC · Presupuestos/Mediciones – Sprint 21-22

Este Sprint apunta a la **gestión fiscal predictiva**: predicciones tributarias, riesgos fiscales con IA y reportes IFRS multi-empresa.

---

## 0) Objetivos
- **Predicciones tributarias**: IVA, PPM y Renta proyectados con AI.
- **Riesgos fiscales**: detección de anomalías y alertas proactivas.
- **Reportes IFRS**: estados financieros consolidados con normas internacionales.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0011_tax_ai_ifrs.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0011_tax_ai_ifrs"
down_revision = "0010_ai_multi_tax"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "ifrs_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("company_id", sa.Integer, sa.ForeignKey("companies.id", ondelete="CASCADE")),
        sa.Column("period", sa.String()),
        sa.Column("file_ref", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("ifrs_reports")
```

---

## 2) Modelos
**`backend/app/db/models/ifrs.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from app.db.base import Base

class IFRSReport(Base):
    __tablename__ = "ifrs_reports"
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey("companies.id", ondelete="CASCADE"))
    period = Column(String)
    file_ref = Column(String)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Predicciones tributarias** – `backend/app/services/tax_ai.py`
```python
import random

def predict_taxes(project_id: int, months: int=6):
    out = []
    for m in range(months):
        out.append({
            "month": m+1,
            "IVA": round(random.uniform(1000,5000),2),
            "PPM": round(random.uniform(500,2000),2),
            "Renta": round(random.uniform(2000,7000),2)
        })
    return out
```

**Riesgos fiscales** – `backend/app/services/fiscal_risk.py`
```python
import random

RISKS = ["Subdeclaración IVA","Retraso PPM","Factura no conciliada","Error Renta"]

def detect_risks():
    return [{"risk": r, "probability": round(random.random(),2)} for r in RISKS]
```

**Reportes IFRS** – `backend/app/services/ifrs.py`
```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
import tempfile

def generate_ifrs(company_id: int, period: str):
    path = tempfile.mktemp(suffix=".pdf")
    c = canvas.Canvas(path, pagesize=A4)
    c.drawString(40,800,f"Reporte IFRS {company_id} Periodo {period}")
    c.showPage(); c.save(); return path
```

---

## 4) API
**Predicciones tributarias** – `backend/app/api/v1/tax_ai.py`
```python
from fastapi import APIRouter
from app.services.tax_ai import predict_taxes

router = APIRouter()

@router.get("/predict")
def predict(project_id: int, months: int=6):
    return predict_taxes(project_id, months)
```

**Riesgos fiscales** – `backend/app/api/v1/fiscal_risk.py`
```python
from fastapi import APIRouter
from app.services.fiscal_risk import detect_risks

router = APIRouter()

@router.get("/detect")
def detect():
    return detect_risks()
```

**IFRS** – `backend/app/api/v1/ifrs.py`
```python
from fastapi import APIRouter
from app.services.ifrs import generate_ifrs

router = APIRouter()

@router.post("/generate")
def generate(company_id: int, period: str):
    return {"file": generate_ifrs(company_id, period)}
```

---

## 5) UI Next.js
- `/tax/predict`: tabla con proyección IVA/PPM/Renta.
- `/tax/risks`: lista de riesgos fiscales detectados.
- `/ifrs/[companyId]`: exportar reporte IFRS por periodo.

**Componentes**
- `TaxForecast.tsx`: gráfico barras IVA/PPM/Renta por mes.
- `FiscalRisks.tsx`: tabla con riesgos y probabilidad.
- `IFRSButton.tsx`: botón para generar PDF.

---

## 6) Integración OFITEC
- **Tax AI**: motor predictivo con `ai_bridge` sobre históricos reales.
- **Riesgos**: vinculados a alertas de cumplimiento.
- **IFRS**: reportes consolidados multi-empresa para directorio.
- **Docuchat**: consulta en lenguaje natural sobre reportes fiscales.

---

## 7) Checklist Sprint 21-22
- [ ] Migración 0011 aplicada.
- [ ] Predicciones tributarias generadas y visibles en UI.
- [ ] Riesgos fiscales detectados y alertados.
- [ ] Reportes IFRS exportados (PDF).
- [ ] Integración con ai_bridge y docuchat.
- [ ] Tests Pytest para tax_ai, riesgos e IFRS.

---

## 8) Próximos pasos (Sprint 23+)
- Análisis de sensibilidad tributaria (escenarios).
- Conexión directa con Tesorería (pago automático).
- Forecast IFRS consolidado multi-año.
- IA explicativa de riesgos fiscales (por qué/probabilidad).

