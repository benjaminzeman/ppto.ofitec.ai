import tempfile
from sqlalchemy.orm import Session
from app.db.models.audit import UserProjectRole, AuditLog
from app.db.session import get_db

BC3_SAMPLE = """# Demo BC3
C;C1;Capitulo 1
I;C1;IT1;Item 1;m2;5
R;IT1;MAT;R1;Res 1;2;10
R;IT1;MO;R2;Res 2;0.5;40
"""


def test_import_bc3(client, auth_token):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
        tmp.write(BC3_SAMPLE.encode())
        tmp.flush()
        with open(tmp.name, "rb") as fh:
            files = {"file": ("test.bc3", fh.read(), "text/plain")}
        data = {"project_name": "Proyecto BC3"}
    r = client.post("/api/v1/imports/bc3", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    project_id = r.json()["project_id"]
    assert isinstance(project_id, int)

    # Listar roles del proyecto (debe existir admin)
    rroles = client.get(f"/api/v1/budgets/projects/{project_id}/roles", headers={"Authorization": f"Bearer {auth_token}"})
    assert rroles.status_code == 200
    roles = rroles.json()
    assert any(r["role"] == "admin" for r in roles)

    # Auditoría debe contener import_bc3
    raudit = client.get(f"/api/v1/budgets/projects/{project_id}/audit", headers={"Authorization": f"Bearer {auth_token}"})
    assert raudit.status_code == 200
    actions = {a["action"] for a in raudit.json()}
    assert "import_bc3" in actions
