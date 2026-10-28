from django.urls import path
import Gubernamental.views as VG


#Rutas Gerente
urlpatterns = [
    path('', VG.inicio_gubernamental, name="Gobernacion"),

    #Gestion de municipios y sus administradores
    path('Municipios', VG.gestion_municipios, name="Municipios"),
    path('Municipios/Agregar-Municipio', VG.agregar_municipio, name="Agregar-Municipio"),
    path('Municipios/Eliminar-Municipio', VG.eliminar_municipio, name="Eliminar-Municipio"),

    #Gestion de Administradores
    path('Municipios/Agregar-Administrador', VG.agregar_administrador, name="Agregar-Administrador"),
    path('Municipios/Registrar-Administrador', VG.registrar_administrador, name="Registrar-Administrador"),
    path('Municipios/Eliminar-Administrador', VG.eliminar_administrador, name="Eliminar-Administrador"), 
    path('Municipios/Actualizar-Administrador/<int:id>/', VG.actualizar_administrador, name="Actualizar-Administrador"),

    #Historial de incidentes
    path('Reportes/', VG.reportes, name='Reportes'),
    path('Reportes/filtros/', VG.api_filtros, name='Reportes-Filtros'),
    path('Reportes/incidentes/', VG.api_incidentes, name='Reportes-Incidentes'),
    path('Reportes/incidente/<int:pk>/', VG.api_incidente_detalle, name='Reportes-Detalle'),
    path('Reportes/pdf/', VG.api_reporte_pdf, name='Reportes-pdf'),

    #Listado de incidentes
    path('Incidentes/', VG.reportes_l, name='Lista-Incidentes'),
    path('Incidentes/Filtros/', VG.api_filtros_l, name='Incidentes-Filtros-A'),
    path('Incidentes/Lista-Incidentes/', VG.api_incidentes_l, name='Reportes-Incidentes-A'),
    path('Incidentes/Detalle/<int:pk>/', VG.api_incidente_detalle_l, name='Reportes-Detalle-A'),

    #Actualizacion de datos del usuario
    path('Configuracion', VG.actualizar_usuario, name="Actualizar-Usuario-G"),
    
]