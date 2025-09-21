import pytest


def register(client, username: str, password: str = "pass"):
    r = client.post("/api/v1/auth/register", json={"username": username, "password": password})
    assert r.status_code == 200, r.text
    data = r.json()
    token = data["access_token"]
    r2 = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r2.status_code == 200
    data["user_id"] = r2.json()["id"]
    return data


def create_project(client, token: str, name: str = "WF Proj"):
    r = client.post("/api/v1/budgets/projects", json={"name": name, "currency": "CLP"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_chapter(client, token: str, project_id: int):
    r = client.post("/api/v1/budgets/chapters", json={"project_id": project_id, "code": "C1", "name": "Chapter 1"}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def create_item(client, token: str, chapter_id: int):
    r = client.post("/api/v1/budgets/items", json={"chapter_id": chapter_id, "code": "I1", "name": "Item 1", "unit": "u", "quantity": 10}, headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200, r.text
    return r.json()["id"]


def assign_role(client, admin_token: str, project_id: int, user_id: int, role: str):
    r = client.post(f"/api/v1/budgets/projects/{project_id}/roles", json={"user_id": user_id, "role": role}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text


def test_workflow_full_cycle(client, db_session):
    # Registrar usuarios
    admin = register(client, "admin_wf@example.com")
    editor = register(client, "editor_wf@example.com")
    viewer = register(client, "viewer_wf@example.com")

    admin_token = admin["access_token"]
    editor_token = editor["access_token"]
    viewer_token = viewer["access_token"]

    # Crear proyecto (admin recibe rol admin automáticamente)
    project_id = create_project(client, admin_token)
    # Asignar roles
    assign_role(client, admin_token, project_id, editor["user_id"], "editor")
    assign_role(client, admin_token, project_id, viewer["user_id"], "viewer")

    chapter_id = create_chapter(client, admin_token, project_id)
    item_id = create_item(client, admin_token, chapter_id)

    # Crear workflow (roles admin -> editor)
    r = client.post("/api/v1/workflows/", json={
        "project_id": project_id,
        "name": "Aprobación Items",
        "entity_type": "item",
        "steps": ["admin", "editor"]
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text
    wf_id = r.json()["workflow_id"]

    # Iniciar instancia
    r = client.post("/api/v1/workflows/start", json={
        "workflow_id": wf_id,
        "entity_type": "item",
        "entity_id": item_id
    }, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200, r.text
    inst_id = r.json()["instance_id"]

    # Admin aprueba primer paso
    r = client.post(f"/api/v1/workflows/instance/{inst_id}/decide", json={"decision": "approve"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "running"
    assert r.json()["current_step"] == 2

    # Viewer no autorizado
    r = client.post(f"/api/v1/workflows/instance/{inst_id}/decide", json={"decision": "approve"}, headers={"Authorization": f"Bearer {viewer_token}"})
    assert r.status_code == 403

    # Editor aprueba segundo paso -> workflow aprobado
    r = client.post(f"/api/v1/workflows/instance/{inst_id}/decide", json={"decision": "approve"}, headers={"Authorization": f"Bearer {editor_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "approved"

    # Detalle
    r = client.get(f"/api/v1/workflows/instance/{inst_id}", headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    detail = r.json()
    assert detail["status"] == "approved"
    assert len(detail["steps"]) == 2


def test_workflow_rejection(client, db_session):
    admin = register(client, "admin_wf2@example.com")
    editor = register(client, "editor_wf2@example.com")
    admin_token = admin["access_token"]
    editor_token = editor["access_token"]
    project_id = create_project(client, admin_token)
    assign_role(client, admin_token, project_id, editor["user_id"], "editor")
    chapter_id = create_chapter(client, admin_token, project_id)
    item_id = create_item(client, admin_token, chapter_id)
    r = client.post("/api/v1/workflows/", json={
        "project_id": project_id,
        "name": "WF Reject",
        "entity_type": "item",
        "steps": ["admin", "editor"]
    }, headers={"Authorization": f"Bearer {admin_token}"})
    wf_id = r.json()["workflow_id"]
    r = client.post("/api/v1/workflows/start", json={"workflow_id": wf_id, "entity_type": "item", "entity_id": item_id}, headers={"Authorization": f"Bearer {admin_token}"})
    inst_id = r.json()["instance_id"]
    # Rechazo primer paso
    r = client.post(f"/api/v1/workflows/instance/{inst_id}/decide", json={"decision": "reject", "comment": "No procede"}, headers={"Authorization": f"Bearer {admin_token}"})
    assert r.status_code == 200
    assert r.json()["status"] == "rejected"
    # No debería permitir más decisiones
    r = client.post(f"/api/v1/workflows/instance/{inst_id}/decide", json={"decision": "approve"}, headers={"Authorization": f"Bearer {editor_token}"})
    assert r.status_code == 400
    # Fin del test
