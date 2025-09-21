from fastapi.testclient import TestClient
import pytest


def register(client: TestClient, username: str):
    r = client.post('/api/v1/auth/register', json={'username': username, 'password': 'pass'})
    assert r.status_code == 200
    token = r.json()['access_token']
    me = client.get('/api/v1/auth/me', headers={'Authorization': f'Bearer {token}'})
    return token, me.json()['id']


def test_risks_flow(client: TestClient):
    admin_token, admin_id = register(client, 'risk_admin')
    viewer_token, viewer_id = register(client, 'risk_viewer')

    # Crear proyecto
    r = client.post('/api/v1/budgets/projects', json={'name': 'RiskProj', 'currency': 'CLP'}, headers={'Authorization': f'Bearer {admin_token}'})
    assert r.status_code == 200
    project_id = r.json()['id']

    # Asignar rol viewer
    r = client.post(f'/api/v1/budgets/projects/{project_id}/roles', json={'user_id': viewer_id, 'role': 'viewer'}, headers={'Authorization': f'Bearer {admin_token}'})
    assert r.status_code == 200

    # Viewer NO puede crear riesgo
    r = client.post('/api/v1/risks/', json={
        'project_id': project_id,
        'category': 'financiero',
        'description': 'Sobre costo de materiales',
        'probability': 4,
        'impact': 5
    }, headers={'Authorization': f'Bearer {viewer_token}'})
    assert r.status_code == 403

    # Admin crea riesgo
    r = client.post('/api/v1/risks/', json={
        'project_id': project_id,
        'category': 'financiero',
        'description': 'Sobre costo de materiales',
        'probability': 4,
        'impact': 5,
        'mitigation': 'Negociar contratos',
        'owner': 'Compras'
    }, headers={'Authorization': f'Bearer {admin_token}'})
    assert r.status_code == 200
    risk_id = r.json()['id']

    # Listar riesgos (viewer puede ver)
    r = client.get(f'/api/v1/risks/project/{project_id}', headers={'Authorization': f'Bearer {viewer_token}'})
    assert r.status_code == 200
    assert len(r.json()) == 1

    # Matriz
    r = client.get(f'/api/v1/risks/project/{project_id}/matrix', headers={'Authorization': f'Bearer {viewer_token}'})
    assert r.status_code == 200
    matrix = r.json()['matrix']
    assert matrix[3][4] == 1  # posición (prob 4, impacto 5)

    # Actualizar riesgo (admin)
    r = client.patch(f'/api/v1/risks/{risk_id}', json={'status': 'mitigating', 'impact': 4}, headers={'Authorization': f'Bearer {admin_token}'})
    assert r.status_code == 200

    # Verificar matriz actualizada
    r = client.get(f'/api/v1/risks/project/{project_id}/matrix', headers={'Authorization': f'Bearer {viewer_token}'})
    matrix2 = r.json()['matrix']
    assert matrix2[3][4] == 0
    assert matrix2[3][3] == 1
