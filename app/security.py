"""Contraseñas con hash (Argon2) y tokens JWT firmados.

Dos ideas:
- La contraseña nunca se guarda: se guarda su hash. Al iniciar sesión se vuelve a
  calcular y se compara. Si roban la base de datos, no obtienen las contraseñas.
- Después del login, el usuario recibe un token JWT firmado con SECRET_KEY. Cada
  petición lo trae en el encabezado Authorization; si alguien lo modifica, la firma
  ya no coincide y se rechaza.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

# En producción viene de una variable de entorno, nunca escrita en el código.
SECRET_KEY = os.environ.get("JWT_SECRET", "solo-para-desarrollo-cambiar-por-una-clave-larga")
ALGORITMO = "HS256"
MINUTOS_TOKEN = 30

hasher = PasswordHash.recommended()  # Argon2id, el algoritmo que recomienda OWASP

# Hash de una contraseña que nadie usa: sirve para tardar lo mismo cuando el correo
# no existe (si no, un atacante mediría el tiempo para saber qué correos existen).
HASH_FALSO = hasher.hash("contraseña-que-nadie-usa")


def hashear_password(password: str) -> str:
    return hasher.hash(password)


def verificar_password(password: str, password_hash: str) -> bool:
    return hasher.verify(password, password_hash)


def crear_token(email: str, rol: str, minutos: int = MINUTOS_TOKEN) -> str:
    expira = datetime.now(timezone.utc) + timedelta(minutes=minutos)
    datos = {"sub": email, "rol": rol, "exp": expira}  # sub = de quién es el token
    return jwt.encode(datos, SECRET_KEY, algorithm=ALGORITMO)


def leer_token(token: str) -> dict:
    """Devuelve el contenido del token. Lanza jwt.InvalidTokenError si la firma no
    coincide o si ya expiró."""
    return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITMO])
