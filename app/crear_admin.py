"""Crea una cuenta de administrador desde la terminal.

    python -m app.crear_admin

El registro público siempre crea clientes; un admin solo se crea así, con acceso
al servidor.
"""

from getpass import getpass

from pydantic import ValidationError

from .db import SessionLocal
from .repository_usuarios import EmailDuplicado, SqlUsuarioRepository
from .schemas import UsuarioIn


def main() -> None:
    email = input("Correo del admin: ")
    nombre = input("Nombre: ")
    password = getpass("Contraseña (no se ve al escribir): ")
    try:
        data = UsuarioIn(email=email, nombre=nombre, password=password)
    except ValidationError as error:
        print("Datos inválidos:", error.errors()[0]["msg"])
        return
    with SessionLocal() as session:
        try:
            SqlUsuarioRepository(session).crear(data, rol="admin")
        except EmailDuplicado:
            print("Ese correo ya existe")
            return
    print(f"Administrador {data.email} creado")


if __name__ == "__main__":
    main()
