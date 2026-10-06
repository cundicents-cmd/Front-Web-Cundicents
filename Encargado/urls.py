from django.urls import path
import Encargado.views as VE

# Rutas Encargado
urlpatterns = [
    # Inicio / Dashboard de Encargado
    path('', VE.inicio_encargado, name="Encargado"), 

    # Actualización / Ver datos del usuario
    path('Configuracion', VE.actualizar_usuario, name="Actualizar-Usuario-E"),
]

