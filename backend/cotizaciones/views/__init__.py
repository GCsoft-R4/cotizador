"""
Re-exporta símbolos para mantener compatibilidad con imports existentes:
`from cotizaciones import views` y `from cotizaciones.views import X`.
"""

from apps.core.views import register, UserListView, UserCreateView, GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView, configuracion, reportes_view  # noqa: F401
from apps.dashboard.views import dashboard, reportes  # noqa: F401
from apps.clientes.views import (  # noqa: F401
    ClienteListView,
    ClienteCreateView,
    ClienteUpdateView,
    ClienteDeleteView,
    ClienteDetailView,
    toggle_cliente_activo,
    importar_clientes_excel,
    exportar_clientes_excel,
    exportar_clientes_pdf,
    LeadListView,
    LeadCreateView,
    LeadUpdateView,
    LeadDeleteView,
)
from apps.productos.views import (  # noqa: F401
    ProductoListView,
    ProductoCreateView,
    ProductoUpdateView,
    ProductoDeleteView,
    ProductoDetailView,
    CategoriaListView,
    CategoriaCreateView,
    CategoriaUpdateView,
    CategoriaDeleteView,
    MarcaListView,
    MarcaCreateView,
    MarcaUpdateView,
    MarcaDeleteView,
    ListaPrecioListView,
    ListaPrecioCreateView,
    ListaPrecioUpdateView,
    ListaPrecioDeleteView,
    ListaPrecioDetailView,
    importar_csv_lista_precio,
    exportar_lista_precio_pdf,
    aplicar_precios_lista,
    editar_item_lista_precio,
    eliminar_item_lista_precio,
    agregar_item_lista_precio,
)
from apps.ventas.views import (  # noqa: F401
    CotizacionListView,
    CotizacionCreateView,
    CotizacionUpdateView,
    CotizacionDeleteView,
    CotizacionDetailView,
    cambiar_estado_cotizacion,
    agregar_item_cotizacion,
    eliminar_item_cotizacion,
    generar_pdf,
    enviar_cotizacion_email,
    actualizar_descuento_cotizacion,
    buscar_productos_ajax,
    diagnostico_datos,
    ReciboListView,
    ReciboCreateView,
    ReciboUpdateView,
    ReciboDeleteView,
    ReciboDetailView,
    agregar_item_recibo,
    eliminar_item_recibo,
    generar_pdf_recibo,
    enviar_recibo_email,
    RemitoListView,
    RemitoCreateView,
    RemitoUpdateView,
    RemitoDeleteView,
)
from apps.compras.views import (  # noqa: F401
    CompraListView,
    CompraCreateView,
    CompraUpdateView,
    CompraDeleteView,
    CompraDetailView,
    agregar_item_compra,
    eliminar_item_compra,
)
from apps.stock.views import (  # noqa: F401
    MovimientoStockListView,
    MovimientoStockCreateView,
    StockListView,
    exportar_stock_excel,
    exportar_stock_pdf,
    importar_stock_excel,
)
from apps.facturacion.views import (  # noqa: F401
    configuracion_afip,
    generar_csr_view,
    test_conexion_afip,
    FacturaListView,
    FacturaCreateView,
    FacturaDetailView,
    agregar_item_factura,
    autorizar_factura_view,
    generar_pdf_factura_view,
    crear_factura_desde_cotizacion,
)
from apps.comprobantes.views import ComprobanteListView  # noqa: F401
from apps.ventas.api import (  # noqa: F401
    pending_cotizaciones_count, pending_cotizaciones_list,
    CotizacionViewSet, CotizacionItemViewSet,
)
from apps.clientes.api import ClienteViewSet  # noqa: F401
from apps.productos.api import ProductoViewSet, get_producto_precio  # noqa: F401
from apps.facturacion.api import FacturaViewSet  # noqa: F401
from apps.proveedores.views import (  # noqa: F401
    ProveedorListView,
    ProveedorCreateView,
    ProveedorUpdateView,
    ProveedorDeleteView,
    ProveedorDetailView,
)