from django.contrib import admin
from .models import (
    Empresa,
    Sucursal,
    LineaArticulo,
    GrupoArticulo,
    Articulo,
    ListaPrecio,
    PrecioArticulo, 
    ReglaPrecio,
)

# Registramos cada modelo aquí para que aparezca en el panel de administración.
# Esto nos permitirá crear, ver, actualizar y eliminar registros fácilmente.

admin.site.register(Empresa)
admin.site.register(Sucursal)
admin.site.register(LineaArticulo)
admin.site.register(GrupoArticulo)
admin.site.register(Articulo)
admin.site.register(ListaPrecio)
admin.site.register(PrecioArticulo)
admin.site.register(ReglaPrecio)
