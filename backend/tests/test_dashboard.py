def test_dashboard_basic(client, auth_token):
    """Valida agregaciones básicas del dashboard para un proyecto con:
    - 1 item con quantity=10 y precio derivado de APU (5*2 = 10)
    - 1 batch de medición ejecutando 4 unidades (EV=40)
    - 1 riesgo abierto
    """
    admin_token = auth_token
    # Crear proyecto
    r = client.post('/api/v1/budgets/projects', json={'name': 'DashProj', 'currency': 'CLP'}, headers={'Authorization': f'Bearer {admin_token}'})
    project_id = r.json()['id']
    # Crear capítulo + item
    ch = client.post('/api/v1/budgets/chapters', json={'project_id': project_id, 'code': 'C1', 'name': 'Cap 1'}, headers={'Authorization': f'Bearer {admin_token}'})
    chapter_id = ch.json()['id']
    it = client.post('/api/v1/budgets/items', json={'chapter_id': chapter_id, 'code': 'I1', 'name': 'Item 1', 'unit': 'u', 'quantity': 10}, headers={'Authorization': f'Bearer {admin_token}'})
    item_id = it.json()['id']
    # Set APU para price (precio resultante 10)
    apu = client.post(f'/api/v1/budgets/items/{item_id}/apu', json=[{'resource_code':'R1','resource_name':'Res 1','resource_type':'mat','unit':'u','unit_cost':5,'coeff':2}], headers={'Authorization': f'Bearer {admin_token}'})
    assert apu.status_code == 200
    # Crear batch medición y cerrar
    rmb = client.post('/api/v1/measurements/batches', json={'project_id': project_id, 'name': 'MB1'}, headers={'Authorization': f'Bearer {admin_token}'})
    assert rmb.status_code == 200
    batch_id = rmb.json()['batch_id']
    # Añadir línea (4 ejecutado)
    rline = client.post('/api/v1/measurements/batches/lines', json={'batch_id': batch_id, 'lines': [{'item_id': item_id, 'qty': 4}]}, headers={'Authorization': f'Bearer {admin_token}'})
    assert rline.status_code == 200
    # Cerrar batch
    rclose = client.post(f'/api/v1/measurements/batches/{batch_id}/close', headers={'Authorization': f'Bearer {admin_token}'})
    assert rclose.status_code == 200

    # Crear un riesgo
    rr = client.post('/api/v1/risks/', json={'project_id': project_id,'category':'financiero','description':'Riesgo X','probability':3,'impact':4}, headers={'Authorization': f'Bearer {admin_token}'})
    assert rr.status_code == 200

    # Dashboard
    rdb = client.get(f'/api/v1/dashboard/projects/{project_id}', headers={'Authorization': f'Bearer {admin_token}'})
    assert rdb.status_code == 200, rdb.text
    data = rdb.json()
    assert data['budget']['pv'] == 100  # 10 * 10
    assert data['budget']['ev'] == 40   # 4 * 10
    assert data['risks']['open'] == 1
    assert 'pending_steps' in data['workflows']
