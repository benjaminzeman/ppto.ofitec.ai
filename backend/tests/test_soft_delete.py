def test_soft_delete_flow(client, auth_token):
    h = {"Authorization": f"Bearer {auth_token}"}

    # Crear proyecto
    rp = client.post("/api/v1/budgets/projects", json={"name": "P SD", "currency": "CLP"}, headers=h)
    assert rp.status_code == 200
    pid = rp.json()["id"]

    # Crear capítulo
    rc = client.post("/api/v1/budgets/chapters", json={"project_id": pid, "code": "CSD", "name": "Cap SD"}, headers=h)
    assert rc.status_code == 200
    chapter_id = rc.json()["id"]

    # Crear item
    ri = client.post("/api/v1/budgets/items", json={"chapter_id": chapter_id, "code": "ISD", "name": "Item SD", "unit": "m2", "quantity": 5}, headers=h)
    assert ri.status_code == 200
    item_id = ri.json()["id"]

    # Update capítulo
    rcu = client.patch(f"/api/v1/budgets/chapters/{chapter_id}", json={"name": "Cap SD 2"}, headers=h)
    assert rcu.status_code == 200
    assert rcu.json()["name"] == "Cap SD 2"

    # Update item
    riu = client.patch(f"/api/v1/budgets/items/{item_id}", json={"quantity": 9}, headers=h)
    assert riu.status_code == 200

    # Delete item (soft)
    rid = client.delete(f"/api/v1/budgets/items/{item_id}", headers=h)
    assert rid.status_code == 200
    assert rid.json()["status"] == "deleted"

    # List items -> vacío
    r_list_items = client.get(f"/api/v1/budgets/chapters/{chapter_id}/items", headers=h)
    assert r_list_items.status_code == 200
    assert all(it["id"] != item_id for it in r_list_items.json())

    # Delete capítulo (soft)
    rcdel = client.delete(f"/api/v1/budgets/chapters/{chapter_id}", headers=h)
    assert rcdel.status_code == 200

    # List capítulos -> no incluye capítulo borrado
    r_list_ch = client.get(f"/api/v1/budgets/projects/{pid}/chapters", headers=h)
    assert r_list_ch.status_code == 200
    assert all(ch["id"] != chapter_id for ch in r_list_ch.json())

    # Auditoría contiene acciones nuevas
    ra = client.get(f"/api/v1/budgets/projects/{pid}/audit", headers=h)
    assert ra.status_code == 200
    audit_actions = {a["action"] for a in ra.json()}
    for expected in {"update_chapter", "update_item", "delete_item", "delete_chapter"}:
        assert expected in audit_actions
