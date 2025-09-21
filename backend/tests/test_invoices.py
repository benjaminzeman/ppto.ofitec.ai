import pytest
from app.db.models.project import Project
from app.db.models.audit import UserProjectRole
from app.db.models.user import User


def test_invoice_lifecycle(client, db_session, auth_token):
    # Crear proyecto y rol para el usuario auth_token
    token = auth_token
    # obtener username del token (endpoint /me)
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    username = me.json()["username"]
    user = db_session.query(User).filter_by(username=username).first()
    p = Project(name="Proj Inv")
    db_session.add(p); db_session.commit(); db_session.refresh(p)
    db_session.add(UserProjectRole(project_id=p.id, user_id=user.id, role="admin")); db_session.commit()
    headers = {"Authorization": f"Bearer {token}"}
    # crear factura
    r = client.post("/api/v1/invoices/", json={"project_id": p.id, "amount": 1000, "currency": "CLP"}, headers=headers)
    assert r.status_code == 200, r.text
    inv = r.json(); assert inv["status"] == "pending"
    # enviar SII
    r2 = client.post(f"/api/v1/invoices/{inv['id']}/send_sii", headers=headers)
    assert r2.status_code == 200, r2.text
    sii = r2.json(); assert sii["status"] == "accepted"; assert sii["dte_number"].startswith("DTE-")
    # registrar pago parcial
    r3 = client.post(f"/api/v1/invoices/{inv['id']}/payments", json={"amount": 400, "method": "transfer"}, headers=headers)
    assert r3.status_code == 200
    inv_after = r3.json(); assert inv_after["status"] == "accepted"
    # pago final
    r4 = client.post(f"/api/v1/invoices/{inv['id']}/payments", json={"amount": 600, "method": "transfer"}, headers=headers)
    assert r4.status_code == 200
    inv_paid = r4.json(); assert inv_paid["status"] == "paid"


def test_bank_import_and_reconcile(client, db_session, auth_token):
    token = auth_token
    me = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    username = me.json()["username"]
    user = db_session.query(User).filter_by(username=username).first()
    p = Project(name="Proj Inv 2")
    db_session.add(p); db_session.commit(); db_session.refresh(p)
    db_session.add(UserProjectRole(project_id=p.id, user_id=user.id, role="admin")); db_session.commit()
    headers = {"Authorization": f"Bearer {token}"}
    # Crear factura accepted
    r = client.post("/api/v1/invoices/", json={"project_id": p.id, "amount": 500, "currency": "CLP"}, headers=headers)
    inv = r.json()
    client.post(f"/api/v1/invoices/{inv['id']}/send_sii", headers=headers)
    # importar transacción banco
    items = [{"date": "2025-01-15", "description": "Pago cliente", "amount": 500, "balance": 10000}]
    r_imp = client.post("/api/v1/invoices/bank/import", json={"project_id": p.id, "items": items}, headers=headers)
    assert r_imp.status_code == 200, r_imp.text
    # listar transacciones para obtener id
    # (Simplificación: acceder directamente DB)
    db = db_session
    from app.db.models.versioning import BankTransaction
    bt = db.query(BankTransaction).filter(BankTransaction.project_id == p.id).order_by(BankTransaction.id.desc()).first()
    # reconciliar
    r_rec = client.post("/api/v1/invoices/bank/reconcile", json={"bank_txn_id": bt.id, "invoice_id": inv['id']}, headers=headers)
    assert r_rec.status_code == 200, r_rec.text
    data = r_rec.json(); assert data["invoice_status"] == "paid"
