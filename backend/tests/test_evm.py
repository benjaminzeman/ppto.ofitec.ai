import pytest
from sqlalchemy.orm import Session
from app.db.models.budget import Chapter, Item
from app.db.models.project import Project


def auth_headers(client):
    # crear usuario/login helper consistente con auth (usa username)
    r = client.post('/api/v1/auth/register', json={'username':'evm_user','password':'secret123'})
    # si ya existe, ignorar error 400
    if r.status_code not in (200,201,400):
        raise AssertionError(f"registro falló: {r.status_code} {r.text}")
    r2 = client.post('/api/v1/auth/login', data={'username':'evm_user','password':'secret123'})
    assert r2.status_code == 200, r2.text
    token = r2.json()['access_token']
    return {'Authorization': f'Bearer {token}'}


def create_basic_budget(db: Session):
    # crear proyecto aislado
    p = Project(name="Proyecto Test")
    db.add(p); db.flush()
    project_id = p.id
    ch = Chapter(name='Capitulo X', code='CX', project_id=project_id)
    db.add(ch)
    db.flush()
    it1 = Item(code='IT1', name='Item 1', quantity=10, price=5, chapter_id=ch.id)
    it2 = Item(code='IT2', name='Item 2', quantity=20, price=2, chapter_id=ch.id)
    db.add_all([it1,it2])
    db.commit(); db.expire_all()
    return project_id, ch.id


def test_evm_basic_flow(db_session, client):
    headers = auth_headers(client)
    # presupuesto
    project_id, _ = create_basic_budget(db_session)
    # crear batch medicion
    r = client.post('/api/v1/measurements/batches', json={'project_id':project_id,'name':'Batch 1'}, headers=headers)
    assert r.status_code == 200
    batch_id = r.json()['batch_id']
    # buscar items
    # simple query to get items
    # Items solo del proyecto bajo prueba
    items = db_session.query(Item).join(Chapter, Item.chapter_id==Chapter.id).filter(Chapter.project_id==project_id).all()
    # agregar lineas (parcial)
    lines_payload = []
    for it in items:
        qty = 5 if it.code=='IT1' else 10
        lines_payload.append({'item_id': it.id, 'qty': qty})
    r = client.post('/api/v1/measurements/batches/lines', json={'batch_id': batch_id, 'lines': lines_payload}, headers=headers)
    assert r.status_code == 200
    # cerrar batch
    r = client.post(f'/api/v1/measurements/batches/{batch_id}/close', headers=headers)
    assert r.status_code == 200
    # llamar evm
    r = client.get(f'/api/v1/evm/projects/{project_id}', headers=headers)
    assert r.status_code == 200
    data = r.json()
    # PV = 10*5 + 20*2 = 50 + 40 = 90
    assert round(data['planned_value'],2) == 90.0
    # EV esperado: ejecutado 5*5 + 10*2 = 25 + 20 = 45
    assert round(data['earned_value'],2) == 45.0
    assert round(data['actual_cost'],2) == 45.0
    assert data['spi'] == pytest.approx(0.5)
    assert data['cpi'] == pytest.approx(1.0)
    assert len(data['curve_s']) == 1
    assert round(data['curve_s'][0]['cumulative_ev'],2) == 45.0
