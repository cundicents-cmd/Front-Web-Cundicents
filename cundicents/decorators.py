from django.contrib.auth.decorators import login_required
from functools import wraps
from django.shortcuts import redirect

def group_required(group_name):
    def decorator(view_func):
        @wraps(view_func)
        @login_required  # Asegura que el usuario esté autenticado
        def _wrapped_view(request, *args, **kwargs):
            user = request.user
            # Verifica si pertenece al grupo correcto
            if user.groups.filter(name=group_name).exists():
                return view_func(request, *args, **kwargs)
            # Si no pertenece, retorna error 403
            return redirect('no_autorizado')
        return _wrapped_view
    return decorator
