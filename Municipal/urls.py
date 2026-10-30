from django.urls import path
import Municipal.views as VM


#Rutas Municipalidad
urlpatterns = [
    path('', VM.inicio_municipalidad, name="Municipalidad"),
    path('Sectores-Consulta/', VM.sectores_municipalidad, name='Sectores-Municipalidad'),
    path('Graficas/pdf/', VM.reportes_graficas_pdf_m, name='Reportes-Graficas-PDF-Municipal'),
    
    #Gestion de sectores
    path('Sectores', VM.gestion_sectores, name="Sectores"),
    path('Sectores/Crear-Sector', VM.crear_sector, name="Crear-Sector"),
    path("Municipalidad/Sectores/Ver/<int:sector_id>/",VM.ver_sector,name="Ver-Sector"), 
    path("Municipalidad/Sectores/Eliminar/<int:sector_id>/", VM.eliminar_sector, name="Eliminar-Sector"),

    #Gestion de encargados
    path('Encargados', VM.gestion_encargados, name="Encargados"),   
    path('Encargados/Agregar-Encargado', VM.agregar_encargado, name="Agregar-Encargado"),   
    path('Encargados/Eliminar-Encargado/<int:id_usuario>/', VM.eliminar_encargado, name="Eliminar-Encargado"),   
    path('Encargados/Actualizar-Encargado/<int:id_usuario>/', VM.actualizar_encargado, name="Actualizar-Encargado"),   

    #Listado de incidentes
    path('Incidentes/', VM.reportes_a, name='Lista-Incidentes-M'),
    path('Incidentes/Filtros/', VM.api_filtros_a, name='Incidentes-Filtros-A-M'),
    path('Incidentes/Lista-Incidentes/', VM.api_incidentes_a, name='Reportes-Incidentes-A-M'),
    path('Incidentes/Detalle/<int:pk>/', VM.api_incidente_detalle_a, name='Reportes-Detalle-A-M'),
    

    #Historial de incidentes
    path('Reportes/', VM.reportes, name='Reportes-M'),
    path('Reportes/filtros/', VM.api_filtros, name='Reportes-Filtros-M'),
    path('Reportes/incidentes/', VM.api_incidentes, name='Reportes-Incidentes-M'),
    path('Reportes/incidente/<int:pk>/', VM.api_incidente_detalle, name='Reportes-Detalle-M'),
    path('Reportes/pdf/', VM.api_reporte_pdf, name='Reportes-pdf-M'),
      

    #Actualizacion de datos del usuario
    path('Configuracion', VM.actualizar_usuario, name="Actualizar-Usuario-M"),
        
]
