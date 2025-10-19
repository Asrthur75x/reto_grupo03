from datetime import date
from django.db.models import Q
from .models import ListaPrecio, Articulo, PrecioArticulo
from decimal import Decimal

class PrecioService:
    """
    Clase que encapsula toda la lógica de negocio para el cálculo de precios.
    """

    @staticmethod
    def calcular_precio_final(empresa_id: int, canal_venta: str, articulo_id: int, cantidad: int, sucursal_id: int = None):
        """
        Calcula el precio final para un artículo, aplicando la lista y reglas correspondientes.

        Returns:
            dict: Un diccionario con el resultado del cálculo o con un error.
        """
        # 1. Reutilizamos la función que ya teníamos para encontrar la lista correcta
        lista_vigente = PrecioService.obtener_lista_vigente(
            empresa_id=empresa_id,
            canal_venta=canal_venta,
            sucursal_id=sucursal_id
        )

        if not lista_vigente:
            return {"error": "No se encontró una lista de precios aplicable.", "precio_final": None}

        # 2. Buscamos el precio base del artículo DENTRO de la lista encontrada
        try:
            precio_articulo = PrecioArticulo.objects.get(
                lista_precio=lista_vigente,
                articulo_id=articulo_id
            )
            precio_base = precio_articulo.precio_base
        except PrecioArticulo.DoesNotExist:
            return {"error": f"El artículo ID {articulo_id} no tiene un precio base definido en la lista '{lista_vigente.nombre}'.", "precio_final": None}

        # --- Lógica de Reglas (Próximo paso) ---
        # Por ahora, el precio final es simplemente el precio base.
        # Aquí es donde en el futuro aplicaremos descuentos por cantidad, etc.
        precio_final = precio_base
        reglas_aplicadas = [] # Lista para guardar las reglas que se usen

        # 3. Validamos contra el costo (como pedía la especificación)
        # Por ahora, simplemente devolvemos la información.
        autorizado_bajo_costo = False
        if precio_final < precio_articulo.articulo.ultimo_costo:
            autorizado_bajo_costo = True # En un futuro, aquí iría lógica de permisos

        # 4. Devolvemos un diccionario con toda la información
        return {
            "lista_precio_aplicada": lista_vigente.nombre,
            "precio_base": precio_base,
            "precio_final": precio_final,
            "cantidad": cantidad,
            "total": precio_final * cantidad,
            "reglas_aplicadas": reglas_aplicadas,
            "autorizado_bajo_costo": autorizado_bajo_costo
        }


    @staticmethod
    def obtener_lista_vigente(empresa_id: int, canal_venta: str, sucursal_id: int = None):
        """
        Encuentra la lista de precios más específica y aplicable para una operación.
        """
        # ... (este método se queda exactamente como estaba)
        hoy = date.today()

        filtros_base = Q(empresa_id=empresa_id) & \
                       Q(estado='ACTIVA') & \
                       Q(fecha_inicio_vigencia__lte=hoy) & \
                       (Q(fecha_fin_vigencia__gte=hoy) | Q(fecha_fin_vigencia__isnull=True))

        if sucursal_id:
            lista = ListaPrecio.objects.filter(
                filtros_base &
                Q(sucursal_id=sucursal_id) &
                Q(canal_venta=canal_venta)
            ).first()
            if lista:
                return lista

            lista = ListaPrecio.objects.filter(
                filtros_base &
                Q(sucursal_id=sucursal_id) &
                Q(canal_venta='TODOS')
            ).first()
            if lista:
                return lista

        lista = ListaPrecio.objects.filter(
            filtros_base &
            Q(sucursal_id__isnull=True) &
            Q(canal_venta=canal_venta)
        ).first()
        if lista:
            return lista

        lista = ListaPrecio.objects.filter(
            filtros_base &
            Q(sucursal_id__isnull=True) &
            Q(canal_venta='TODOS')
        ).first()
        if lista:
            return lista

        return None

