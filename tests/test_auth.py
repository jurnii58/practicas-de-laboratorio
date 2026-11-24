"""Autenticación: registro, contraseñas con hash y tokens JWT."""

import jwt

from app.models import UsuarioModel
from app.security import SECRET_KEY, crear_token

ANA = {"email": "ana@utvt.edu.mx", "nombre": "Ana López", "password": "una-frase-larga"}


def iniciar_sesion(client, email=ANA["email"], password=ANA["password"]):
    return client.post("/auth/token", data={"username": email, "password": password})


def test_registro_no_devuelve_la_contraseña(client):
    r = client.post("/auth/registro", json=ANA)
    assert r.status_code == 201
    assert r.json() == {
        "id": 1,
        "email": "ana@utvt.edu.mx",
        "nombre": "Ana López",
        "rol": "cliente",
    }


def test_registro_ignora_el_rol_que_manda_el_usuario(client):
    r = client.post("/auth/registro", json={**ANA, "rol": "admin"})
    assert r.json()["rol"] == "cliente"


def test_correo_repetido_devuelve_409(client):
    client.post("/auth/registro", json=ANA)
    r = client.post("/auth/registro", json={**ANA, "email": "ANA@utvt.edu.mx"})
    assert r.status_code == 409


def test_contraseña_corta_devuelve_422(client):
    assert client.post("/auth/registro", json={**ANA, "password": "123"}).status_code == 422


def test_en_la_base_se_guarda_el_hash_no_la_contraseña(client, sesiones):
    client.post("/auth/registro", json=ANA)
    with sesiones() as session:
        guardado = session.get(UsuarioModel, 1).password_hash
    assert guardado != ANA["password"]
    assert guardado.startswith("$argon2id$")


def test_login_correcto_entrega_un_token_jwt(client):
    client.post("/auth/registro", json=ANA)
    r = iniciar_sesion(client)
    assert r.status_code == 200
    assert r.json()["token_type"] == "bearer"
    datos = jwt.decode(r.json()["access_token"], SECRET_KEY, algorithms=["HS256"])
    assert datos["sub"] == "ana@utvt.edu.mx"
    assert datos["rol"] == "cliente"
    assert "exp" in datos  # el token caduca


def test_login_fallido_no_revela_si_el_correo_existe(client):
    client.post("/auth/registro", json=ANA)
    mala_password = iniciar_sesion(client, password="otra-cosa-123")
    correo_inexistente = iniciar_sesion(client, email="nadie@utvt.edu.mx")
    assert mala_password.status_code == correo_inexistente.status_code == 401
    assert mala_password.json() == correo_inexistente.json()


def test_sin_token_devuelve_401(client):
    r = client.get("/auth/yo")
    assert r.status_code == 401
    assert r.headers["WWW-Authenticate"] == "Bearer"


def test_con_token_sabe_quien_eres(client):
    client.post("/auth/registro", json=ANA)
    token = iniciar_sesion(client).json()["access_token"]
    r = client.get("/auth/yo", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["email"] == "ana@utvt.edu.mx"


def test_token_alterado_devuelve_401(client):
    client.post("/auth/registro", json=ANA)
    token = iniciar_sesion(client).json()["access_token"]
    alterado = token[:-4] + ("AAAA" if not token.endswith("AAAA") else "BBBB")
    assert (
        client.get("/auth/yo", headers={"Authorization": f"Bearer {alterado}"}).status_code == 401
    )


def test_token_firmado_con_otra_clave_devuelve_401(client):
    client.post("/auth/registro", json=ANA)
    falso = jwt.encode({"sub": ANA["email"], "rol": "admin"}, "clave-de-un-atacante-" * 2)
    assert client.get("/auth/yo", headers={"Authorization": f"Bearer {falso}"}).status_code == 401


def test_token_vencido_devuelve_401(client):
    client.post("/auth/registro", json=ANA)
    vencido = crear_token(ANA["email"], "cliente", minutos=-1)
    assert client.get("/auth/yo", headers={"Authorization": f"Bearer {vencido}"}).status_code == 401
