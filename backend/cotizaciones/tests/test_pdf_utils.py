from decimal import Decimal
from io import BytesIO
from unittest.mock import patch, MagicMock

import pytest
from django.urls import reverse
from PyPDF2 import PdfReader

from ..models import Cotizacion, CotizacionItem, Factura, Cliente
from ..utils.pdf_utils import (
    generar_pdf_cotizacion,
    generar_pdf_buffer,
    generar_pdf_factura,
    generar_pdf_factura_buffer,
)


@pytest.fixture
def cotizacion(usuario_admin, cliente):
    c = Cotizacion.objects.create(
        numero="COT-TEST-001",
        cliente=cliente,
        tipo_documento="presupuesto",
        usuario=usuario_admin,
    )
    from ..models import Producto, Proveedor
    prov = Proveedor.objects.create(nombre="Prov PDF")
    prod = Producto.objects.create(
        nombre="Producto PDF", proveedor=prov, precio_unitario=Decimal("100.00"), tipo="producto"
    )
    CotizacionItem.objects.create(cotizacion=c, producto=prod, cantidad=2, precio_unitario=Decimal("100.00"))
    return c


class TestGenerarPdfCotizacion:
    """Tests del wrapper HTTP generar_pdf_cotizacion"""

    def test_devuelve_http_response(self, cotizacion):
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_cotizacion(cotizacion)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]
        assert ".pdf" in response["Content-Disposition"]

    def test_filename_incluye_cliente(self, cotizacion):
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_cotizacion(cotizacion)
        assert cotizacion.cliente.nombre.replace(" ", "_") in response["Content-Disposition"]

    def test_filename_para_recibo(self, cotizacion):
        cotizacion.tipo_documento = "recibo"
        cotizacion.numero = "Recibo_001"
        cotizacion.save()
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_cotizacion(cotizacion)
        assert "Recibo" in response["Content-Disposition"]

    def test_filename_para_cotizacion(self, cotizacion):
        cotizacion.tipo_documento = "cotizacion"
        cotizacion.numero = "COT-001"
        cotizacion.save()
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_cotizacion(cotizacion)
        assert "Cotizacion" in response["Content-Disposition"]

    def test_fallback_sin_nombre_en_cliente(self, cotizacion):
        cotizacion.cliente.nombre = ""
        cotizacion.cliente.save()
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_cotizacion(cotizacion)
        assert "sin_nombre" in response["Content-Disposition"]


class TestGenerarPdfBuffer:
    """Tests de generaciÃ³n real del buffer PDF"""

    def test_devuelve_pdf_valido(self, cotizacion):
        buffer = generar_pdf_buffer(cotizacion)
        assert isinstance(buffer, BytesIO)
        content = buffer.getvalue()
        assert len(content) > 0
        assert content[:4] == b"%PDF"

    def test_sin_items_sigue_siendo_pdf_valido(self, cotizacion):
        cotizacion.items.all().delete()
        buffer = generar_pdf_buffer(cotizacion)
        buffer.seek(0)
        content = buffer.read()
        assert len(content) > 0

    def test_con_descuento_muestra_fila(self, cotizacion):
        cotizacion.descuento_porcentaje = Decimal("10.00")
        cotizacion.calcular_total()
        buffer = generar_pdf_buffer(cotizacion)
        content = buffer.getvalue()
        assert len(content) > 0
        reader = PdfReader(BytesIO(content))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "Descuento (10%):" in text
        assert "-$20.00" in text

    def test_sin_descuento_no_muestra_fila(self, cotizacion):
        cotizacion.descuento_porcentaje = Decimal("0.00")
        cotizacion.calcular_total()
        buffer = generar_pdf_buffer(cotizacion)
        reader = PdfReader(BytesIO(buffer.getvalue()))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
        assert "Descuento" not in text

    def test_con_observaciones(self, cotizacion):
        cotizacion.observaciones = "Test observaciÃ³n"
        cotizacion.save()
        buffer = generar_pdf_buffer(cotizacion)
        content = buffer.getvalue()
        assert len(content) > 0


class TestGenerarPdfFactura:
    """Tests del wrapper HTTP generar_pdf_factura"""

    def test_devuelve_http_response(self, cliente, usuario_admin):
        factura = Factura.objects.create(
            cliente=cliente, tipo="C", punto_venta=1, numero=1, usuario=usuario_admin,
        )
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_factura_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_factura(factura)
        assert response.status_code == 200
        assert response["Content-Type"] == "application/pdf"
        assert "attachment" in response["Content-Disposition"]

    def test_filename_formato_correcto(self, cliente, usuario_admin):
        factura = Factura.objects.create(
            cliente=cliente, tipo="C", punto_venta=1, numero=152, usuario=usuario_admin,
        )
        with patch("cotizaciones.utils.pdf_utils.generar_pdf_factura_buffer") as mock_buffer:
            mock_buffer.return_value = BytesIO(b"%PDF-1.4 mock content")
            response = generar_pdf_factura(factura)
        filename = response["Content-Disposition"]
        assert "factura_0001-00000152" in filename


class TestGenerarPdfFacturaBuffer:
    """Tests del buffer real de factura PDF"""

    def test_devuelve_bytesio(self, cliente, usuario_admin):
        factura = Factura.objects.create(
            cliente=cliente, tipo="C", punto_venta=1, numero=1, usuario=usuario_admin,
            cae="12345678901234", estado="autorizada",
        )
        buffer = generar_pdf_factura_buffer(factura)
        assert isinstance(buffer, BytesIO)
        content = buffer.getvalue()
        assert len(content) > 0

    def test_con_items(self, cliente, usuario_admin, producto):
        factura = Factura.objects.create(
            cliente=cliente, tipo="C", punto_venta=1, numero=2, usuario=usuario_admin,
        )
        factura.items.create(
            descripcion=producto.nombre, cantidad=2, precio_unit=Decimal("100.00"),
        )
        buffer = generar_pdf_factura_buffer(factura)
        content = buffer.getvalue()
        assert len(content) > 0

    def test_con_cae_vencimiento(self, cliente, usuario_admin):
        factura = Factura.objects.create(
            cliente=cliente, tipo="C", punto_venta=1, numero=3, usuario=usuario_admin,
            cae_vencimiento="2025-02-01",
        )
        buffer = generar_pdf_factura_buffer(factura)
        content = buffer.getvalue()
        assert len(content) > 0
