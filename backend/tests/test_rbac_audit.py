def test_project_role_assignment_and_audit(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Crear proyecto (asigna rol admin al creador)
    r = client.post("/api/v1/budgets/projects", json={"name": "P1", "currency": "CLP"}, headers=headers)
    assert r.status_code == 200
    project_id = r.json()["id"]

    # Crear capítulo (debe permitir porque usuario es admin)
    rc = client.post("/api/v1/budgets/chapters", json={"project_id": project_id, "code": "C1", "name": "Cap 1"}, headers=headers)
    assert rc.status_code == 200
    chapter_id = rc.json()["id"]

    # Crear item
    ri = client.post("/api/v1/budgets/items", json={"chapter_id": chapter_id, "code": "I1", "name": "Item 1", "unit": "m2", "quantity": 10}, headers=headers)
    assert ri.status_code == 200
    item_id = ri.json()["id"]

    # Set APU
    r_apu = client.post(f"/api/v1/budgets/items/{item_id}/apu", json=[{"resource_code": "R1", "resource_name": "Recurso 1", "resource_type": "mat", "unit": "u", "unit_cost": 5.0, "coeff": 2}], headers=headers)
    assert r_apu.status_code == 200

    # List audit logs
    r_audit = client.get(f"/api/v1/budgets/projects/{project_id}/audit", headers=headers)
    assert r_audit.status_code == 200
    data = r_audit.json()
    # Debe haber al menos logs de create project, chapter, item, set_apu
    actions = {entry["action"] for entry in data}
    assert {"create", "set_apu"}.issubset(actions)


def test_rbac_denied_for_non_member(client, auth_token):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Crear proyecto 1
    r = client.post("/api/v1/budgets/projects", json={"name": "P1", "currency": "CLP"}, headers=headers)
    project_id = r.json()["id"]

    # Registrar otro usuario sin rol en el proyecto
    r2 = client.post("/api/v1/auth/register", json={"username": "other", "password": "pass"})
    token_other = r2.json()["access_token"]
    h2 = {"Authorization": f"Bearer {token_other}"}

    # Intentar crear capítulo con segundo usuario debe fallar 403
    rc = client.post("/api/v1/budgets/chapters", json={"project_id": project_id, "code": "C1", "name": "Cap 1"}, headers=h2)
    assert rc.status_code == 403
