from django.urls import path
from .views import ObtenerListaVigenteAPIView, CalcularPrecioFinalAPIView # Importa la nueva vista

# Estas son las "direcciones" específicas de nuestra app.
urlpatterns = [
    path(
        'obtener-lista-vigente/',
        ObtenerListaVigenteAPIView.as_view(),
        name='obtener-lista-vigente'
    ),

    # --- AÑADE ESTA NUEVA RUTA ---
    path(
        'calcular-precio/',
        CalcularPrecioFinalAPIView.as_view(),
        name='calcular-precio'
    ),
]

