from app.db.models.project import Project
from app.db.models.budget import Chapter, Item
from app.db.models.audit import UserProjectRole
from app.db.models.versioning import BudgetVersionItem

def seed(db):
    p = Project(name="P-Adv")
    db.add(p); db.flush()
    ch = Chapter(project_id=p.id, code="C1", name="Cap 1"); db.add(ch); db.flush()
    it1 = Item(chapter_id=ch.id, code="IT1", name="Item1", unit="m2", quantity=10, price=100); db.add(it1); db.flush()
    return p, ch, it1

def ensure_admin(db, user_id, project_id):
    if not db.query(UserProjectRole).filter_by(user_id=user_id, project_id=project_id).first():
        db.add(UserProjectRole(user_id=user_id, project_id=project_id, role="admin")); db.commit()

def test_versions_list_detail_restore(client, db_session, auth_token):
    from app.services.security import decode_token
    username = decode_token(auth_token)
    from app.db.models.user import User
    u = db_session.query(User).filter_by(username=username).first()
    if not u:
        u = User(username=username, hashed_password="x"); db_session.add(u); db_session.flush()
    p, ch, it1 = seed(db_session)
    ensure_admin(db_session, u.id, p.id)
    # snapshot inicial
    r1 = client.post(f"/api/v1/versions/{p.id}/snapshot?name=BASE", headers={"Authorization": f"Bearer {auth_token}"})
    assert r1.status_code == 200
    v_base = r1.json()["version_id"]
    # modificar presupuesto
    it1.price = 150; db_session.commit()
    client.post(f"/api/v1/versions/{p.id}/snapshot?name=V2", headers={"Authorization": f"Bearer {auth_token}"})
    # listar versiones
    rlist = client.get(f"/api/v1/versions/{p.id}/versions", headers={"Authorization": f"Bearer {auth_token}"})
    assert rlist.status_code == 200
    assert len(rlist.json()) >= 2
    # detalle versión base
    rdetail = client.get(f"/api/v1/versions/version/{v_base}", headers={"Authorization": f"Bearer {auth_token}"})
    assert rdetail.status_code == 200
    lines = rdetail.json()["lines"]
    assert len(lines) == 1 and lines[0]["item_code"] == "IT1"
    # diff live contra base
    rdiff = client.get(f"/api/v1/versions/diff/live?project_id={p.id}&version_id={v_base}", headers={"Authorization": f"Bearer {auth_token}"})
    assert rdiff.status_code == 200
    changed = rdiff.json()["changed"]
    assert len(changed) == 1 and changed[0]["pu_version"] == 100.0 and changed[0]["pu_current"] == 150.0
    # restore base
    rrestore = client.post(f"/api/v1/versions/restore/{v_base}?project_id={p.id}", headers={"Authorization": f"Bearer {auth_token}"})
    assert rrestore.status_code == 200
    # verificar que precio volvió a 100
    it_current = db_session.query(Item).join(Chapter, Chapter.id==Item.chapter_id).filter(Item.code=="IT1", Chapter.project_id==p.id).first()
    assert float(it_current.price) == 100.0
