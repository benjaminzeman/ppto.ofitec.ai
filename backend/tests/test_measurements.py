import tempfile

def test_measurements_flow(client, auth_token):
    # Importar BC3 simple para crear proyecto e ítem
    BC3_CONTENT = """# Demo BC3\nC;M;Chap M\nI;M;ITM;Item Med;m2;20\nR;ITM;MAT;RM;Res M;1;10\n"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
        tmp.write(BC3_CONTENT.encode()); tmp.flush()
        with open(tmp.name,'rb') as fh:
            files = {"file": ("med.bc3", fh.read(), "text/plain")}
        data = {"project_name": "Proyecto Med"}
    r = client.post("/api/v1/imports/bc3", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    project_id = r.json()["project_id"]

    # Obtener tree y extraer item
    r = client.get(f"/api/v1/budgets/projects/{project_id}/tree", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    tree = r.json()
    item_id = tree['chapters'][0]['items'][0]['id']

    # Crear batch
    r = client.post("/api/v1/measurements/batches", json={"project_id": project_id, "name": "B1"}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    batch_id = r.json()["batch_id"]

    # Agregar líneas
    r = client.post("/api/v1/measurements/batches/lines", json={"batch_id": batch_id, "lines": [{"item_id": item_id, "qty": 5}]}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200

    # Cerrar batch
    r = client.post(f"/api/v1/measurements/batches/{batch_id}/close", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200

    # Ver progreso
    r = client.get(f"/api/v1/measurements/project/{project_id}/progress", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    progress = r.json()
    assert progress['executed_pct'] > 0
    assert progress['items'][0]['executed_qty'] == 5
