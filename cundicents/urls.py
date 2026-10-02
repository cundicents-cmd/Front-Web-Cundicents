"""
URL configuration for cundicents project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/6.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
import Login.views as LV

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', LV.login_view, name="Login"),
    path('Logout', LV.logout_g, name="Logout"),
    path('No-Autorizado/', LV.error_403, name='No-Autorizado'),
    path('No-Encontrado/', LV.error_404, name='404'),
    
    #Rutas recuperacion de contraseña
    path('Recuperacion-Contraseña/', LV.recuperar_contrasena, name='Recuperacion-Contraseña'),
    path('Recuperacion-Contraseña/Enviar-Codigo-Recuperacion', LV.enviar_codigo_recuperacion, name='Enviar-Codigo-Recuperacion'),
    path('Recuperacion-Contraseña/Verificar-Codigo/',LV.verificar_codigo_recuperacion,  name='Verificar-Codigo-Recuperacion'),
    path('Recuperacion-Contraseña/Actualizar/',LV.actualizar_contrasena, name='Actualizar-Contrasena'),
        

    #Rutas Gubernamentales, Municipalidad y Encargados
    path('Gobernacion/',include("Gubernamental.urls")),
    path('Municipalidad/',include("Municipal.urls")),
    path('Encargado/',include("Encargado.urls")),
]
