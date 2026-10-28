from django.urls import path
import Encargado.views as VE

# Rutas Encargado
urlpatterns = [
    # Inicio / Dashboard de Encargado
    path('', VE.inicio_encargado, name="Encargado"), 

    #Lista de Incidentes
    path('Lista-Incidentes-E/', VE.reportes_a, name='Lista-Incidentes-E'),
    path('api/Incidentes-Filtros-a/',VE.api_filtros_a, name='Incidentes-Filtros-A-E'),
    path('api/Reportes-Incidentes-a/', VE.api_incidentes_a, name='Reportes-Incidentes-A-E'),
    path('api/Reportes-Detalle-a/<int:pk>/', VE.api_incidente_detalle_a, name='Reportes-Detalle-A-E'),
    path('api/Actualizar-Incidente-a/<int:pk>/', VE.api_actualizar_incidente_a, name='Actualizar-Incidente-A-E'),

    # Actualización / Ver datos del usuario
    path('Configuracion', VE.actualizar_usuario, name="Actualizar-Usuario-E"),
]

