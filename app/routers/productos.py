"""Consulta REST de existencias del almacén SOAP."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from ..services.almacen import (
    AlmacenService,
    ProductoNoRegistrado,
    get_almacen_service,
)
from ..services.clientes import ServicioNoDisponible

router = APIRouter(prefix="/productos", tags=["Productos"])

AlmacenDep = Annotated[AlmacenService, Depends(get_almacen_service)]


@router.get("/{producto}/existencia")
def consultar_existencia(producto: str, almacen: AlmacenDep) -> dict[str, int | str]:
    try:
        existencia = almacen.consultar_existencia(producto)
    except ProductoNoRegistrado as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ServicioNoDisponible as error:
        raise HTTPException(status_code=503, detail=str(error)) from error
    return {"producto": producto, "existencia": existencia}
