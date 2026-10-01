from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse

def login_view(request):
    error = None
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")
        
        if not User.objects.filter(username=email).exists():
            error = "El usuario no existe."
        else:
            # El usuario existe, ahora verificamos la contraseña
            user = authenticate(request, username=email, password=password)
            if user is not None:
                login(request, user)
                grupos_usuario = list(user.groups.values_list("name", flat=True))
                if not grupos_usuario:
                    error = "No perteneces a ningún grupo válido."
                    return redirect("Login")
                grupo = grupos_usuario[0]
                match grupo:
                    case "Gubernamental":
                        return redirect("Gobernacion")
                    case "Municipal":
                        return redirect("Municipalidad")
                    case "Encargado":
                        return redirect("Encargado")
                    case _:
                        error = "No perteneces a un grupo válido."
                        return redirect("Login")
            else:
                error = "La contraseña es incorrecta."
    
    return render(request, "index.html", {"error": error})

@login_required
def logout_g(request):
    logout(request)
    return redirect("Login")

def acceso_denegado(request):
    return render(request, "acceso_denegado.html")

def error_404(request, execption):
    return render(request, "404.html", status=404)