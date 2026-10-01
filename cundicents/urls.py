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
    path('No-Autorizado/', LV.acceso_denegado, name='no_autorizado'),
    path('No-Encontrado/', LV.error_404, name='404'),
    
    #Rutas Gubernamentales, Municipalidad y Encargados
    path('Gobernacion/',include("Gubernamental.urls")),
    path('Municipalidad/',include("Municipal.urls")),
    path('Encargado/',include("Encargado.urls")),
]
handler404 = LV.error_404
