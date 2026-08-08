from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [

    # Dashboard
    path('', views.dashboard, name='dashboard'),

    # Auth
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('register/', views.register, name='register'),
    path('password_reset/', auth_views.PasswordResetView.as_view(template_name='registration/password_reset_form.html'), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),

    # Usuarios
    path('usuarios/', views.UserListView.as_view(), name='user_list'),
    path('usuarios/crear/', views.UserCreateView.as_view(), name='user_create'),

    # Clientes
    path('clientes/', views.ClienteListView.as_view(), name='cliente_list'),
    path('clientes/crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('clientes/<int:pk>/', views.ClienteDetailView.as_view(), name='cliente_detail'),
    path('clientes/<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    path('clientes/<int:pk>/eliminar/', views.ClienteDeleteView.as_view(), name='cliente_delete'),
    path('clientes/<int:pk>/toggle-activo/', views.toggle_cliente_activo, name='cliente_toggle_activo'),
    path('clientes/importar/', views.importar_clientes_excel, name='cliente_importar_excel'),
    path('clientes/exportar/excel/', views.exportar_clientes_excel, name='cliente_exportar_excel'),
    path('clientes/exportar/pdf/', views.exportar_clientes_pdf, name='cliente_exportar_pdf'),

    # Proveedores
    path('proveedores/', views.ProveedorListView.as_view(), name='proveedor_list'),
    path('proveedores/crear/', views.ProveedorCreateView.as_view(), name='proveedor_create'),
    path('proveedores/<int:pk>/', views.ProveedorDetailView.as_view(), name='proveedor_detail'),
    path('proveedores/<int:pk>/editar/', views.ProveedorUpdateView.as_view(), name='proveedor_update'),
    path('proveedores/<int:pk>/eliminar/', views.ProveedorDeleteView.as_view(), name='proveedor_delete'),

    # Productos
    path('productos/', views.ProductoListView.as_view(), name='producto_list'),
    path('productos/crear/', views.ProductoCreateView.as_view(), name='producto_create'),
    path('productos/<int:pk>/', views.ProductoDetailView.as_view(), name='producto_detail'),
    path('productos/<int:pk>/editar/', views.ProductoUpdateView.as_view(), name='producto_update'),
    path('productos/<int:pk>/eliminar/', views.ProductoDeleteView.as_view(), name='producto_delete'),

    # Cotizaciones
    path('cotizaciones/', views.CotizacionListView.as_view(), name='cotizacion_list'),
    path('cotizaciones/crear/', views.CotizacionCreateView.as_view(), name='cotizacion_create'),
    path('cotizaciones/<int:pk>/', views.CotizacionDetailView.as_view(), name='cotizacion_detail'),
    path('cotizaciones/<int:pk>/editar/', views.CotizacionUpdateView.as_view(), name='cotizacion_update'),
    path('cotizaciones/<int:pk>/eliminar/', views.CotizacionDeleteView.as_view(), name='cotizacion_delete'),

    # Descuento
    path('cotizaciones/<int:cotizacion_id>/descuento/', views.actualizar_descuento_cotizacion, name='actualizar_descuento_cotizacion'),

    # PDF
    path('cotizaciones/<int:cotizacion_id>/pdf/', views.generar_pdf, name='generar_pdf'),

    # Estado
    path('cotizaciones/<int:cotizacion_id>/estado/<str:estado>/', views.cambiar_estado_cotizacion, name='cambiar_estado_cotizacion'),

    # Factura desde cotizaciÃ³n
    path('cotizaciones/<int:cotizacion_id>/crear-factura/', views.crear_factura_desde_cotizacion, name='crear_factura_desde_cotizacion'),

    # Items cotizaciÃ³n
    path('cotizaciones/<int:cotizacion_id>/agregar-item/', views.agregar_item_cotizacion, name='agregar_item_cotizacion'),
    path('items/<int:item_id>/eliminar/', views.eliminar_item_cotizacion, name='eliminar_item_cotizacion'),

    # Email
    path('cotizaciones/<int:cotizacion_id>/enviar-email/', views.enviar_cotizacion_email, name='enviar_cotizacion_email'),

    # Leads / CRM
    path('leads/', views.LeadListView.as_view(), name='lead_list'),
    path('leads/crear/', views.LeadCreateView.as_view(), name='lead_create'),
    path('leads/<int:pk>/editar/', views.LeadUpdateView.as_view(), name='lead_update'),
    path('leads/<int:pk>/eliminar/', views.LeadDeleteView.as_view(), name='lead_delete'),

    # Remitos
    path('remitos/', views.RemitoListView.as_view(), name='remito_list'),
    path('remitos/crear/', views.RemitoCreateView.as_view(), name='remito_create'),
    path('remitos/<int:pk>/editar/', views.RemitoUpdateView.as_view(), name='remito_update'),
    path('remitos/<int:pk>/eliminar/', views.RemitoDeleteView.as_view(), name='remito_delete'),

    # Comprobantes
    path('comprobantes/', views.ComprobanteListView.as_view(), name='comprobante_list'),

    # CategorÃ­as
    path('categorias/', views.CategoriaListView.as_view(), name='categoria_list'),
    path('categorias/crear/', views.CategoriaCreateView.as_view(), name='categoria_create'),
    path('categorias/<int:pk>/editar/', views.CategoriaUpdateView.as_view(), name='categoria_update'),
    path('categorias/<int:pk>/eliminar/', views.CategoriaDeleteView.as_view(), name='categoria_delete'),

    # Marcas
    path('marcas/', views.MarcaListView.as_view(), name='marca_list'),
    path('marcas/crear/', views.MarcaCreateView.as_view(), name='marca_create'),
    path('marcas/<int:pk>/editar/', views.MarcaUpdateView.as_view(), name='marca_update'),
    path('marcas/<int:pk>/eliminar/', views.MarcaDeleteView.as_view(), name='marca_delete'),

    # Compras
    path('compras/', views.CompraListView.as_view(), name='compra_list'),
    path('compras/crear/', views.CompraCreateView.as_view(), name='compra_create'),
    path('compras/<int:pk>/', views.CompraDetailView.as_view(), name='compra_detail'),
    path('compras/<int:pk>/editar/', views.CompraUpdateView.as_view(), name='compra_update'),
    path('compras/<int:pk>/eliminar/', views.CompraDeleteView.as_view(), name='compra_delete'),
    path('compras/<int:compra_id>/agregar-item/', views.agregar_item_compra, name='compra_add_item'),
    path('compra-items/<int:item_id>/eliminar/', views.eliminar_item_compra, name='compra_delete_item'),

    # Stock
    path('stock/', views.StockListView.as_view(), name='stock_list'),
    path('stock/exportar/excel/', views.exportar_stock_excel, name='stock_exportar_excel'),
    path('stock/exportar/pdf/', views.exportar_stock_pdf, name='stock_exportar_pdf'),
    path('stock/importar/', views.importar_stock_excel, name='stock_importar_excel'),

    # Movimientos de stock
    path('stock/movimientos/', views.MovimientoStockListView.as_view(), name='movimiento_stock_list'),
    path('stock/movimientos/crear/', views.MovimientoStockCreateView.as_view(), name='movimiento_stock_create'),

    # Recibos
    path('recibos/', views.ReciboListView.as_view(), name='recibo_list'),
    path('recibos/crear/', views.ReciboCreateView.as_view(), name='recibo_create'),
    path('recibos/<int:pk>/', views.ReciboDetailView.as_view(), name='recibo_detail'),
    path('recibos/<int:pk>/editar/', views.ReciboUpdateView.as_view(), name='recibo_update'),
    path('recibos/<int:pk>/eliminar/', views.ReciboDeleteView.as_view(), name='recibo_delete'),
    path('recibos/<int:recibo_id>/pdf/', views.generar_pdf_recibo, name='recibo_pdf'),
    path('recibos/<int:recibo_id>/agregar-item/', views.agregar_item_recibo, name='recibo_add_item'),
    path('recibos/<int:recibo_id>/enviar-email/', views.enviar_recibo_email, name='recibo_email'),
    path('recibo-items/<int:item_id>/eliminar/', views.eliminar_item_recibo, name='recibo_delete_item'),

    # Reportes
    path('reportes/', views.reportes_view, name='reportes'),

    # ConfiguraciÃ³n
    path('configuracion/', views.configuracion, name='configuracion'),

    # API Tradicional Interna
    path('api/producto/<int:producto_id>/precio/', views.get_producto_precio, name='get_producto_precio'),
    path('api/pending-cotizaciones-count/', views.pending_cotizaciones_count, name='pending_cotizaciones_count'),
    path('api/pending-cotizaciones/', views.pending_cotizaciones_list, name='pending_cotizaciones_list'),
    path('api/productos/buscar/', views.buscar_productos_ajax, name='buscar_productos_ajax'),
    path('diagnostico/', views.diagnostico_datos, name='diagnostico_datos'),

    # FacturaciÃ³n
    path('facturacion/', views.FacturaListView.as_view(), name='factura_list'),
    path('facturacion/nueva/', views.FacturaCreateView.as_view(), name='factura_create'),
    path('facturacion/<int:pk>/', views.FacturaDetailView.as_view(), name='factura_detail'),
    path('facturacion/<int:factura_id>/items/', views.agregar_item_factura, name='factura_agregar_item'),
    path('facturacion/<int:factura_id>/autorizar/', views.autorizar_factura_view, name='factura_autorizar'),
    path('facturacion/<int:factura_id>/pdf/', views.generar_pdf_factura_view, name='generar_pdf_factura'),

    # Listas de precio
    path('listas-precio/', views.ListaPrecioListView.as_view(), name='listaprecio_list'),
    path('listas-precio/crear/', views.ListaPrecioCreateView.as_view(), name='listaprecio_create'),
    path('listas-precio/<int:pk>/', views.ListaPrecioDetailView.as_view(), name='listaprecio_detail'),
    path('listas-precio/<int:pk>/editar/', views.ListaPrecioUpdateView.as_view(), name='listaprecio_update'),
    path('listas-precio/<int:pk>/eliminar/', views.ListaPrecioDeleteView.as_view(), name='listaprecio_delete'),
    path('listas-precio/<int:pk>/importar-csv/', views.importar_csv_lista_precio, name='listaprecio_importar_csv'),
    path('listas-precio/<int:pk>/exportar-pdf/', views.exportar_lista_precio_pdf, name='listaprecio_exportar_pdf'),
    path('listas-precio/<int:pk>/aplicar/', views.aplicar_precios_lista, name='listaprecio_aplicar'),
    path('listas-precio/<int:pk>/items/agregar/', views.agregar_item_lista_precio, name='listaprecio_item_add'),
    path('listas-precio/<int:lista_pk>/items/<int:item_pk>/editar/', views.editar_item_lista_precio, name='listaprecio_item_edit'),
    path('listas-precio/<int:lista_pk>/items/<int:item_pk>/eliminar/', views.eliminar_item_lista_precio, name='listaprecio_item_delete'),

    # Roles y permisos
    path('roles/', views.GroupListView.as_view(), name='rol_list'),
    path('roles/crear/', views.GroupCreateView.as_view(), name='rol_create'),
    path('roles/<int:pk>/editar/', views.GroupUpdateView.as_view(), name='rol_update'),
    path('roles/<int:pk>/eliminar/', views.GroupDeleteView.as_view(), name='rol_delete'),

    # AFIP
    path('facturacion/configuracion/', views.configuracion_afip, name='facturacion_config'),
    path('facturacion/configuracion/csr/', views.generar_csr_view, name='facturacion_generar_csr'),
    path('facturacion/configuracion/test/', views.test_conexion_afip, name='facturacion_test'),
]
