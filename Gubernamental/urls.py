from django.urls import path
import Gubernamental.views as VG


#Rutas Gerente
urlpatterns = [
    path('', VG.inicio_gubernamental, name="Gubernamental"),

    #Gestion de municipios y sus administradores
    path('Municipios', VG.gestion_municipios, name="Municipios"),
    path('Municipios/Agregar-Municipio', VG.agregar_municipio, name="Agregar-Municipio"),
    path('Municipios/Eliminar-Municipio', VG.eliminar_municipio, name="Eliminar-Municipio"),


    #Gestion de Administradores
    path('Municipios/Agregar-Administrador', VG.agregar_administrador, name="Agregar-Administrador"),
    path('Municipios/Registrar-Administrador', VG.registrar_administrador, name="Registrar-Administrador"),
    path('Municipios/Eliminar-Administrador', VG.eliminar_administrador, name="Eliminar-Administrador"),         
]