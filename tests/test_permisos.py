"""Autorización: leer es público; modificar y borrar órdenes es solo para admins."""

ORDEN = {"cliente": "Ana López", "producto": "Teclado", "cantidad": 2, "precio_unitario": 350.0}


def test_leer_ordenes_sigue_siendo_publico(client):
    client.post("/orders", json=ORDEN)
    assert client.get("/orders").status_code == 200
    assert client.get("/orders/1").status_code == 200


def test_borrar_sin_token_devuelve_401(client):
    client.post("/orders", json=ORDEN)
    assert client.delete("/orders/1").status_code == 401


def test_un_cliente_no_puede_borrar_403(client, headers_de):
    client.post("/orders", json=ORDEN)
    r = client.delete("/orders/1", headers=headers_de("cliente"))
    assert r.status_code == 403
    assert client.get("/orders/1").status_code == 200  # la orden sigue ahí


def test_un_cliente_no_puede_modificar_403(client, headers_de):
    client.post("/orders", json=ORDEN)
    r = client.put("/orders/1", json={**ORDEN, "cantidad": 9}, headers=headers_de("cliente"))
    assert r.status_code == 403


def test_un_admin_si_puede_borrar(client, headers_de):
    client.post("/orders", json=ORDEN)
    assert client.delete("/orders/1", headers=headers_de("admin")).status_code == 204
