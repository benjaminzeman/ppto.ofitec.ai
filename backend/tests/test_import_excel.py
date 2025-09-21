import io
import pandas as pd


def build_excel_file():
    df = pd.DataFrame([
        {
            "CapituloCodigo": "C1", "CapituloNombre": "Cap 1", "PartidaCodigo": "IT1", "PartidaNombre": "Item 1",
            "Unidad": "m2", "Cantidad": 10,
            "RecursoTipo": "MAT", "RecursoCodigo": "R1", "RecursoNombre": "Recurso 1", "Coef": 2, "CostoUnitRecurso": 5
        },
        {
            "CapituloCodigo": "C1", "CapituloNombre": "Cap 1", "PartidaCodigo": "IT1", "PartidaNombre": "Item 1",
            "Unidad": "m2", "Cantidad": 10,
            "RecursoTipo": "MO", "RecursoCodigo": "R2", "RecursoNombre": "Recurso 2", "Coef": 0.5, "CostoUnitRecurso": 40
        }
    ])
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    buf.seek(0)
    return buf


def test_import_excel_endpoint(client, auth_token):
    excel_content = build_excel_file().read()
    files = {"file": ("test.xlsx", excel_content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    data = {"project_name": "Proyecto Excel"}
    r = client.post("/api/v1/imports/excel", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    pid = r.json()["project_id"]
    assert isinstance(pid, int)

    # Verificar rol asignado automáticamente (admin)
    r_roles = client.get(f"/api/v1/budgets/projects/{pid}/roles", headers={"Authorization": f"Bearer {auth_token}"})
    assert r_roles.status_code == 200
    roles = r_roles.json()
    assert any(r["role"] == "admin" for r in roles)

    # Verificar que existe registro de auditoría para import_excel
    r_audit = client.get(f"/api/v1/budgets/projects/{pid}/audit", headers={"Authorization": f"Bearer {auth_token}"})
    assert r_audit.status_code == 200
    audit = r_audit.json()
    assert any(a["action"] == "import_excel" for a in audit)
