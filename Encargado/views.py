from django.shortcuts import render
from cundicents.decorators import group_required

@group_required("Encargado")
def inicio_encargado(request):
    return render(request, "inicio_e.html")
