import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib.messages.views import SuccessMessageMixin

from apps.ventas.models import Cotizacion, CotizacionItem, Recibo, ReciboItem, Remito
from apps.productos.models import Producto
from apps.ventas.forms import (
    CotizacionForm, CotizacionItemForm, CotizacionFilterForm,
    EnviarEmailForm, ReciboForm, ReciboItemForm, RemitoForm,
)
from cotizaciones.services.recibos import recibo_queryset_filtrado
from cotizaciones.services.remitos import remito_queryset_filtrado
from cotizaciones.services.documents.pdf import build_cotizacion_pdf_response, build_recibo_pdf_response
from cotizaciones.services.communication.email import enviar_cotizacion_por_email, enviar_recibo_por_email


# ============================================
# Cotizaciones
# ============================================

def _items_initial(cotizacion):
    if not cotizacion or not cotizacion.pk:
        return []
    return [
        {
            "producto_id": item.producto_id,
            "nombre": item.producto.nombre,
            "precio_unitario": float(item.precio_unitario),
            "cantidad": item.cantidad,
        }
        for item in cotizacion.items.select_related("producto").all()
    ]


class CotizacionListView(LoginRequiredMixin, ListView):
    model = Cotizacion
    template_name = "cotizaciones/cotizacion/list.html"
    context_object_name = "cotizaciones"
    paginate_by = 10

    def get_queryset(self):
        qs = Cotizacion.objects.select_related("cliente", "usuario")
        form = CotizacionFilterForm(self.request.GET)
        if form.is_valid():
            search = form.cleaned_data.get("search")
            tipo = form.cleaned_data.get("tipo_documento")
            estado = form.cleaned_data.get("estado")
            fecha_desde = form.cleaned_data.get("fecha_desde")
            fecha_hasta = form.cleaned_data.get("fecha_hasta")

            if search:
                qs = qs.filter(
                    Q(numero__icontains=search) | Q(cliente__nombre__icontains=search)
                )
            if tipo:
                qs = qs.filter(tipo_documento=tipo)
            if estado:
                qs = qs.filter(estado=estado)
            if fecha_desde:
                qs = qs.filter(fecha__gte=fecha_desde)
            if fecha_hasta:
                qs = qs.filter(fecha__lte=fecha_hasta)
        return qs.order_by("-fecha", "-id")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["filter_form"] = CotizacionFilterForm(self.request.GET)
        return ctx


class CotizacionCreateView(LoginRequiredMixin, CreateView):
    model = Cotizacion
    form_class = CotizacionForm
    template_name = "cotizaciones/cotizacion/form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items_initial"] = _items_initial(self.object)
        return ctx

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        self.object = form.save()

        try:
            descuento = Decimal(str(self.request.POST.get("descuento_pct", "0") or "0"))
        except (ValueError, InvalidOperation):
            descuento = Decimal("0")
        self.object.descuento_porcentaje = descuento

        raw = self.request.POST.get("items")
        if raw:
            try:
                for itm in json.loads(raw):
                    pid = itm.get("producto_id")
                    if not pid:
                        continue
                    try:
                        cant = Decimal(str(itm.get("cantidad") or "1"))
                    except (ValueError, InvalidOperation):
                        cant = Decimal("1")
                    try:
                        precio = Decimal(str(itm.get("precio_unitario") or "0"))
                    except (ValueError, InvalidOperation):
                        precio = Decimal("0")

                    CotizacionItem.objects.create(
                        cotizacion=self.object,
                        producto_id=pid,
                        cantidad=cant,
                        precio_unitario=precio,
                    )
            except (json.JSONDecodeError, ValueError, InvalidOperation):
                pass

        self.object.calcular_total()
        messages.success(self.request, "Cotización creada exitosamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("cotizacion_detail", kwargs={"pk": self.object.pk})


class CotizacionUpdateView(LoginRequiredMixin, UpdateView):
    model = Cotizacion
    form_class = CotizacionForm
    template_name = "cotizaciones/cotizacion/form.html"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items_initial"] = _items_initial(self.object)
        return ctx

    def form_valid(self, form):
        self.object = form.save()

        try:
            descuento = Decimal(str(self.request.POST.get("descuento_pct", "0") or "0"))
        except (ValueError, InvalidOperation):
            descuento = Decimal("0")
        self.object.descuento_porcentaje = descuento

        raw = self.request.POST.get("items")
        if raw:
            try:
                items_data = json.loads(raw)
                self.object.items.all().delete()
                for itm in items_data:
                    pid = itm.get("producto_id")
                    if not pid:
                        continue
                    try:
                        cant = Decimal(str(itm.get("cantidad") or "1"))
                    except (ValueError, InvalidOperation):
                        cant = Decimal("1")
                    try:
                        precio = Decimal(str(itm.get("precio_unitario") or "0"))
                    except (ValueError, InvalidOperation):
                        precio = Decimal("0")

                    CotizacionItem.objects.create(
                        cotizacion=self.object,
                        producto_id=pid,
                        cantidad=cant,
                        precio_unitario=precio,
                    )
            except (json.JSONDecodeError, ValueError, InvalidOperation):
                pass

        self.object.calcular_total()
        messages.success(self.request, "Cotización actualizada exitosamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("cotizacion_detail", kwargs={"pk": self.object.pk})


class CotizacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Cotizacion
    template_name = "cotizaciones/cotizacion/confirm_delete.html"
    success_url = reverse_lazy("cotizacion_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "Cotización eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)


@login_required
def buscar_productos_ajax(request):
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.filter(activo=True)
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(proveedor__nombre__icontains=q)
        ).select_related("proveedor")[:50]
    else:
        productos = productos.select_related("proveedor")

    data = [
        {
            "id": p.id,
            "nombre": p.nombre,
            "precio": float(p.precio_unitario),
            "proveedor": p.proveedor.nombre if p.proveedor else "",
            "stock": p.stock,
        }
        for p in productos
    ]
    return JsonResponse({"productos": data})


class CotizacionDetailView(LoginRequiredMixin, DetailView):
    model = Cotizacion
    template_name = "cotizaciones/cotizacion/detail.html"
    context_object_name = "cotizacion"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("producto")

        cliente_nombre = getattr(self.object.cliente, "nombre", "Cliente")
        nro = getattr(self.object, "numero", self.object.id)

        ctx["email_form"] = EnviarEmailForm(
            initial={
                "email_destino": self.object.cliente.email or "",
                "asunto": f"Cotización {nro} - GCinsumos",
                "mensaje": f"Estimado/a {cliente_nombre},\n\nAdjuntamos su cotización.\n\nSaludos,\nGCinsumos",
            }
        )
        return ctx


@login_required
def agregar_item_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    if request.method == "POST":
        form = CotizacionItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.cotizacion = cotizacion
            item.save()
            messages.success(request, "Producto agregado.")
    return redirect("cotizacion_detail", pk=cotizacion_id)


@login_required
def eliminar_item_cotizacion(request, item_id):
    item = get_object_or_404(CotizacionItem, id=item_id)
    cot_id = item.cotizacion.id
    item.delete()
    messages.success(request, "Producto eliminado.")
    return redirect("cotizacion_detail", pk=cot_id)


@login_required
def cambiar_estado_cotizacion(request, cotizacion_id, estado):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    nuevo_estado = estado.lower()
    estados_validos = [e[0] for e in Cotizacion.ESTADO_CHOICES]
    if nuevo_estado in estados_validos:
        cotizacion.estado = nuevo_estado
        cotizacion.save()
        messages.success(request, f"Estado actualizado a: {cotizacion.get_estado_display()}")
    else:
        messages.error(request, f"Estado '{estado}' no es válido.")

    return redirect("cotizacion_detail", pk=cotizacion_id)


@login_required
def actualizar_descuento_cotizacion(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    if request.method == "POST":
        raw = request.POST.get("descuento_pct", "0").strip()
        if not raw:
            raw = "0"
        try:
            raw = raw.replace(",", ".")
            pct = Decimal(raw)
            cotizacion.descuento_porcentaje = pct
            cotizacion.save(update_fields=["descuento_porcentaje"])
            cotizacion.calcular_total()
            messages.success(request, f"Descuento actualizado a {pct}%.")
        except Exception:
            messages.error(request, "Valor de descuento inválido.")
    return redirect("cotizacion_detail", pk=cotizacion_id)


@login_required
def generar_pdf(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    return build_cotizacion_pdf_response(cotizacion=cotizacion)


@login_required
def enviar_cotizacion_email(request, cotizacion_id):
    cotizacion = get_object_or_404(Cotizacion, id=cotizacion_id)
    if request.method == "POST":
        form = EnviarEmailForm(request.POST)
        if form.is_valid():
            try:
                enviar_cotizacion_por_email(
                    cotizacion=cotizacion,
                    email_destino=form.cleaned_data["email_destino"],
                    asunto=form.cleaned_data["asunto"],
                    mensaje=form.cleaned_data["mensaje"],
                )
                cotizacion.email_enviado = True
                cotizacion.save(update_fields=["email_enviado"])
                messages.success(request, "Email enviado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al enviar: {str(e)}")
    return redirect("cotizacion_detail", pk=cotizacion_id)


# ============================================
# Recibos
# ============================================

class ReciboListView(LoginRequiredMixin, ListView):
    model = Recibo
    template_name = "cotizaciones/recibo/list.html"
    context_object_name = "recibos"
    paginate_by = 10

    def get_queryset(self):
        qs = recibo_queryset_filtrado(self.request.user)
        busqueda = self.request.GET.get("q", "").strip()
        if busqueda:
            qs = qs.filter(Q(numero__icontains=busqueda) | Q(cliente__nombre__icontains=busqueda))
        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        page = ctx.get("page_obj")
        if page and page.paginator.count:
            start = (page.number - 1) * page.paginator.per_page + 1
            ctx["page_start"] = start
            ctx["page_end"] = start + len(ctx["recibos"]) - 1
            ctx["page_total"] = page.paginator.count
        else:
            ctx["page_start"] = 0
            ctx["page_end"] = 0
            ctx["page_total"] = 0
        ctx["total_recibos"] = Recibo.objects.count()
        return ctx


class ReciboCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Recibo
    form_class = ReciboForm
    template_name = "cotizaciones/recibo/form.html"
    success_message = "Recibo creado correctamente."

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy("recibo_detail", kwargs={"pk": self.object.pk})


class ReciboUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Recibo
    form_class = ReciboForm
    template_name = "cotizaciones/recibo/form.html"
    success_message = "Recibo actualizado correctamente."

    def get_success_url(self):
        return reverse_lazy("recibo_detail", kwargs={"pk": self.object.pk})


class ReciboDeleteView(LoginRequiredMixin, DeleteView):
    model = Recibo
    success_url = reverse_lazy("recibo_list")
    success_message = "Recibo eliminado correctamente."

    def delete(self, request, *args, **kwargs):
        messages.success(self.request, self.success_message)
        return super().delete(request, *args, **kwargs)


class ReciboDetailView(LoginRequiredMixin, DetailView):
    model = Recibo
    template_name = "cotizaciones/recibo/detail.html"
    context_object_name = "recibo"

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["items"] = self.object.items.select_related("producto")
        ctx["item_form"] = ReciboItemForm()
        cliente_nombre = getattr(self.object.cliente, "razon_social", getattr(self.object.cliente, "nombre", "Cliente"))
        ctx["email_form"] = EnviarEmailForm(
            initial={
                "email_destino": self.object.cliente.email or "",
                "asunto": f"Recibo {self.object.numero} - GCinsumos",
                "mensaje": f"Estimado/a {cliente_nombre},\n\nAdjuntamos su recibo.\n\nSaludos,\nGCinsumos",
            }
        )
        return ctx


@login_required
def agregar_item_recibo(request, recibo_id):
    recibo = get_object_or_404(Recibo, id=recibo_id)
    if request.method == "POST":
        form = ReciboItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.recibo = recibo
            item.save()
            recibo.actualizar_totales()
            messages.success(request, "Producto agregado.")
    return redirect("recibo_detail", pk=recibo_id)


@login_required
def eliminar_item_recibo(request, item_id):
    item = get_object_or_404(ReciboItem, id=item_id)
    recibo_id = item.recibo.id
    item.delete()
    item.recibo.actualizar_totales()
    messages.success(request, "Producto eliminado.")
    return redirect("recibo_detail", pk=recibo_id)


@login_required
def generar_pdf_recibo(request, recibo_id):
    recibo = get_object_or_404(Recibo, id=recibo_id)
    return build_recibo_pdf_response(recibo=recibo)


@login_required
def enviar_recibo_email(request, recibo_id):
    recibo = get_object_or_404(Recibo, id=recibo_id)
    if request.method == "POST":
        form = EnviarEmailForm(request.POST)
        if form.is_valid():
            try:
                enviar_recibo_por_email(
                    recibo=recibo,
                    email_destino=form.cleaned_data["email_destino"],
                    asunto=form.cleaned_data["asunto"],
                    mensaje=form.cleaned_data["mensaje"],
                )
                messages.success(request, "Email enviado con éxito.")
            except Exception as e:
                messages.error(request, f"Error al enviar: {str(e)}")
    return redirect("recibo_detail", pk=recibo_id)


# ============================================
# Remitos
# ============================================

class RemitoListView(LoginRequiredMixin, ListView):
    model = Remito
    template_name = "cotizaciones/remito/list.html"
    context_object_name = "remitos"
    paginate_by = 10

    def get_queryset(self):
        return remito_queryset_filtrado(self.request)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["total_remitos"] = Remito.objects.count()
        ctx["remitos_pendientes"] = Remito.objects.filter(estado="pendiente").count()
        ctx["filtro_estado"] = self.request.GET.get("estado", "")
        page = ctx.get("page_obj")
        if page and page.paginator.count:
            start = (page.number - 1) * page.paginator.per_page + 1
            ctx["page_start"] = start
            ctx["page_end"] = start + len(ctx["remitos"]) - 1
            ctx["page_total"] = page.paginator.count
        else:
            ctx["page_start"] = 0
            ctx["page_end"] = 0
            ctx["page_total"] = 0
        return ctx


class RemitoCreateView(LoginRequiredMixin, CreateView):
    model = Remito
    form_class = RemitoForm
    template_name = "cotizaciones/remito/form.html"
    success_url = reverse_lazy("remito_list")

    def form_valid(self, form):
        form.instance.usuario = self.request.user
        return super().form_valid(form)


class RemitoUpdateView(LoginRequiredMixin, UpdateView):
    model = Remito
    form_class = RemitoForm
    template_name = "cotizaciones/remito/form.html"
    success_url = reverse_lazy("remito_list")


class RemitoDeleteView(LoginRequiredMixin, DeleteView):
    model = Remito
    success_url = reverse_lazy("remito_list")


@login_required
def diagnostico_datos(request):
    from django.db.models import Count

    productos_total = Producto.objects.count()
    productos_activos = Producto.objects.filter(activo=True).count()
    productos_inactivos = productos_total - productos_activos
    proveedores_total = Producto.objects.values("proveedor_id").distinct().count()
    cotizaciones_total = Cotizacion.objects.count()
    cotizaciones_con_items = (
        Cotizacion.objects.annotate(n_items=Count("items")).filter(n_items__gt=0).count()
    )
    cotizaciones_sin_items = cotizaciones_total - cotizaciones_con_items
    items_total = CotizacionItem.objects.count()

    ultimas = list(
        Cotizacion.objects.annotate(n_items=Count("items"))
        .order_by("-id")[:10]
        .values("id", "numero", "cliente__nombre", "n_items", "total", "descuento_porcentaje")
    )

    ctx = {
        "productos_total": productos_total,
        "productos_activos": productos_activos,
        "productos_inactivos": productos_inactivos,
        "proveedores_total": proveedores_total,
        "cotizaciones_total": cotizaciones_total,
        "cotizaciones_con_items": cotizaciones_con_items,
        "cotizaciones_sin_items": cotizaciones_sin_items,
        "items_total": items_total,
        "ultimas": ultimas,
    }
    return render(request, "cotizaciones/diagnostico.html", ctx)