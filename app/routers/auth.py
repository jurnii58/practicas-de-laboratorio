"""Registro, inicio de sesión (token) y datos del usuario actual."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm

from ..permisos import UsuarioActual
from ..repository_usuarios import (
    EmailDuplicado,
    SqlUsuarioRepository,
    get_usuarios_repo,
)
from ..schemas import Token, UsuarioIn, UsuarioOut
from ..security import HASH_FALSO, crear_token, verificar_password

router = APIRouter(prefix="/auth", tags=["Autenticación"])

Usuarios = Annotated[SqlUsuarioRepository, Depends(get_usuarios_repo)]


@router.post(
    "/registro",
    response_model=UsuarioOut,
    status_code=status.HTTP_201_CREATED,
)
def registrar(data: UsuarioIn, repo: Usuarios) -> UsuarioOut:
    try:
        return repo.crear(data)  # siempre con rol "cliente"
    except EmailDuplicado:
        raise HTTPException(
            status_code=409, detail="Ese correo ya está registrado"
        ) from None


@router.post("/token", response_model=Token)
def iniciar_sesion(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    repo: Usuarios,
) -> Token:
    # OAuth2 llama "username" al campo; en nuestra tienda es el correo
    usuario = repo.get_por_email(form.username)
    if usuario is None:
        verificar_password(form.password, HASH_FALSO)  # tarda lo mismo que si existiera
        valido = False
    else:
        valido = verificar_password(form.password, usuario.password_hash)

    if not valido:
        # Mismo mensaje para correo inexistente y contraseña incorrecta
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Correo o contraseña incorrectos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return Token(
        access_token=crear_token(usuario.email, usuario.rol),
        token_type="bearer",
    )


@router.get("/yo", response_model=UsuarioOut)
def quien_soy(usuario: UsuarioActual) -> UsuarioOut:
    return usuario
