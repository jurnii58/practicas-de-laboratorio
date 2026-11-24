"""Cliente SOAP para consultar la existencia de productos en el almacén."""

from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape

import httpx

from .clientes import ServicioNoDisponible

URL_BASE = "http://127.0.0.1:8001"
SOAP_ACTION = "http://utvt.edu.mx/almacen/ConsultarExistencia"
NS_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
NS_ALM = "http://utvt.edu.mx/almacen"


class ProductoNoRegistrado(Exception):
    """El almacén no tiene registrado el producto solicitado."""


class AlmacenService:
    def __init__(self, client: httpx.Client | None = None) -> None:
        self._client = client or httpx.Client(
            base_url=URL_BASE,
            timeout=3.0,
            transport=httpx.HTTPTransport(retries=2),
        )
        base_url = self._client.base_url
        if not str(base_url):
            base_url = httpx.URL(URL_BASE)
        self._url = base_url.join("/almacen")

    def consultar_existencia(self, producto: str) -> int:
        sobre = (
            '<?xml version="1.0" encoding="utf-8"?>'
            f'<soap:Envelope xmlns:soap="{NS_SOAP}" xmlns:alm="{NS_ALM}">'
            "<soap:Body><alm:ConsultarExistencia>"
            f"<alm:producto>{escape(producto)}</alm:producto>"
            "</alm:ConsultarExistencia></soap:Body></soap:Envelope>"
        )

        try:
            respuesta = self._client.post(
                self._url,
                content=sobre.encode("utf-8"),
                headers={
                    "Content-Type": "text/xml; charset=utf-8",
                    "SOAPAction": f'"{SOAP_ACTION}"',
                },
            )
        except httpx.HTTPError as error:
            raise ServicioNoDisponible(str(error)) from error

        try:
            raiz = ET.fromstring(respuesta.content)
        except ET.ParseError as error:
            raise ServicioNoDisponible("El almacén respondió con XML inválido") from error

        falla = raiz.find(f"{{{NS_SOAP}}}Body/{{{NS_SOAP}}}Fault")
        if falla is not None:
            codigo = falla.findtext("faultcode", default="")
            mensaje = falla.findtext("faultstring", default="Error SOAP del almacén")
            if codigo.rsplit(":", 1)[-1] == "Client":
                raise ProductoNoRegistrado(mensaje)
            raise ServicioNoDisponible(mensaje)
        if respuesta.is_error:
            raise ServicioNoDisponible(f"El almacén respondió con HTTP {respuesta.status_code}")

        existencia = raiz.findtext(
            f"{{{NS_SOAP}}}Body/{{{NS_ALM}}}ConsultarExistenciaResponse/"
            f"{{{NS_ALM}}}existencia"
        )
        if existencia is None:
            raise ServicioNoDisponible("La respuesta SOAP no contiene la existencia")
        try:
            return int(existencia)
        except ValueError as error:
            raise ServicioNoDisponible("La existencia recibida no es un entero") from error


servicio = AlmacenService()


def get_almacen_service() -> AlmacenService:
    return servicio
