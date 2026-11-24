"""Rutas web para gestionar órdenes con HTML y formularios."""

from pathlib import Path
from typing import Annotated

from fastapi import APIRouter, Depends, Form, Request, status
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError

from ..repository_sql import SqlOrderRepository, get_repo
from ..schemas import OrderIn
from ..services.clientes import ClientesService, ServicioNoDisponible, get_clientes_service

router = APIRouter(prefix="/web", tags=["Web"])
templates = Jinja2Templates(directory=str(Path(__file__).resolve().parent.parent / "templates"))
Repo = Annotated[SqlOrderRepository, Depends(get_repo)]
ClientesDep = Annotated[ClientesService, Depends(get_clientes_service)]


def _datos_vacios() -> dict[str, str]:
    return {"cliente": "", "producto": "", "cantidad": "", "precio_unitario": ""}


@router.get("/ordenes")
def listar_ordenes_web(request: Request, repo: Repo):
    return templates.TemplateResponse(
        request,
        "ordenes.html",
        {"ordenes": repo.list()},
    )


@router.get("/ordenes/nueva")
def nueva_orden_web(
    request: Request,
    repo: Repo,
    clientes_service: ClientesDep = None,
):
    del repo
    try:
        clientes = clientes_service.listar_nombres()
        aviso = ""
    except ServicioNoDisponible:
        clientes = []
        aviso = "El servicio de clientes no responde."
    return templates.TemplateResponse(
        request,
        "nueva_orden.html",
        {
            "clientes": clientes,
            "datos": _datos_vacios(),
            "errores": {},
            "aviso": aviso,
        },
    )


@router.post("/ordenes/nueva")
def crear_orden_web(
    request: Request,
    repo: Repo,
    cliente: str = Form(...),
    producto: str = Form(...),
    cantidad: str = Form(...),
    precio_unitario: str = Form(...),
    clientes_service: ClientesDep = None,
):
    datos = {
        "cliente": cliente,
        "producto": producto,
        "cantidad": cantidad,
        "precio_unitario": precio_unitario,
    }
    try:
        clientes = clientes_service.listar_nombres()
        aviso = ""
    except ServicioNoDisponible:
        clientes = []
        aviso = "El servicio de clientes no responde."

    try:
        orden = OrderIn.model_validate(datos)
    except ValidationError as exc:
        errores = {}
        for error in exc.errors():
            campo = error["loc"][0] if error["loc"] else "root"
            errores[campo] = error["msg"]
        return templates.TemplateResponse(
            request,
            "nueva_orden.html",
            {
                "clientes": clientes,
                "datos": datos,
                "errores": errores,
                "aviso": aviso,
            },
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        )

    repo.add(orden)
    return RedirectResponse(url="/web/ordenes", status_code=status.HTTP_303_SEE_OTHER)
