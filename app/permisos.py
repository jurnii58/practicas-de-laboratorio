"""Dependencias de seguridad.

- get_usuario_actual: autenticación. ¿Quién eres? Sin token válido -> 401.
- requiere_admin: autorización. ¿Tienes permiso? Si no eres admin -> 403.
"""

from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .models import UsuarioModel
from .repository_usuarios import SqlUsuarioRepository, get_usuarios_repo
from .security import leer_token

# Le dice a FastAPI que el token llega en "Authorization: Bearer <token>" y que se
# obtiene en /auth/token. Con esto aparece el botón "Authorize" en /docs.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/token")

NO_AUTENTICADO = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="No se pudo validar la sesión",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_usuario_actual(
    token: Annotated[str, Depends(oauth2_scheme)],
    repo: Annotated[SqlUsuarioRepository, Depends(get_usuarios_repo)],
) -> UsuarioModel:
    try:
        datos = leer_token(token)
    except jwt.InvalidTokenError:  # firma alterada, token vencido o mal formado
        raise NO_AUTENTICADO from None

    usuario = repo.get_por_email(datos.get("sub", ""))
    if usuario is None:  # el token es válido pero la cuenta ya no existe
        raise NO_AUTENTICADO
    return usuario


UsuarioActual = Annotated[UsuarioModel, Depends(get_usuario_actual)]


def requiere_admin(usuario: UsuarioActual) -> UsuarioModel:
    if usuario.rol != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Solo administradores",
        )
    return usuario
