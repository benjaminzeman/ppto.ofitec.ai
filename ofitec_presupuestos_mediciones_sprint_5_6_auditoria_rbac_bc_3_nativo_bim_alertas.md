# OFITEC · Presupuestos/Mediciones – Sprint 5-6

En este Sprint avanzamos hacia **auditoría de operaciones**, **RBAC granular por proyecto**, **parser BC3 nativo (.bc3)**, **integración BIM-IFC para mediciones**, y **alertas automáticas** (WhatsApp + Grafana). Integra las dependencias descritas en la estrategia técnica OFITEC【77†source】.

---

## 0) Objetivos

- Auditoría: registro de cambios en presupuesto, mediciones y OC.
- RBAC avanzado: roles dinámicos a nivel de proyecto.
- Parser BC3 real: lectura nativa de archivos `.bc3` (formato estándar FIEBDC-3).
- BIM: importar mediciones desde modelos IFC y asociarlas a ítems.
- Alertas: desvíos de costo/plazo vía WhatsApp y métricas Prometheus.

---

## 1) Migraciones Alembic

``

```python
from alembic import op
import sqlalchemy as sa

revision = "0003_audit_rbac_bc3_bim"
down_revision = "0002_measurements_comparatives_versions"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        "audit_logs",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("entity", sa.String()),  # item|apu|measurement|po
        sa.Column("entity_id", sa.Integer),
        sa.Column("action", sa.String()),  # create|update|delete
        sa.Column("data", sa.JSON()),
        sa.Column("user_id", sa.Integer),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "user_project_roles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer),
        sa.Column("project_id", sa.Integer, sa.ForeignKey("projects.id", ondelete="CASCADE")),
        sa.Column("role", sa.String()),  # admin|pm|compras|lector
    )

def downgrade():
    op.drop_table("user_project_roles")
    op.drop_table("audit_logs")
```

---

## 2) Modelos

``

```python
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, JSON
from app.db.base import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    entity = Column(String)
    entity_id = Column(Integer)
    action = Column(String)
    data = Column(JSON)
    user_id = Column(Integer)
    created_at = Column(DateTime)
```

``

```python
from sqlalchemy import Column, Integer, String, ForeignKey
from app.db.base import Base

class UserProjectRole(Base):
    __tablename__ = "user_project_roles"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    role = Column(String)
```

---

## 3) Servicios

### Auditoría

``

```python
from app.db.models.audit import AuditLog
from sqlalchemy.orm import Session

def log_action(db: Session, project_id: int, entity: str, entity_id: int, action: str, data: dict, user_id: int):
    log = AuditLog(project_id=project_id, entity=entity, entity_id=entity_id, action=action, data=data, user_id=user_id)
    db.add(log); db.commit()
```

### RBAC

``

```python
from fastapi import HTTPException
from app.db.models.security import UserProjectRole
from sqlalchemy.orm import Session

def check_role(db: Session, user_id: int, project_id: int, allowed: list[str]):
    r = db.query(UserProjectRole).filter_by(user_id=user_id, project_id=project_id).first()
    if not r or r.role not in allowed:
        raise HTTPException(403, "No permission")
    return True
```

### Parser BC3 nativo

``

```python
# Lector nativo BC3 (texto plano, FIEBDC-3)
# Usa prefijos ~V, ~K, ~C, ~D, ~R para versiones, capítulos, descompuestos, recursos.

def parse_bc3(file_path: str):
    projects, chapters, items, resources, apus = [], [], [], [], []
    with open(file_path, encoding="latin-1") as f:
        for line in f:
            if line.startswith("~V"):
                pass  # versión
            elif line.startswith("~K"):
                code, name = line[2:].split("|")[:2]
                chapters.append({"code": code.strip(), "name": name.strip()})
            elif line.startswith("~C"):
                code, name, unit = line[2:].split("|")[:3]
                items.append({"code": code.strip(), "name": name.strip(), "unit": unit.strip()})
            elif line.startswith("~R"):
                code, name, unit, cost = line[2:].split("|")[:4]
                resources.append({"code": code, "name": name, "unit": unit, "unit_cost": float(cost)})
            elif line.startswith("~D"):
                parts = line[2:].split("|")
                apus.append({"item_code": parts[0], "res_code": parts[1], "coeff": float(parts[2])})
    return {"chapters": chapters, "items": items, "resources": resources, "apus": apus}
```

### BIM-IFC

``

```python
# Usa ifcopenshell (pip install ifcopenshell)
import ifcopenshell

def import_ifc_quantities(file_path: str):
    model = ifcopenshell.open(file_path)
    quantities = []
    for qto in model.by_type("IfcElementQuantity"):
        for q in qto.Quantities:
            if q.is_a("IfcQuantityVolume"):
                quantities.append({"element": qto.Name, "volume": q.VolumeValue})
            elif q.is_a("IfcQuantityLength"):
                quantities.append({"element": qto.Name, "length": q.LengthValue})
    return quantities
```

### Alertas (WhatsApp + Prometheus)

``

```python
import requests, os

WA_TOKEN = os.getenv("WA_TOKEN")
WA_PHONE_ID = os.getenv("WA_PHONE_ID")

def send_whatsapp(phone: str, message: str):
    url = f"https://graph.facebook.com/v16.0/{WA_PHONE_ID}/messages"
    headers = {"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"}
    data = {"messaging_product": "whatsapp", "to": phone, "type": "text", "text": {"body": message}}
    return requests.post(url, headers=headers, json=data).json()

# Exportar métrica a Prometheus (via pushgateway o /metrics endpoint)
```

---

## 4) API

``

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.db.models.audit import AuditLog

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.get("/{project_id}")
def list_logs(project_id: int, db: Session = Depends(get_db)):
    return db.query(AuditLog).filter_by(project_id=project_id).all()
```

``

```python
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.services.bc3_native import parse_bc3
import tempfile, os

router = APIRouter()

def get_db():
    db = SessionLocal(); yield db; db.close()

@router.post("/import")
async def import_bc3(project_id: int = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
        tmp.write(await file.read()); tmp.flush()
        parsed = parse_bc3(tmp.name)
    os.unlink(tmp.name)
    return {"parsed": parsed}
```

``

```python
from fastapi import APIRouter, UploadFile, File
from app.services.ifc_import import import_ifc_quantities
import tempfile, os

router = APIRouter()

@router.post("/import")
async def import_ifc(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".ifc") as tmp:
        tmp.write(await file.read()); tmp.flush()
        q = import_ifc_quantities(tmp.name)
    os.unlink(tmp.name)
    return {"quantities": q}
```

---

## 5) UI Next.js

- `/audit/[projectId]`: tabla de logs (quién, qué, cuándo).
- `/bc3/import`: formulario upload .bc3 + vista previa capítulos/partidas.
- `/ifc/import`: subir modelo IFC + tabla de quantities.
- Notificaciones en frontend cuando se dispara alerta (via websockets o polling /alerts).

---

## 6) Integración con Estrategia OFITEC

- **Auditoría** enlaza con ELK/Grafana (logs centralizados)【77†source】.
- **RBAC** se alinea con `ofitec_security` (roles dinámicos por proyecto)【77†source】.
- **Parser BC3** complementa importadores Excel previos.
- **BIM-IFC** se conecta con `site_management` para mediciones reales.
- **Alertas**: WhatsApp Cloud API + métricas Prometheus ya definidas【77†source】.

---

## 7) Checklist Sprint 5-6

-

---

## 8) Próximos pasos (Sprint 7+)

- Workflows de aprobación (PM → Gerente) integrados con auditoría.
- Dashboards unificados (finanzas + mediciones + riesgos).
- Integración completa con `project_financials` para proyecciones de caja.
- Alertas de IA (ai\_bridge) basadas en predicciones.
- Control documental (DocuChat + AI) ligado a partidas y versiones de presupuesto.

