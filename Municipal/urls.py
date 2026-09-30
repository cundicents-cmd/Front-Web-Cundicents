from django.urls import path
import Municipal.views as VM


#Rutas Municipalidad
urlpatterns = [
    path('', VM.inicio_municipalidad, name="Municipalidad"),

    #Gestion de sectores
    path('Sectores', VM.gestion_sectores, name="Sectores"),
    path('Sectores/Crear-Sector', VM.crear_sector, name="Crear-Sector"),
    path("Municipalidad/Sectores/Ver/<int:sector_id>/",VM.ver_sector,name="Ver-Sector"), 
    path("Municipalidad/Sectores/Eliminar/<int:sector_id>/", VM.eliminar_sector, name="Eliminar-Sector"),

    #Gestion de encargados
    path('Encargados', VM.gestion_encargados, name="Encargados"),   
    path('Encargados/Agregar-Encargado', VM.agregar_encargado, name="Agregar-Encargado"),   
    path('Encargados/Eliminar-Encargado/<int:id_usuario>/', VM.eliminar_encargado, name="Eliminar-Encargado"),   

    #Actualizacion de datos del usuario
    path('Configuracion', VM.actualizar_usuario, name="Actualizar-Usuario"),
        
]
