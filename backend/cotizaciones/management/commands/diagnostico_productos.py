from django.core.management.base import BaseCommand

from cotizaciones.models import Producto, Proveedor


class Command(BaseCommand):
    help = "Diagnóstico: muestra cuántos productos hay en la DB y su estado."

    def handle(self, *args, **kwargs):
        try:
            total = Producto.objects.count()
        except Exception as exc:
            self.stderr.write(self.style.ERROR(
                f"No se pudo consultar la tabla de productos: {exc}"
            ))
            return

        activos = Producto.objects.filter(activo=True).count()
        inactivos = Producto.objects.filter(activo=False).count()
        proveedores = Proveedor.objects.count()

        self.stdout.write("=== Diagnóstico de productos ===")
        self.stdout.write(f"Total productos: {total}")
        self.stdout.write(f"Activos: {activos}")
        self.stdout.write(f"Inactivos: {inactivos}")
        self.stdout.write(f"Proveedores: {proveedores}")

        if total == 0:
            self.stdout.write(self.style.WARNING(
                "No hay productos cargados. El buscador (modal) y el listado "
                "quedan vacíos porque no hay datos que mostrar."
            ))
        elif activos == 0:
            self.stdout.write(self.style.WARNING(
                "Hay productos pero TODOS están inactivos. El buscador del modal "
                "solo muestra productos activos (activo=True)."
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                f"Hay {activos} productos activos. El buscador debería mostrarlos."
            ))

        muestra = list(
            Producto.objects.order_by("-id")[:5].values("id", "nombre", "activo", "precio_unitario")
        )
        for p in muestra:
            self.stdout.write(f"  - id={p['id']} activo={p['activo']} precio={p['precio_unitario']} {p['nombre']}")
