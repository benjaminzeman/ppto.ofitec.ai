import tempfile

BC3_SAMPLE = """# Demo BC3
C;C1;Capitulo 1
I;C1;IT1;Item 1;m2;5
R;IT1;MAT;R1;Res 1;2;10
R;IT1;MO;R2;Res 2;0.5;40
"""


def test_import_bc3(client, auth_token):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".bc3") as tmp:
        tmp.write(BC3_SAMPLE.encode())
        tmp.flush()
        with open(tmp.name, "rb") as fh:
            files = {"file": ("test.bc3", fh.read(), "text/plain")}
        data = {"project_name": "Proyecto BC3"}
    r = client.post("/api/v1/imports/bc3", data=data, files=files, headers={"Authorization": f"Bearer {auth_token}"})
    assert r.status_code == 200
    assert isinstance(r.json()["project_id"], int)
