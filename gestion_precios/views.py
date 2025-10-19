from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions

from .services import PrecioService
from .serializers import ListaPrecioSerializer, ResultadoCalculoSerializer # Importa el nuevo serializer

class ObtenerListaVigenteAPIView(APIView):
    """
    Endpoint para obtener la lista de precios vigente según los parámetros.
    """
    def get(self, request, *args, **kwargs):
        """
        Maneja las peticiones GET.
        Espera los siguientes parámetros en la URL (query params):
        - empresa_id (requerido)
        - canal_venta (requerido)
        - sucursal_id (opcional)
        """
        # 1. Obtener parámetros de la URL
        empresa_id = request.query_params.get('empresa_id')
        canal_venta = request.query_params.get('canal_venta')
        sucursal_id = request.query_params.get('sucursal_id')

        # 2. Validar que los parámetros requeridos existan
        if not empresa_id or not canal_venta:
            return Response(
                {"error": "Los parámetros 'empresa_id' y 'canal_venta' son requeridos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 3. Llamar a nuestro "cerebro" (el servicio)
        try:
            lista_vigente = PrecioService.obtener_lista_vigente(
                empresa_id=int(empresa_id),
                canal_venta=canal_venta.upper(), # Convertimos a mayúsculas por si acaso
                sucursal_id=int(sucursal_id) if sucursal_id else None
            )
        except (ValueError, TypeError):
             return Response(
                {"error": "Los IDs deben ser números enteros válidos."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 4. Preparar y enviar la respuesta
        if lista_vigente:
            # Si encontramos una lista, la "traducimos" con el serializer
            serializer = ListaPrecioSerializer(lista_vigente)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            # Si el servicio no encontró nada, respondemos con un error 404
            return Response(
                {"mensaje": "No se encontró una lista de precios aplicable para los criterios dados."},
                status=status.HTTP_404_NOT_FOUND
            )

# --- AÑADE ESTA NUEVA CLASE ---
class CalcularPrecioFinalAPIView(APIView):
    """
    Endpoint para calcular el precio final de un artículo.
    """
    def get(self, request, *args, **kwargs):
        # 1. Obtener parámetros (ahora incluimos articulo_id y cantidad)
        empresa_id = request.query_params.get('empresa_id')
        canal_venta = request.query_params.get('canal_venta')
        sucursal_id = request.query_params.get('sucursal_id')
        articulo_id = request.query_params.get('articulo_id')
        cantidad = request.query_params.get('cantidad')

        # 2. Validar
        required_params = {'empresa_id': empresa_id, 'canal_venta': canal_venta, 'articulo_id': articulo_id, 'cantidad': cantidad}
        for param, value in required_params.items():
            if not value:
                return Response({"error": f"El parámetro '{param}' es requerido."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Llamar al nuevo método del servicio
        try:
            resultado = PrecioService.calcular_precio_final(
                empresa_id=int(empresa_id),
                canal_venta=canal_venta.upper(),
                sucursal_id=int(sucursal_id) if sucursal_id else None,
                articulo_id=int(articulo_id),
                cantidad=int(cantidad)
            )
        except (ValueError, TypeError):
            return Response({"error": "Los IDs y la cantidad deben ser números enteros válidos."}, status=status.HTTP_400_BAD_REQUEST)

        # 4. Enviar respuesta
        if "error" in resultado:
            return Response(resultado, status=status.HTTP_404_NOT_FOUND)
        else:
            serializer = ResultadoCalculoSerializer(resultado)
            return Response(serializer.data, status=status.HTTP_200_OK)

