from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from simple_history.models import HistoricalRecords


class Cotizacion(models.Model):
    TIPO_CHOICES = [("presupuesto", "Presupuesto"), ("recibo", "Recibo")]
    ESTADO_CHOICES = [
        ("borrador", "Borrador"), ("enviada", "Enviada"),
        ("aprobada", "Aprobada"), ("rechazada", "Rechazada"), ("facturada", "Facturada"),
    ]

    numero = models.CharField(max_length=20, unique=True, db_index=True, blank=True, null=True)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    tipo_documento = models.CharField(max_length=20, choices=TIPO_CHOICES, default="presupuesto")
    fecha = models.DateField(auto_now_add=True)
    observaciones = models.TextField(blank=True)
    descuento_porcentaje = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"), validators=[MinValueValidator(Decimal("0.00")), MaxValueValidator(Decimal("100.00"))])
    subtotal_bruto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    monto_descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0, validators=[MinValueValidator(0.00)])
    usuario = models.ForeignKey("auth.User", on_delete=models.CASCADE)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="borrador")
    email_enviado = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-fecha", "-numero"]
        db_table = "cotizaciones_cotizacion"

    def save(self, *args, **kwargs):
        if not self.numero and not self.pk:
            tipo = "Recibo" if self.tipo_documento == "recibo" else "Cotización"
            ultimo = Cotizacion.objects.order_by("-id").first()
            n = (ultimo.id + 1) if ultimo else 1
            self.numero = f"{tipo} N° {n}"
        super().save(*args, **kwargs)

    def calcular_total(self):
        items = self.items.all()
        self.subtotal_bruto = sum(i.subtotal for i in items)
        self.monto_descuento = self.subtotal_bruto * (self.descuento_porcentaje / Decimal("100"))
        self.total = self.subtotal_bruto - self.monto_descuento
        self.save(update_fields=["subtotal_bruto", "monto_descuento", "total", "descuento_porcentaje"])
        return self.total

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse("cotizacion_detail", kwargs={"pk": self.pk})

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"


class CotizacionItem(models.Model):
    cotizacion = models.ForeignKey(Cotizacion, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey("productos.Producto", on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        verbose_name = "Item de Cotización"
        db_table = "cotizaciones_cotizacionitem"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)
        self.cotizacion.calcular_total()


class Recibo(models.Model):
    FORMA_PAGO_CHOICES = [
        ("efectivo", "Efectivo"), ("transferencia", "Transferencia Bancaria"),
        ("cheque", "Cheque"), ("tarjeta_debito", "Tarjeta Débito"),
        ("tarjeta_credito", "Tarjeta Crédito"), ("mercadopago", "Mercado Pago"),
        ("otro", "Otro"),
    ]

    numero = models.CharField(max_length=50, unique=True, db_index=True)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    fecha = models.DateField()
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    forma_pago = models.CharField(max_length=20, choices=FORMA_PAGO_CHOICES)
    observaciones = models.TextField(null=True, blank=True)
    usuario = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    history = HistoricalRecords()

    class Meta:
        ordering = ["-fecha", "-numero"]
        db_table = "cotizaciones_recibo"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = Recibo.objects.order_by("-id").first()
            n = (ultimo.id + 1) if ultimo else 1
            self.numero = f"RC-{n:04d}"
        super().save(*args, **kwargs)

    def actualizar_totales(self):
        self.total = sum(i.subtotal for i in self.items.all())
        self.save(update_fields=["total"])


class ReciboItem(models.Model):
    recibo = models.ForeignKey(Recibo, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey("productos.Producto", on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = "cotizaciones_reciboitem"

    def save(self, *args, **kwargs):
        self.subtotal = self.cantidad * self.precio_unitario
        super().save(*args, **kwargs)


class Remito(models.Model):
    ESTADO_CHOICES = [("pendiente", "Pendiente"), ("entregado", "Entregado"), ("cancelado", "Cancelado")]

    numero = models.CharField(max_length=50, unique=True)
    cliente = models.ForeignKey("clientes.Cliente", on_delete=models.CASCADE)
    fecha = models.DateField()
    direccion_entrega = models.TextField(null=True, blank=True)
    observaciones = models.TextField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default="pendiente")
    usuario = models.ForeignKey("auth.User", on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fecha", "-numero"]
        db_table = "cotizaciones_remito"

    def save(self, *args, **kwargs):
        if not self.numero:
            ultimo = Remito.objects.order_by("-id").first()
            n = (ultimo.id + 1) if ultimo else 1
            self.numero = f"R-{n:04d}"
        super().save(*args, **kwargs)


class RemitoItem(models.Model):
    remito = models.ForeignKey(Remito, on_delete=models.CASCADE, related_name="items")
    producto = models.ForeignKey("productos.Producto", on_delete=models.SET_NULL, null=True, blank=True)
    descripcion = models.CharField(max_length=255, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "cotizaciones_remitoitem"
