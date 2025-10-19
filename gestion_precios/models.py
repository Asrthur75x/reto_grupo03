from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone

# -----------------------------------------------------------------------------
# 1. MODELOS BASE (Prerrequisitos mencionados en el documento)
# Estos son los modelos con los que nuestro sistema de precios se integrará.
# Si ya existen en tu proyecto, puedes ignorar esta sección o adaptarla.
# -----------------------------------------------------------------------------

class Empresa(models.Model):
    """Representa una empresa en el sistema."""
    nombre = models.CharField(max_length=255, unique=True)
    ruc = models.CharField(max_length=11, unique=True, blank=True, null=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.nombre

class Sucursal(models.Model):
    """Representa una sucursal de una empresa."""
    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='sucursales')
    nombre = models.CharField(max_length=255)
    direccion = models.CharField(max_length=255, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('empresa', 'nombre') # No puede haber dos sucursales con el mismo nombre en una empresa

    def __str__(self):
        return f"{self.empresa.nombre} - {self.nombre}"

class LineaArticulo(models.Model):
    """Ej: Línea Blanca, Electrónica, etc."""
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.nombre

class GrupoArticulo(models.Model):
    """Ej: Televisores, Refrigeradores, etc."""
    linea_articulo = models.ForeignKey(LineaArticulo, on_delete=models.PROTECT, related_name='grupos')
    nombre = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return f"{self.linea_articulo.nombre} - {self.nombre}"

class Articulo(models.Model):
    """Representa un producto o artículo."""
    sku = models.CharField(max_length=50, unique=True, help_text="Stock Keeping Unit")
    nombre = models.CharField(max_length=255)
    grupo_articulo = models.ForeignKey(GrupoArticulo, on_delete=models.PROTECT, related_name='articulos')
    ultimo_costo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} - {self.nombre}"

# -----------------------------------------------------------------------------
# 2. MODELOS CENTRALES (Núcleo del sistema de gestión de precios)
# Estos modelos implementan la lógica descrita en la especificación funcional.
# -----------------------------------------------------------------------------

class ListaPrecio(models.Model):
    """
    Define una lista de precios, asociada a una empresa/sucursal y con una vigencia.
    """
    CANAL_VENTA_CHOICES = [
        ('TIENDA', 'Tienda Física'),
        ('ECOMMERCE', 'E-Commerce'),
        ('MAYORISTA', 'Mayorista'),
        ('TELEVENTA', 'Televenta'),
        ('TODOS', 'Todos los Canales'),
    ]
    ESTADO_CHOICES = [
        ('ACTIVA', 'Activa'),
        ('INACTIVA', 'Inactiva'),
        ('PROGRAMADA', 'Programada'),
    ]

    empresa = models.ForeignKey(Empresa, on_delete=models.CASCADE, related_name='listas_precio')
    sucursal = models.ForeignKey(Sucursal, on_delete=models.CASCADE, related_name='listas_precio', blank=True, null=True, help_text="Si es nulo, aplica a toda la empresa")
    nombre = models.CharField(max_length=255)
    canal_venta = models.CharField(max_length=20, choices=CANAL_VENTA_CHOICES, default='TODOS')
    fecha_inicio_vigencia = models.DateField()
    fecha_fin_vigencia = models.DateField(blank=True, null=True, help_text="Si es nulo, no tiene fecha de fin.")
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='ACTIVA')
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    def clean(self):
        # Validación para no solapar vigencias (lógica más compleja se implementará en servicios)
        if self.fecha_fin_vigencia and self.fecha_inicio_vigencia > self.fecha_fin_vigencia:
            raise ValidationError('La fecha de inicio de vigencia no puede ser posterior a la fecha de fin.')

    def __str__(self):
        sucursal_str = self.sucursal.nombre if self.sucursal else "Toda la Empresa"
        return f"{self.nombre} ({self.empresa.nombre} - {sucursal_str})"

class PrecioArticulo(models.Model):
    """
    Define el precio base de un artículo dentro de una lista de precios específica.
    """
    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='precios_articulos')
    articulo = models.ForeignKey(Articulo, on_delete=models.CASCADE, related_name='precios_en_listas')
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    
    class Meta:
        unique_together = ('lista_precio', 'articulo') # Un artículo solo puede tener un precio base por lista

    def clean(self):
        # Validación básica de costo, la autorización se manejará en la lógica de negocio.
        if self.precio_base < self.articulo.ultimo_costo:
            # En un sistema real, aquí se podría generar una alerta o requerir un campo de "autorización"
            print(f"Advertencia: El precio base {self.precio_base} para {self.articulo.nombre} es inferior al último costo {self.articulo.ultimo_costo}.")

    def __str__(self):
        return f"{self.articulo.nombre} - S/ {self.precio_base} en lista '{self.lista_precio.nombre}'"


class ReglaPrecio(models.Model):
    """
    Define las políticas comerciales dinámicas o reglas de descuento/recargo.
    """
    TIPO_REGLA_CHOICES = [
        ('ESCALA_UNIDADES', 'Por Escala de Unidades'),
        ('MONTO_TOTAL_PEDIDO', 'Por Monto Total del Pedido'),
        ('COMBINACION_PRODUCTOS', 'Por Combinación de Productos'),
        # Podríamos añadir más en el futuro
    ]
    TIPO_AJUSTE_CHOICES = [
        ('PORCENTAJE_DSCTO', 'Porcentaje de Descuento'),
        ('MONTO_FIJO_DSCTO', 'Monto Fijo de Descuento'),
        ('PRECIO_FINAL_FIJO', 'Precio Final Fijo'),
    ]

    lista_precio = models.ForeignKey(ListaPrecio, on_delete=models.CASCADE, related_name='reglas')
    nombre_regla = models.CharField(max_length=255)
    tipo_regla = models.CharField(max_length=30, choices=TIPO_REGLA_CHOICES)
    tipo_ajuste = models.CharField(max_length=30, choices=TIPO_AJUSTE_CHOICES)
    valor_ajuste = models.DecimalField(max_digits=10, decimal_places=2, help_text="El valor del descuento o precio final")
    
    # Condiciones para aplicar la regla
    min_unidades = models.PositiveIntegerField(blank=True, null=True, help_text="Para 'ESCALA_UNIDADES'")
    max_unidades = models.PositiveIntegerField(blank=True, null=True, help_text="Para 'ESCALA_UNIDADES'")
    min_monto_pedido = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True, help_text="Para 'MONTO_TOTAL_PEDIDO'")
    
    # Relaciones para reglas de combinación (opcional)
    # Un artículo específico puede activar esta regla
    articulo_condicion = models.ForeignKey(Articulo, on_delete=models.SET_NULL, blank=True, null=True, related_name='reglas_condicion')
    # O un grupo de artículos puede activarla
    grupo_articulo_condicion = models.ForeignKey(GrupoArticulo, on_delete=models.SET_NULL, blank=True, null=True, related_name='reglas_condicion')

    prioridad = models.PositiveIntegerField(default=10, help_text="Menor número = mayor prioridad de aplicación")

    def __str__(self):
        return f"Regla '{self.nombre_regla}' para lista '{self.lista_precio.nombre}'"

