from rest_framework import serializers
from django.db.models import Q
from datetime import date
from .models import (
    Empresa, Sucursal, LineaArticulo, GrupoArticulo, Articulo,
    ListaPrecio, PrecioArticulo, ReglaPrecio, CombinacionProducto
)
from decimal import Decimal

class ArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Articulo
        fields = '__all__' # Expondrá todos los campos del modelo

class PrecioArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = PrecioArticulo
        fields = '__all__'

class ReglaPrecioSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReglaPrecio
        fields = '__all__' # (Esto se queda igual)

    def validate(self, data):
        """
        Validación personalizada para evitar reglas duplicadas.
        """
        # Definimos los campos que determinan la unicidad de una regla
        campos_unicos = [
            'lista_precio', 'tipo_regla', 'condicion', 'condicion_valor',
            'aplica_articulo', 'aplica_grupo', 'aplica_linea', 'aplica_combinacion'
        ]
        
        # Construimos el filtro con los datos que se están intentando guardar
        filtro_duplicados = {}
        for campo in campos_unicos:
            if campo in data:
                filtro_duplicados[campo] = data.get(campo)
        
        # Buscamos si ya existe una regla con esos mismos valores
        query = ReglaPrecio.objects.filter(**filtro_duplicados)

        # Si estamos actualizando (PUT/PATCH), debemos excluirnos a nosotros mismos
        if self.instance:
            query = query.exclude(pk=self.instance.pk)

        if query.exists():
            regla_existente = query.first()
            raise serializers.ValidationError(
                f"Ya existe una regla idéntica con estos criterios: "
                f"'{regla_existente.nombre_regla}' (ID: {regla_existente.id})"
            )

        return data

class CombinacionProductoSerializer(serializers.ModelSerializer):
    class Meta:
        model = CombinacionProducto
        fields = '__all__'

# Serializers para los modelos base (opcional pero recomendado)
class EmpresaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Empresa
        fields = '__all__'

class SucursalSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sucursal
        fields = '__all__'

class LineaArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = LineaArticulo
        fields = '__all__'

class GrupoArticuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = GrupoArticulo
        fields = '__all__'

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
            'activa',
        ]
    def validate(self, data):
        """
        Validación personalizada para evitar solapamiento de vigencias.
        """
        # Obtenemos las fechas. Si no hay fecha fin, la tratamos como "infinito"
        inicio = data.get('fecha_inicio_vigencia')
        fin = data.get('fecha_fin_vigencia')

        # Construimos el filtro base para listas que compiten
        filtros_competencia = Q(empresa=data.get('empresa')) & \
                              Q(sucursal=data.get('sucursal')) & \
                              Q(canal_venta=data.get('canal_venta')) & \
                              Q(activa=True)

        # Lógica de solapamiento
        # 1. Comprueba si la nueva lista "envuelve" a una existente
        consulta_solapamiento = Q(fecha_inicio_vigencia__gte=inicio)
        if fin:
            consulta_solapamiento &= Q(fecha_fin_vigencia__lte=fin)
        
        # 2. Comprueba si la nueva lista "inicia durante" una existente
        consulta_inicia_durante = Q(fecha_inicio_vigencia__lte=inicio)
        if fin:
             consulta_inicia_durante &= Q(fecha_fin_vigencia__gte=inicio)
        else:
            # Si la nueva lista no tiene fin, choca con cualquiera
            # que no haya terminado antes de que esta empiece.
             consulta_inicia_durante &= Q(fecha_fin_vigencia__gte=inicio) | Q(fecha_fin_vigencia__isnull=True)

        # 3. Comprueba si la nueva lista "termina durante" una existente
        consulta_termina_durante = Q(fecha_inicio_vigencia__isnull=False) # Solo aplica si la nueva tiene fin
        if fin:
            consulta_termina_durante = Q(fecha_inicio_vigencia__lte=fin) & \
                                       (Q(fecha_fin_vigencia__gte=fin) | Q(fecha_fin_vigencia__isnull=True))
        
        filtros_solapamiento = Q(consulta_solapamiento | consulta_inicia_durante | consulta_termina_durante)

        # Excluimos el objeto actual si estamos actualizando (PUT/PATCH)
        instancia_actual = self.instance
        query = ListaPrecio.objects.filter(filtros_competencia & filtros_solapamiento)
        
        if instancia_actual:
            query = query.exclude(pk=instancia_actual.pk) # No te compares contigo mismo

        if query.exists():
            lista_existente = query.first()
            raise serializers.ValidationError(
                f"Las fechas se solapan con una lista de precios existente: "
                f"'{lista_existente.nombre}' (ID: {lista_existente.id})"
            )

        return data
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

