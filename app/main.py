import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.sessions import SessionMiddleware

from .db import engine  # noqa: F401
from .routers import auth, carrito, comprobantes, orders, productos, web

logger = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Evento de arranque
    logger.info("API de Órdenes iniciada")
    yield
    # Evento de apagado
    logger.info("API de Órdenes detenida")


app = FastAPI(title="API de Órdenes", version="0.2.0", lifespan=lifespan)
app.include_router(auth.router)
app.include_router(orders.router)
app.include_router(productos.router)
app.include_router(web.router)
app.include_router(comprobantes.router)
app.include_router(carrito.router)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SECRET_KEY", "solo-para-desarrollo-cambiar"),
    session_cookie="sesion_tienda",
    max_age=60 * 60 * 2,  # la sesión dura 2 horas
    same_site="lax",
    https_only=False,  # en producción, True (solo por HTTPS)
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
