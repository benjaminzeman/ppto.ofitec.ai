import tempfile
from app.services.bc3_parser import BC3ParseError

BC3_EXT_SAMPLE = """~V|FIEBDC-3|1.0
~KCH1|Capitulo CH1
~KCH2|Capitulo CH2
~RRC1|Recurso 1|u|12,5
~RRC2|Recurso 2|u|3
~CIT1.1|Item 1.1|m2
~CIT2|Item 2|m
~DIT1.1|RC1|2
~DIT1.1|RC2|0,5
~DIT2|RC2|10
"""

def test_import_bc3_extended(client, auth_token):
    # Crear archivo temporal extended
    with tempfile.NamedTemporaryFile(delete=False, suffix='.bc3') as tmp:
        tmp.write(BC3_EXT_SAMPLE.encode('latin-1'))
        tmp.flush()
        with open(tmp.name, 'rb') as fh:
            files = {"file": ("extended.bc3", fh.read(), "text/plain")}
        data = {"project_name": "Proyecto BC3 Ext"}
    r = client.post("/api/v1/imports/bc3", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200, r.text
    project_id = r.json()["project_id"]
    # Obtener árbol para verificar items
    tree = client.get(f"/api/v1/budgets/projects/{project_id}/tree", headers={"Authorization": f"Bearer {auth_token}"})
    assert tree.status_code == 200
    payload = tree.json()
    # Debe contener capítulos GENERAL y/o CH1/CH2 dependiendo mapping
    chapter_codes = {c['code'] for c in payload['chapters']}
    assert 'CH1' in chapter_codes or 'GENERAL' in chapter_codes
    # Verificar que items tienen precio calculado (>= 0) dentro de capítulos
    total_items_checked = 0
    for ch in payload['chapters']:
        for itm in ch['items']:
            assert itm['price'] >= 0
            total_items_checked += 1
    assert total_items_checked > 0
