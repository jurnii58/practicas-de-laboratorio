"""Repositorio de usuarios: guardar y buscar cuentas."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .db import get_session
from .models import UsuarioModel
from .schemas import UsuarioIn
from .security import hashear_password


class EmailDuplicado(Exception):
    """Ya existe una cuenta con ese correo."""


class SqlUsuarioRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def crear(self, data: UsuarioIn, rol: str = "cliente") -> UsuarioModel:
        usuario = UsuarioModel(
            email=data.email.lower(),
            nombre=data.nombre,
            password_hash=hashear_password(data.password),  # nunca la contraseña tal cual
            rol=rol,  # el rol lo decide el servidor, no lo que mande el cliente
        )
        self.session.add(usuario)
        try:
            self.session.commit()
        except IntegrityError:  # el correo es UNIQUE en la tabla
            self.session.rollback()
            raise EmailDuplicado(data.email) from None
        self.session.refresh(usuario)
        return usuario

    def get_por_email(self, email: str) -> UsuarioModel | None:
        consulta = select(UsuarioModel).where(UsuarioModel.email == email.lower())
        return self.session.scalars(consulta).first()


def get_usuarios_repo(
    session: Annotated[Session, Depends(get_session)],
) -> SqlUsuarioRepository:
    return SqlUsuarioRepository(session)
