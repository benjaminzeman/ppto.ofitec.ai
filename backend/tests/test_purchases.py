from fastapi.testclient import TestClient
import uuid

def test_purchases_flow(client, auth_token):
    # Crear supplier
    sname = f"Supp {uuid.uuid4().hex[:6]}"
    r = client.post("/api/v1/purchases/suppliers", json={"name": sname, "tax_id": "T123", "contact_email": "s@example.com"}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200, r.text
    supplier_id = r.json()["id"]

    # Crear proyecto vía import excel mínimo no disponible aquí -> crear capítulo/ítem usando budgets endpoints?
    # Simplificamos: crear proyecto importando BC3 simple inline
    BC3_CONTENT = """# Demo BC3\nC;X;Chap X\nI;X;ITX;Item X;m2;10\nR;ITX;MAT;RZ;Res Z;1;5\n"""
    import tempfile
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
        tmp.write(BC3_CONTENT.encode()); tmp.flush()
        with open(tmp.name, 'rb') as fh:
            files = {"file": ("p.bc3", fh.read(), "text/plain")}
        data = {"project_name": "Proyecto Compras"}
    r = client.post("/api/v1/imports/bc3", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200, r.text
    project_id = r.json()["project_id"]

    # Recuperar tree para obtener item id
    r = client.get(f"/api/v1/budgets/projects/{project_id}/tree", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    tree = r.json()
    item_id = tree['chapters'][0]['items'][0]['id']

    # Crear RFQ
    r = client.post("/api/v1/purchases/rfq", json={"project_id": project_id, "items": [{"item_id": item_id, "qty": 5}]}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    rfq_id = r.json()["rfq_id"]

    # Añadir Quote
    # Obtener rfq_items id: simplificación -> rfq_items consecutivos, consultar ranking luego
    # Creamos cotización usando rfq_item_id=1 asunción: base limpia en test.
    r = client.post("/api/v1/purchases/quote", json={"rfq_id": rfq_id, "supplier_id": supplier_id, "lines": [{"rfq_item_id": 1, "unit_price": 100}]}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    quote_id = r.json()["quote_id"]

    # Ranking
    r = client.get(f"/api/v1/purchases/rank/{rfq_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    ranking = r.json()
    assert any(q['quote_id'] == quote_id for q in ranking)

    # Crear PO
    r = client.post("/api/v1/purchases/po", json={"project_id": project_id, "supplier_id": supplier_id, "lines": [{"item_id": item_id, "qty": 5, "unit_price": 100}], "rfq_id": rfq_id}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    po_id = r.json()["po_id"]

    # Obtener PO
    r = client.get(f"/api/v1/purchases/po/{po_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    data_po = r.json()
    assert data_po['id'] == po_id and len(data_po['lines']) == 1

    # Cambiar estado
    r = client.patch(f"/api/v1/purchases/po/{po_id}/status", json={"status": "approved"}, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    assert r.json()['status'] == 'approved'

    # Listar POs del proyecto
    r = client.get(f"/api/v1/purchases/po/project/{project_id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    listed = r.json()
    assert any(p['id'] == po_id for p in listed)
