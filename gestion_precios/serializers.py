from rest_framework import serializers
from .models import ListaPrecio, Articulo, PrecioArticulo
from decimal import Decimal

class ListaPrecioSerializer(serializers.ModelSerializer):
    # ... (esta clase se queda como está)
    class Meta:
        model = ListaPrecio
        fields = [
            'id',
            'nombre',
            'empresa',
            'sucursal',
            'canal_venta',
            'fecha_inicio_vigencia',
            'fecha_fin_vigencia',
            'estado',
        ]

# --- AÑADE ESTA NUEVA CLASE ---
class ResultadoCalculoSerializer(serializers.Serializer):
    """
    Serializador para mostrar el resultado del cálculo de precios.
    No se basa en un modelo, solo define la estructura de la respuesta.
    """
    lista_precio_aplicada = serializers.CharField()
    precio_base = serializers.DecimalField(max_digits=10, decimal_places=2)
    precio_final = serializers.DecimalField(max_digits=10, decimal_places=2)
    cantidad = serializers.IntegerField()
    total = serializers.DecimalField(max_digits=12, decimal_places=2)
    reglas_aplicadas = serializers.ListField(child=serializers.CharField())
    autorizado_bajo_costo = serializers.BooleanField()

