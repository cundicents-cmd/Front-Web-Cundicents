import json, re
from django.conf import settings
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.shortcuts import render, redirect
from django.contrib import messages
from django.db import connection
from django.contrib.auth import update_session_auth_hash
from cundicents.decorators import group_required
from .models import verUsuarioEncargado, ver_Usuario_Municipio_Responsabilidad, VerListaIncidentes, VerReportes, VerMunicipios

@group_required("Encargado")
def inicio_encargado(request):
    return render(request, "inicio_e.html")

#Views de Lista de incidentes acticos
def _limpiar(valor):
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == '' or valor.lower() == 'todos':
        return None
    return valor

def _a_decimal(valor):
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None

def _a_estructura(valor):
    if valor is None:
        return None
    if isinstance(valor, (list, dict)):
        return valor
    if isinstance(valor, str):
        texto = valor.strip()
        if not texto:
            return None
        try:
            return json.loads(texto)
        except (ValueError, TypeError):
            return None
    return None

def _extraer_evidencias(evidencias):
    datos = _a_estructura(evidencias)
    if datos is None:
        return []

    try:
        media_url = getattr(settings, 'MEDIA_URL', '') or '/media/'
    except Exception:
        media_url = '/media/'
    if not media_url.startswith(('http://', 'https://', '/')):
        media_url = '/' + media_url
    if not media_url.endswith('/'):
        media_url += '/'

    def _normalizar(valor):
        if not isinstance(valor, str):
            return None
        texto = valor.strip()
        if not texto:
            return None
        if texto.startswith(('http://', 'https://', '//')):
            return texto
        if texto.startswith('/'):
            return texto
        if texto.startswith(('media/', 'static/')):
            return '/' + texto
        return media_url + texto.lstrip('/')

    def _orden_sufijo(clave):
        coincidencia = re.search(r'(\d+)\s*$', str(clave))
        return int(coincidencia.group(1)) if coincidencia else 10 ** 9

    encontradas = []
    if isinstance(datos, dict):
        for clave in sorted(datos.keys(), key=lambda k: (_orden_sufijo(k), str(k))):
            url = _normalizar(datos.get(clave))
            if url:
                encontradas.append(url)
            if len(encontradas) >= 4:
                break
    elif isinstance(datos, (list, tuple)):
        for valor in datos:
            url = _normalizar(valor)
            if url:
                encontradas.append(url)
            if len(encontradas) >= 4:
                break

    vistas, salida = set(), []
    for url in encontradas:
        if url not in vistas:
            vistas.add(url)
            salida.append(url)
    return salida

def _extraer_coordenadas(ubicacion):
    datos = _a_estructura(ubicacion)
    if datos is None:
        return None

    lat = lng = None

    if isinstance(datos, dict):
        claves = {str(k).lower(): v for k, v in datos.items()}
        for clave in ('lat', 'latitud', 'latitude', 'y'):
            if clave in claves:
                lat = _a_decimal(claves[clave])
                if lat is not None:
                    break
        for clave in ('lng', 'lon', 'long', 'longitud', 'longitude', 'x'):
            if clave in claves:
                lng = _a_decimal(claves[clave])
                if lng is not None:
                    break
        if (lat is None or lng is None) and isinstance(claves.get('coordinates'), (list, tuple)):
            coords = claves['coordinates']
            if len(coords) >= 2:
                lng = _a_decimal(coords[0])
                lat = _a_decimal(coords[1])
        if lat is None or lng is None:
            lat = lng = None
            for valor in datos.values():
                if isinstance(valor, (dict, list)):
                    sub = _extraer_coordenadas(valor)
                    if sub:
                        return sub
    elif isinstance(datos, (list, tuple)) and len(datos) >= 2:
        a, b = _a_decimal(datos[0]), _a_decimal(datos[1])
        if a is not None and b is not None:
            if abs(a) <= 90 and abs(b) <= 180:
                lat, lng = a, b
            elif abs(b) <= 90 and abs(a) <= 180:
                lat, lng = b, a

    if lat is None or lng is None:
        return None
    if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
        return None
    if lat == 0 and lng == 0:
        return None
    return lat, lng

def _contexto_incidentes_del_usuario(request):
    relacion = (
        ver_Usuario_Municipio_Responsabilidad.objects
        .filter(id_usuario=request.user.id)
        .first()
    )
    if relacion is None:
        return None, []

    id_municipio    = relacion.id_municipio
    id_tp_incidente = relacion.id_tp_incidente

    if not id_municipio:
        return None, []

    if id_tp_incidente is None:
        return id_municipio, []

    ids_incidentes_visibles = list(
        VerListaIncidentes.objects
        .filter(id_tp_incidente=id_tp_incidente)
        .values_list('id', flat=True)
    )

    return id_municipio, ids_incidentes_visibles

def _municipio_del_usuario(request):
    relacion = (
        ver_Usuario_Municipio_Responsabilidad.objects
        .filter(id_usuario=request.user.id)
        .first()
    )
    if not relacion:
        return None
    try:
        return VerMunicipios.objects.filter(id_municipio=relacion.id_municipio).first()
    except Exception:
        return None

def _catalogo_prioridades():
    return [
        {'id': 1, 'nombre': 'Muy baja'},
        {'id': 2, 'nombre': 'Baja'},
        {'id': 3, 'nombre': 'Media'},
        {'id': 4, 'nombre': 'Alta'},
        {'id': 5, 'nombre': 'Crítica'},
    ]

def _catalogo_estados():
    return [
        {'id': 1, 'nombre': 'Pendiente'},
        {'id': 2, 'nombre': 'En revisión'},
        {'id': 3, 'nombre': 'Solucionando'},
    ]

def _queryset_filtrado_a(request):
    id_municipio, ids_incidentes_visibles = _contexto_incidentes_del_usuario(request)

    if id_municipio is None:
        return VerReportes.objects.none()
    if not ids_incidentes_visibles:
        return VerReportes.objects.none()

    qs = VerReportes.objects.filter(
        id_municipio=id_municipio,
        id_incidente__in=ids_incidentes_visibles,
    )

    sector       = _limpiar(request.GET.get('sector'))
    incidente    = _limpiar(request.GET.get('incidente'))
    id_prioridad = _limpiar(request.GET.get('id_prioridad'))
    id_estado    = _limpiar(request.GET.get('id_estado'))

    if sector:
        qs = qs.filter(sector=sector)
    if incidente:
        qs = qs.filter(incidente=incidente)

    if id_prioridad is not None:
        try:
            qs = qs.filter(id_prioridad=int(id_prioridad))
        except (TypeError, ValueError):
            pass

    if id_estado is not None:
        try:
            qs = qs.filter(id_estado=int(id_estado))
        except (TypeError, ValueError):
            pass

    return qs.order_by('-id_prioridad', '-fecha_hora')

@group_required("Encargado")
def reportes_a(request):
    return render(request, 'lista_reportes_e.html')

@group_required("Encargado")
def api_filtros_a(request):
    try:
        id_municipio, ids_incidentes_visibles = _contexto_incidentes_del_usuario(request)

        if id_municipio is None or not ids_incidentes_visibles:
            return JsonResponse({
                'ok': True, 'municipio': '',
                'sectores': [], 'incidentes': [],
                'prioridades': _catalogo_prioridades(),
                'estados': _catalogo_estados(),
            })

        base = VerReportes.objects.filter(
            id_municipio=id_municipio,
            id_incidente__in=ids_incidentes_visibles,
        )

        def distintos(campo):
            vals = (base.exclude(**{campo + '__isnull': True})
                        .exclude(**{campo: ''})
                        .values_list(campo, flat=True)
                        .order_by(campo)
                        .distinct())
            out = set()
            for v in vals:
                if v is None:
                    continue
                v = str(v).strip()
                if v:
                    out.add(v)
            return sorted(out, key=lambda s: s.lower())

        municipio_obj = _municipio_del_usuario(request)
        return JsonResponse({
            'ok': True,
            'municipio': municipio_obj.municipio if municipio_obj else '',
            'sectores': distintos('sector'),
            'incidentes': distintos('incidente'),
            'prioridades': _catalogo_prioridades(),
            'estados': _catalogo_estados(),
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Encargado")
def api_incidentes_a(request):
    try:
        registros = _queryset_filtrado_a(request)
        data = [{
            'id': r.id,
            'municipio': r.municipio or '',
            'sector': r.sector or '',
            'prioridad': r.tp_prioridad or '',
            'id_prioridad': r.id_prioridad,
            'incidente': r.incidente or '',
            'estado': r.estado or '',
            'id_estado': r.id_estado,
            'fecha_hora': r.fecha_hora.isoformat() if r.fecha_hora else None,
        } for r in registros]
        return JsonResponse({'ok': True, 'total': len(data), 'registros': data})
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Encargado")
def api_incidente_detalle_a(request, pk):
    try:
        id_municipio, ids_incidentes_visibles = _contexto_incidentes_del_usuario(request)
        if id_municipio is None:
            return JsonResponse(
                {'ok': False, 'error': 'El usuario no tiene un municipio asignado.'},
                status=403,
            )

        registro = (VerReportes.objects
                    .filter(pk=pk, id_municipio=id_municipio)
                    .first())
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'El incidente no existe o no pertenece a su municipio.'},
                status=404,
            )

        if registro.id_incidente not in ids_incidentes_visibles:
            return JsonResponse(
                {'ok': False, 'error': 'No tiene permisos sobre este incidente.'},
                status=403,
            )

        coordenadas = _extraer_coordenadas(registro.ubicacion)

        return JsonResponse({
            'ok': True,
            'registro': {
                'id': registro.id,
                'usuario': registro.usuario or '',
                'municipio': registro.municipio or '',
                'sector': registro.sector or '',
                'prioridad': registro.tp_prioridad or '',
                'id_prioridad': registro.id_prioridad,
                'incidente': registro.incidente or '',
                'estado': registro.estado or '',
                'id_estado': registro.id_estado,
                'descripcion': registro.descripcion or '',
                'fecha_hora': registro.fecha_hora.isoformat() if registro.fecha_hora else None,
                'lat': coordenadas[0] if coordenadas else None,
                'lng': coordenadas[1] if coordenadas else None,
                'evidencias': _extraer_evidencias(registro.evidencias),
            },
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Encargado")
@require_POST
def api_actualizar_incidente_a(request, pk):
    try:
        id_municipio, ids_incidentes_visibles = _contexto_incidentes_del_usuario(request)
        if id_municipio is None:
            return JsonResponse(
                {'ok': False, 'error': 'Usuario sin municipio asignado.'},
                status=403,
            )

        registro = (VerReportes.objects
                    .filter(pk=pk, id_municipio=id_municipio)
                    .first())
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'Incidente no encontrado o fuera de su municipio.'},
                status=404,
            )

        if registro.id_incidente not in ids_incidentes_visibles:
            return JsonResponse(
                {'ok': False, 'error': 'No tiene permisos sobre este incidente.'},
                status=403,
            )

        try:
            id_prioridad = int(request.POST.get('id_prioridad'))
            id_estado    = int(request.POST.get('id_estado'))
        except (TypeError, ValueError):
            return JsonResponse({'ok': False, 'error': 'Parámetros inválidos.'}, status=400)

        if id_prioridad not in (1, 2, 3, 4, 5):
            return JsonResponse({'ok': False, 'error': 'Prioridad inválida.'}, status=400)
        if id_estado not in (1, 2, 3, 4):
            return JsonResponse({'ok': False, 'error': 'Estado inválido.'}, status=400)

        with connection.cursor() as cursor:
            cursor.execute(
                "CALL actualizar_Reporte(%s, %s, %s)",
                [pk, id_prioridad, id_estado]
            )
            row = cursor.fetchone()

        resultado = row[0] if row else 0
        if resultado == 1:
            return JsonResponse(
                {'ok': False, 'error': 'El SP no pudo actualizar el reporte.'},
                status=500,
            )

        return JsonResponse({
            'ok': True,
            'mensaje': 'Reporte actualizado correctamente.',
            'estado_movido_historial': (id_estado == 4),
        })

    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

#View de actualizar usuario
@group_required("Encargado")
def actualizar_usuario(request):
    user = request.user
    user_id = user.id

    if request.method == 'POST':
        nombre    = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula    = request.POST.get('cedula', '').strip()
        correo    = request.POST.get('correo', '').strip()
        password  = request.POST.get('password', '').strip()

        # Si el campo password viene vacío, pasamos None al SP para no modificarla
        passw_para_sp = None
        if password:
            from django.contrib.auth.hashers import make_password
            passw_para_sp = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.callproc('actualizar_Usuario', [user_id, nombre, apellidos, cedula, correo, passw_para_sp])

            # Si se proporcionó nueva contraseña, se actualiza el objeto de usuario y la sesión activa
            if password:
                user.set_password(password)
                user.save()
                update_session_auth_hash(request, user)

            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('Actualizar-Usuario-E')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar los datos: {e}')

    try:
        usuario = verUsuarioEncargado.objects.get(id_usuario=user_id)
    except verUsuarioEncargado.DoesNotExist:
        usuario = None
        messages.error(request, "No se encontró el registro del usuario.")

    return render(request, 'configuracion_e.html', {'usuario': usuario})
