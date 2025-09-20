# OFITEC · Presupuestos/Mediciones – Sprint 15-16

Este Sprint refuerza la **inteligencia ejecutiva** de OFITEC con reportes financieros avanzados, un simulador IA de factoring y tableros ejecutivos con histórico y forecast.

---

## 0) Objetivos
- **Reportes financieros avanzados**: export a Excel/PDF consolidado multi-proyecto.
- **Simulador IA de factoring**: recomendación automática del mejor proveedor/tasa.
- **Tablero ejecutivo**: comparativas históricas y forecast financiero.
- **Integración**: alimentar `ai_bridge` y `docuchat` para consultas inteligentes.

---

## 1) Migraciones Alembic
**`backend/alembic/versions/0008_reports_ai_forecast.py`**
```python
from alembic import op
import sqlalchemy as sa

revision = "0008_reports_ai_forecast"
down_revision = "0007_factoring_dashboards"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "financial_reports",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("type", sa.String()),  # excel|pdf
        sa.Column("file_ref", sa.String()),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

def downgrade():
    op.drop_table("financial_reports")
```

---

## 2) Modelos
**`backend/app/db/models/report.py`**
```python
from sqlalchemy import Column, Integer, ForeignKey, String, DateTime
from app.db.base import Base

class FinancialReport(Base):
    __tablename__ = "financial_reports"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    type = Column(String)
    file_ref = Column(String)
    created_at = Column(DateTime)
```

---

## 3) Servicios
**Reportes** – `backend/app/services/reports.py`
```python
import pandas as pd
from app.db.models.invoice import Invoice
from app.db.models.bank import BankTransaction

def generate_excel(db, project_id: int, path: str):
    invoices = db.query(Invoice).filter_by().all()
    txs = db.query(BankTransaction).filter_by(project_id=project_id).all()
    df_inv = pd.DataFrame([{ "id":i.id, "amount":float(i.amount or 0), "status": i.status } for i in invoices])
    df_tx = pd.DataFrame([{ "date":t.date, "amount":float(t.amount), "desc":t.description } for t in txs])
    with pd.ExcelWriter(path) as writer:
        df_inv.to_excel(writer, sheet_name="Facturas")
        df_tx.to_excel(writer, sheet_name="Transacciones")
    return path

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

def generate_pdf(db, project_id: int, path: str):
    c = canvas.Canvas(path, pagesize=A4)
    c.drawString(40,800,f"Reporte Financiero Proyecto {project_id}")
    c.showPage(); c.save(); return path
```

**Simulador IA Factoring** – `backend/app/services/ai_factoring.py`
```python
# Usa modelos ML/heurísticos simples + conexión ai_bridge
import random

PROVIDERS = ["BancoEstado Factoring","Santander Factoring","BCI Factoring"]

def recommend_provider(invoice_amount: float, days: int):
    # Simulación simple → IA real via ai_bridge
    rec = random.choice(PROVIDERS)
    rate = round(0.9 + random.random()*0.5,3)
    advance = invoice_amount * (1 - rate/100)
    return {"provider": rec, "rate": rate, "advance": round(advance,2)}
```

**Forecast** – `backend/app/services/forecast.py`
```python
from sqlalchemy.orm import Session
from app.db.models.invoice import Invoice
from datetime import datetime, timedelta

def forecast_cash(db: Session, months: int=6):
    invoices = db.query(Invoice).all()
    today = datetime.today()
    forecast = []
    for m in range(months):
        period = (today + timedelta(days=30*m)).strftime("%Y-%m")
        inflows = sum([float(i.amount or 0) for i in invoices if i.status=="accepted"])
        outflows = inflows * 0.8  # dummy ratio
        forecast.append({"period": period, "inflows": inflows, "outflows": outflows, "net": inflows-outflows})
    return forecast
```

---

## 4) API
**Reportes** – `backend/app/api/v1/reports.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.reports import generate_excel, generate_pdf
import tempfile

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/excel")
def excel(project_id: int, db: Session = Depends(get_db)):
    path = tempfile.mktemp(suffix=".xlsx")
    return {"file": generate_excel(db, project_id, path)}

@router.post("/pdf")
def pdf(project_id: int, db: Session = Depends(get_db)):
    path = tempfile.mktemp(suffix=".pdf")
    return {"file": generate_pdf(db, project_id, path)}
```

**IA Factoring** – `backend/app/api/v1/ai_factoring.py`
```python
from fastapi import APIRouter
from app.services.ai_factoring import recommend_provider

router = APIRouter()

@router.get("/recommend")
def recommend(amount: float, days: int):
    return recommend_provider(amount, days)
```

**Forecast** – `backend/app/api/v1/forecast.py`
```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.forecast import forecast_cash

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/cash")
def forecast_(months: int=6, db: Session = Depends(get_db)):
    return forecast_cash(db, months)
```

---

## 5) UI Next.js
- `/reports/[projectId]`: descargar Excel/PDF financiero.
- `/factoring/ai`: simulador con recomendación de proveedor.
- `/forecast/global`: gráfico de proyección de flujo de caja (línea inflows/outflows/net).

**Componentes**
- `ReportButtons.tsx`: botones para exportar Excel/PDF.
- `AIRecommender.tsx`: form (monto, días) + recomendación IA.
- `ForecastChart.tsx`: gráfico temporal inflows/outflows/net.

---

## 6) Integración OFITEC
- **Reportes** vinculados a `docuchat` para búsqueda textual en PDFs/Excels.
- **IA Factoring**: plugin sobre `ai_bridge` (predicciones avanzadas).
- **Forecast**: usa datos de invoices, riesgos y cash scenarios previos.
- **Dashboards ejecutivos**: integran histórico + proyecciones.

---

## 7) Checklist Sprint 15-16
- [ ] Migración 0008 aplicada.
- [ ] Export Excel/PDF operativo.
- [ ] Recomendador IA de factoring funcionando.
- [ ] Forecast cash global generado.
- [ ] UI con reportes, simulador y forecast.
- [ ] Tests Pytest para reportes, IA y forecast.
- [ ] Integración con auditoría y docuchat.

---

## 8) Próximos pasos (Sprint 17+)
- Integración contable tributaria (ERP externo).
- Firma digital de reportes/documentos.
- Dashboard ejecutivo multi-empresa.
- Predicciones IA de desvíos de caja vs mercado (benchmark).

