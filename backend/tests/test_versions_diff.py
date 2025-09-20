from app.db.models.project import Project
from app.db.models.budget import Chapter, Item


def seed_basic_budget(db):
    p = Project(name="P1")
    db.add(p); db.flush()
    ch = Chapter(project_id=p.id, code="C1", name="Cap")
    db.add(ch); db.flush()
    it = Item(chapter_id=ch.id, code="IT1", name="Item 1", unit="m2", quantity=10, price=100)
    db.add(it); db.flush()
    return p, it


def test_snapshot_and_diff(client, db_session, auth_token):
    p, it = seed_basic_budget(db_session)
    # snapshot 1
    r1 = client.post(f"/api/v1/versions/{p.id}/snapshot?name=V1", headers={"Authorization": f"Bearer {auth_token}"})
    assert r1.status_code == 200
    # modificar item
    it.price = 120
    db_session.commit()
    # snapshot 2
    r2 = client.post(f"/api/v1/versions/{p.id}/snapshot?name=V2", headers={"Authorization": f"Bearer {auth_token}"})
    assert r2.status_code == 200
    v1 = r1.json()["version_id"]
    v2 = r2.json()["version_id"]
    diff = client.get(f"/api/v1/versions/diff?v_from={v1}&v_to={v2}")
    assert diff.status_code == 200
    data = diff.json()
    assert data["added"] == []
    assert data["removed"] == []
    assert len(data["changed"]) == 1
    row = data["changed"][0]
    assert row["pu_from"] == 100.0
    assert row["pu_to"] == 120.0
