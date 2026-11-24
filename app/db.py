"""Conexión a la base de datos con SQLAlchemy."""

from collections.abc import Iterator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

URL_BD = "sqlite:///./ordenes.db"
# En la Unidad IV: postgresql+psycopg://...

# check_same_thread=False: FastAPI puede atender peticiones en distintos hilos
engine = create_engine(URL_BD, connect_args={"check_same_thread": False})


@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Clase base de todos los modelos (tablas)."""


def get_session() -> Iterator[Session]:
    """Dependencia: abre una sesión por petición y la cierra al terminar."""
    with SessionLocal() as session:
        yield session
