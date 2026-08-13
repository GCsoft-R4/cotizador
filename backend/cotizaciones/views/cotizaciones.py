import json
from decimal import Decimal, InvalidOperation

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import (
    ListView, CreateView, UpdateView, DeleteView, DetailView,
)

from ..models import Cotizacion, CotizacionItem, Producto
from ..forms import (
    CotizacionForm, CotizacionItemForm, CotizacionFilterForm, EnviarEmailForm,
)
from ..services.communication.email import enviar_cotizacion_por_email
from ..services.documents.pdf import build_cotizacion_pdf_response


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
        return qs.order_by('-fecha', '-id')

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
        messages.success(self.request, "CotizaciÃ³n actualizada exitosamente.")
        return redirect(self.get_success_url())

    def get_success_url(self):
        return reverse_lazy("cotizacion_detail", kwargs={"pk": self.object.pk})


class CotizacionDeleteView(LoginRequiredMixin, DeleteView):
    model = Cotizacion
    template_name = "cotizaciones/cotizacion/confirm_delete.html"
    success_url = reverse_lazy("cotizacion_list")

    def delete(self, request, *args, **kwargs):
        messages.success(request, "CotizaciÃ³n eliminada exitosamente.")
        return super().delete(request, *args, **kwargs)


@login_required
def buscar_productos_ajax(request):
    q = request.GET.get("q", "").strip()
    productos = Producto.objects.filter(activo=True)
    if q:
        productos = productos.filter(
            Q(nombre__icontains=q) | Q(proveedor__nombre__icontains=q)
        )
    productos = productos.select_related("proveedor")
    if q:
        productos = productos[:50]
    # sin q se devuelven todos
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
        
        cliente_nombre = getattr(self.object.cliente, 'nombre', 'Cliente')
        nro = getattr(self.object, 'numero', self.object.id)
        
        ctx["email_form"] = EnviarEmailForm(
            initial={
                "email_destino": self.object.cliente.email or "",
                "asunto": f"CotizaciÃ³n {nro} - GCinsumos",
                "mensaje": f"Estimado/a {cliente_nombre},\n\nAdjuntamos su cotizaciÃ³n.\n\nSaludos,\nGCinsumos",
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
        messages.error(request, f"Estado '{estado}' no es vÃ¡lido.")

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
            messages.error(request, "Valor de descuento invÃ¡lido.")
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
                messages.success(request, "Email enviado con Ã©xito.")
            except Exception as e:
                messages.error(request, f"Error al enviar: {str(e)}")
    return redirect("cotizacion_detail", pk=cotizacion_id)
