import re, json
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.shortcuts import render
from django.shortcuts import render, redirect
from .models import VerMunicipios, VerUsuarios, VerHistoricoIncidentes, VerReportes
from django.db import connection
from django.http import JsonResponse
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.hashers import make_password
from cundicents.decorators import group_required
from django.contrib import messages
from django.views.decorators.http import require_POST


@group_required("Gubernamental")
def inicio_gubernamental(request):
    #granjas = VerGranjas.objects.all()
    #context = {"granjas": granjas,}
    return render(request, "inicio_g.html")


# Views de la seccion de municipios
@group_required("Gubernamental")
def gestion_municipios(request):
    municipios = VerMunicipios.objects.all()
    return render(request, 'municipios_g.html', {'municipios': municipios})

@group_required("Gubernamental")
def agregar_municipio(request):
    nombre = request.POST.get('nombre', '').strip()
    try:
        with connection.cursor() as cursor:
            cursor.callproc('agregar_Municipio', [nombre])
        return JsonResponse({'ok': True, 'tipo': 'municipio_creado', 'mensaje': 'Municipio agregado correctamente.'})
    except Exception as e:
        return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': 'Ocurrió un error al crear el municipio.', 'error': str(e)}, status=500)

@group_required("Gubernamental")
def eliminar_municipio(request):
    if request.method == 'POST':
        id_municipio = request.POST.get('id_municipio', '').strip()
        try:
            with connection.cursor() as cursor:
                cursor.execute( "CALL eliminar_Municipio(%s, @p_mensaje);", [id_municipio])
                cursor.execute("SELECT @p_mensaje;")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else None

            if mensaje_sp == 'Municipio eliminado correctamente':
                return JsonResponse({'ok': True, 'tipo': 'municipio_eliminado', 'mensaje': 'Municipio eliminado correctamente.'})
            else:
                return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': mensaje_sp or 'Error al eliminar el municipio.', 'error': mensaje_sp or 'Error al eliminar el municipio' }, status=400)

        except Exception as e:
            return JsonResponse({'ok': False, 'tipo': 'municipio_error', 'mensaje': 'Ocurrió un error al eliminar el municipio.', 'error': f'Error: {str(e)}'}, status=500)

# Views de gestion de administradores
@group_required("Gubernamental")
def agregar_administrador(request):
    id = request.GET.get('id_municipio', '').strip()
    if not id:
        return redirect('Municipios')
    contexto = {'id_municipio': id}
    return render(request, 'agregar_administrador_g.html', contexto)

@group_required("Gubernamental")
def registrar_administrador(request):
    id_municipio = request.GET.get('id_municipio', '').strip()
    if request.method == 'POST':
        id_municipio = request.POST.get('id_municipio', id_municipio).strip()

    if not id_municipio:
        return redirect('Municipios')

    contexto = {'id_municipio': id_municipio}

    if request.method == 'POST':
        nombre = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula = request.POST.get('cedula', '').strip()
        correo = request.POST.get('correo', '').strip().lower()
        password = request.POST.get('password', '')
        password_hash = make_password(password)

        mensaje_sp = ''
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL registrar_Administrador_Municipio(%s, %s, %s, %s, %s, %s, @p_mensaje)",
                    [nombre, apellidos, correo, password_hash, cedula, int(id_municipio)]
                )
                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''

        except Exception as e:
            contexto['tipo'] = 'administrador_error'
            contexto['mensaje_ui'] = f'⚠️ Error al registrar: {e}'
            messages.error(request, f'⚠️ Error al registrar: {e}')
            return render(request, 'agregar_administrador_g.html', contexto)

        if mensaje_sp != "Usuario registrado correctamente":
            contexto['tipo'] = 'administrador_error'
            contexto['mensaje_ui'] = f'⚠️ {mensaje_sp or "No se recibió respuesta del servidor."}'
            messages.error(request, f'⚠️ {mensaje_sp or "No se recibió respuesta del servidor."}')
            return render(request, 'agregar_administrador_g.html', contexto)
        else:
            messages.success(request, '✅ Administrador agregado exitosamente.')
            return redirect('Municipios')

    return render(request, 'agregar_administrador_g.html', contexto)

@group_required("Gubernamental")
@require_POST
def eliminar_administrador(request):
    id_usuario = request.POST.get('id_usuario')
    try:
        with connection.cursor() as cursor:
            cursor.callproc('eliminar_Administrador', [id_usuario])
        return JsonResponse({
            'ok': True, 'tipo': 'administrador_eliminado', 'mensaje': 'Administrador eliminado correctamente.'})
    except Exception as e:
        return JsonResponse({'ok': False, 'tipo': 'administrador_error', 'mensaje': 'Ocurrió un error al eliminar el administrador.', 'error': str(e)}, status=500)

@group_required("Gubernamental")
def actualizar_administrador(request, id):
    # ===== Obtener el administrador =====
    try:
        administrador = VerUsuarios.objects.get(id=id)
    except VerUsuarios.DoesNotExist:
        messages.error(request, 'El administrador no existe.')
        return redirect('Municipios')

    # ===== GET: mostrar formulario con datos actuales =====
    if request.method != 'POST':
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    nombre    = request.POST.get('nombre', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    cedula    = request.POST.get('cedula', '').strip()
    correo    = request.POST.get('correo', '').strip()
    password  = request.POST.get('password', '').strip()


    # ----- Validar cédula duplicada (otro usuario) -----
    if VerUsuarios.objects.filter(cedula=cedula).exclude(id=id).exists():
        messages.error(request, 'La cédula ya está registrada por otro usuario.')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    # ----- Validar correo duplicado (otro usuario) -----
    if VerUsuarios.objects.filter(correo=correo).exclude(id=id).exists():
        messages.error(request, 'El correo ya está registrado por otro usuario.')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

    try:
        if password == "": passw = None
        else: passw = make_password(password)
        
        with connection.cursor() as cursor:
            cursor.callproc('actualizar_Usuario', [id , nombre, apellidos, cedula, correo, passw])
        messages.success(request, 'Administrador actualizado correctamente.')
        return redirect('Municipios')

    except Exception as e:
        # ❌ Error → se queda en HTML2 con el mensaje
        messages.error(request, f'Ocurrió un error al actualizar el administrador: {e}')
        return render(request, 'actualizar_administrador_g.html', {
            'administrador': administrador
        })

# Views para la seccion de configuracion
@group_required("Gubernamental")
def actualizar_usuario(request):
    user = request.user
    id = user.id

    if request.method == 'POST':
        nombre    = request.POST.get('nombre', '').strip()
        apellidos = request.POST.get('apellidos', '').strip()
        cedula    = request.POST.get('cedula', '').strip()
        correo    = request.POST.get('correo', '').strip()
        password  = (request.POST.get('password') or '').strip()

        if password == "": passw = None
        else: passw = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.callproc('actualizar_Usuario', [id, nombre, apellidos, cedula, correo, passw])

            if passw != None:
                user.password = passw
                update_session_auth_hash(request, user)

            messages.success(request, 'Datos actualizados correctamente.')
            return redirect('Actualizar-Usuario')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar el administrador: {e}')
            usuario = VerUsuarios.objects.get(id=id)
            return render(request, 'configuracion_g.html', {'usuario': usuario})

    usuario = VerUsuarios.objects.get(id=id)
    context = {'usuario': usuario, }
    return render(request, 'configuracion_g.html', context)

# Views para la seccion de historial de incidentes
def _limpiar(valor):
    """Devuelve None cuando el filtro equivale a 'todos'."""
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == '' or valor.lower() == 'todos':
        return None
    return valor

def _a_estructura(valor):
    """Normaliza un JSONField (dict, list o string JSON) a estructura Python."""
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

def _a_decimal(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero

def _formatear_fecha(dt):
    if not dt:
        return ''
    try:
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
    except Exception:
        pass
    return dt.strftime('%d/%m/%Y %H:%M')

def _queryset_filtrado(request):
    qs = VerHistoricoIncidentes.objects.all()

    municipio = _limpiar(request.GET.get('municipio'))
    sector = _limpiar(request.GET.get('sector'))
    tipo = _limpiar(request.GET.get('tipo_incidente'))
    incidente = _limpiar(request.GET.get('incidente'))

    if municipio:
        qs = qs.filter(municipio=municipio)
    if sector:
        qs = qs.filter(sector=sector)
    if tipo:
        qs = qs.filter(tipo_incidente=tipo)
    if incidente:
        qs = qs.filter(incidente=incidente)

    return qs.order_by('-fecha_hora')

def _extraer_evidencias(evidencias):
    """
    Devuelve la lista de URLs de evidencias a partir del JSON.

    Estructura esperada:
        {"1_incidente_1": "url", "1_incidente_2": "url",
         "1_incidente_3": "url", "1_incidente_4": "url"}

    - El prefijo "1" es el ID del registro; el sufijo "_1.._4" es el
      número de evidencia (máximo 4).
    - Se ordenan por el sufijo numérico para que la galería respete
      el orden 1 → 4.
    """
    datos = _a_estructura(evidencias)
    if datos is None:
        return []

    try:
        from django.conf import settings
        media_url = getattr(settings, 'MEDIA_URL', '') or '/media/'
    except Exception:
        media_url = '/media/'
    if not media_url.startswith(('http://', 'https://', '/')):
        media_url = '/' + media_url
    if not media_url.endswith('/'):
        media_url += '/'

    def _normalizar(valor):
        """Convierte el valor a una URL utilizable, o None si no aplica."""
        if not isinstance(valor, str):
            return None
        texto = valor.strip()
        if not texto:
            return None
        # URL absoluta
        if texto.startswith(('http://', 'https://', '//')):
            return texto
        # Ruta absoluta dentro del sitio
        if texto.startswith('/'):
            return texto
        # Ruta relativa que ya incluye media/ o static/
        if texto.startswith(('media/', 'static/')):
            return '/' + texto
        # Ruta relativa genérica → se asume dentro de MEDIA
        return media_url + texto.lstrip('/')

    def _orden_sufijo(clave):
        """Extrae el número final de la clave: '1_incidente_3' → 3."""
        coincidencia = re.search(r'(\d+)\s*$', str(clave))
        return int(coincidencia.group(1)) if coincidencia else 10 ** 9

    encontradas = []

    if isinstance(datos, dict):
        # Ordenar por el sufijo numérico (_1, _2, _3, _4)
        claves = sorted(
            datos.keys(),
            key=lambda k: (_orden_sufijo(k), str(k)),
        )
        for clave in claves:
            url = _normalizar(datos.get(clave))
            if url:
                encontradas.append(url)
            if len(encontradas) >= 4:   # máximo 4 evidencias
                break

    elif isinstance(datos, (list, tuple)):
        for valor in datos:
            url = _normalizar(valor)
            if url:
                encontradas.append(url)
            if len(encontradas) >= 4:
                break

    # Sin duplicados, conservando el orden
    vistas = set()
    salida = []
    for url in encontradas:
        if url not in vistas:
            vistas.add(url)
            salida.append(url)
    return salida

def _extraer_coordenadas(ubicacion):
    """Devuelve (lat, lng) a partir del JSON de ubicación, o None."""
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

        # GeoJSON: {"type": "Point", "coordinates": [lng, lat]}
        if (lat is None or lng is None) and isinstance(claves.get('coordinates'), (list, tuple)):
            coords = claves['coordinates']
            if len(coords) >= 2:
                lng = _a_decimal(coords[0])
                lat = _a_decimal(coords[1])

        # Estructuras anidadas: {"ubicacion": {...}}
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

@group_required("Gubernamental")
def reportes(request):
    """Renderiza la página de reportes (mantiene el HTML/estilos actuales)."""
    return render(request, 'historial_reportes_g.html')

@group_required("Gubernamental")
def api_filtros(request):
    """Valores distintos existentes en la tabla para poblar los selects."""
    try:
        def distintos(campo):
            valores = (
                VerHistoricoIncidentes.objects
                .exclude(**{campo + '__isnull': True})
                .exclude(**{campo: ''})
                .values_list(campo, flat=True)
                .order_by(campo)
                .distinct()
            )
            limpios = set()
            for v in valores:
                if v is None:
                    continue
                v = str(v).strip()
                if v:
                    limpios.add(v)
            return sorted(limpios, key=lambda s: s.lower())

        return JsonResponse({
            'ok': True,
            'municipios': distintos('municipio'),
            'sectores': distintos('sector'),
            'tipos': distintos('tipo_incidente'),
            'incidentes': distintos('incidente'),
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Gubernamental")
def api_incidentes(request):
    """Listado de registros aplicando los filtros recibidos."""
    try:
        registros = _queryset_filtrado(request)
        data = [{
            'id': r.id,
            'municipio': r.municipio or '',
            'sector': r.sector or '',
            'tipo_incidente': r.tipo_incidente or '',
            'incidente': r.incidente or '',
            'estado': r.estado or '',
            'fecha_hora': r.fecha_hora.isoformat() if r.fecha_hora else None,
        } for r in registros]

        return JsonResponse({'ok': True, 'total': len(data), 'registros': data})
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Gubernamental")
def api_incidente_detalle(request, pk):
    """Detalle completo de un incidente, con ubicación y evidencias normalizadas."""
    try:
        registro = VerHistoricoIncidentes.objects.filter(pk=pk).first()
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'El incidente solicitado no existe.'},
                status=404,
            )

        coordenadas = _extraer_coordenadas(registro.ubicacion)

        return JsonResponse({
            'ok': True,
            'registro': {
                'id': registro.id,
                'cc_usuario': registro.cc_usuario or '',
                'municipio': registro.municipio or '',
                'sector': registro.sector or '',
                'tipo_incidente': registro.tipo_incidente or '',
                'incidente': registro.incidente or '',
                'prioridad': registro.prioridad or '',
                'estado': registro.estado or '',
                'descripcion': registro.descripcion or '',
                'fecha_hora': registro.fecha_hora.isoformat() if registro.fecha_hora else None,
                'lat': coordenadas[0] if coordenadas else None,
                'lng': coordenadas[1] if coordenadas else None,
                'evidencias': _extraer_evidencias(registro.evidencias),
            },
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Gubernamental")
def api_reporte_pdf(request):
    
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)
    

    try:
        registros = list(_queryset_filtrado(request))
    except Exception as exc:  # noqa: BLE001
        return HttpResponse(
            f'No se pudo consultar la base de datos: {exc}',
            status=500, content_type='text/plain; charset=utf-8',
        )

    # Filtros aplicados (texto legible)
    etiquetas = (
        ('Municipio', _limpiar(request.GET.get('municipio'))),
        ('Sector', _limpiar(request.GET.get('sector'))),
        ('Tipo de incidente', _limpiar(request.GET.get('tipo_incidente'))),
        ('Incidente', _limpiar(request.GET.get('incidente'))),
    )
    partes = [f'{etq}: {val}' for etq, val in etiquetas if val]
    texto_filtros = ' · '.join(partes) if partes else 'Sin filtros (todos los registros)'

    buffer = BytesIO()
    pagina = landscape(A4)

    doc = SimpleDocTemplate(
        buffer, pagesize=pagina,
        leftMargin=1.2 * cm, rightMargin=1.2 * cm,
        topMargin=1.2 * cm, bottomMargin=1.4 * cm,
        title='Reporte de incidentes',
    )

    estilos = getSampleStyleSheet()
    e_titulo = ParagraphStyle('tit', parent=estilos['Title'], fontSize=15, leading=18,
                              textColor=rl_colors.HexColor('#2c2416'), spaceAfter=4)
    e_sub = ParagraphStyle('sub', parent=estilos['Normal'], fontSize=8.5, leading=11,
                           textColor=rl_colors.HexColor('#5e4b2b'))
    e_celda = ParagraphStyle('celda', parent=estilos['Normal'], fontSize=7.2, leading=9)
    e_cab = ParagraphStyle('cab', parent=e_celda, fontName='Helvetica-Bold',
                           textColor=rl_colors.white)

    story = [
        Paragraph('Reporte de incidentes registrados', e_titulo),
        Paragraph(f'Generado el {timezone.localtime().strftime("%d/%m/%Y %H:%M")}', e_sub),
        Paragraph(f'Filtros aplicados: {texto_filtros}', e_sub),
        Paragraph(f'Total de registros: {len(registros)}', e_sub),
        Spacer(1, 0.45 * cm),
    ]

    if registros:
        cabecera = ['ID', 'Fecha y hora', 'Municipio', 'Sector',
                    'Tipo', 'Incidente', 'Prioridad', 'Estado']
        datos = [[Paragraph(c, e_cab) for c in cabecera]]

        for r in registros:
            datos.append([
                Paragraph(str(r.id), e_celda),
                Paragraph(_formatear_fecha(r.fecha_hora), e_celda),
                Paragraph(r.municipio or '—', e_celda),
                Paragraph(r.sector or '—', e_celda),
                Paragraph(r.tipo_incidente or '—', e_celda),
                Paragraph(r.incidente or '—', e_celda),
                Paragraph(r.prioridad or '—', e_celda),
                Paragraph(r.estado or '—', e_celda),
            ])

        anchos = [1.8 * cm, 3.2 * cm, 3.0 * cm, 2.6 * cm,
                  3.4 * cm, 6.8 * cm, 2.6 * cm, 2.8 * cm]

        tabla = Table(datos, colWidths=anchos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#d71920')),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
            ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#e3d6b6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1),
             [rl_colors.white, rl_colors.HexColor('#faf3e0')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tabla)
    else:
        story.append(Paragraph(
            'No se encontraron registros con los filtros seleccionados.', e_sub))

    def _pie(canvas, documento):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(rl_colors.HexColor('#7a6a4a'))
        canvas.drawString(1.2 * cm, 0.7 * cm,
                          'Sistema de Incidentes · Reporte generado automáticamente')
        canvas.drawRightString(pagina[0] - 1.2 * cm, 0.7 * cm,
                               f'Página {documento.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)

    pdf = buffer.getvalue()
    buffer.close()

    nombre = f"reporte_incidentes_{timezone.localtime().strftime('%Y%m%d_%H%M')}.pdf"
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta

#Views Lista Incidentes activos
def _queryset_filtrado_a(request):
    qs = VerReportes.objects.all()

    municipio = _limpiar(request.GET.get('municipio'))
    sector    = _limpiar(request.GET.get('sector'))
    prioridad = _limpiar(request.GET.get('prioridad'))
    incidente = _limpiar(request.GET.get('incidente'))

    if municipio:
        qs = qs.filter(municipio=municipio)
    if sector:
        qs = qs.filter(sector=sector)
    if prioridad:
        qs = qs.filter(tp_prioridad=prioridad)  
    if incidente:
        qs = qs.filter(incidente=incidente)

    return qs.order_by('-fecha_hora')

@group_required("Gubernamental")
def reportes_l(request):
    """Renderiza la página de reportes."""
    return render(request, 'lista_reportes_g.html')

@group_required("Gubernamental")
def api_filtros_l(request):
    """Valores distintos existentes en la tabla para poblar los selects."""
    try:
        def distintos(campo):
            valores = (
                VerReportes.objects
                .exclude(**{campo + '__isnull': True})
                .exclude(**{campo: ''})
                .values_list(campo, flat=True)
                .order_by(campo)
                .distinct()
            )
            limpios = set()
            for v in valores:
                if v is None:
                    continue
                v = str(v).strip()
                if v:
                    limpios.add(v)
            return sorted(limpios, key=lambda s: s.lower())

        return JsonResponse({
            'ok': True,
            'municipios': distintos('municipio'),
            'sectores': distintos('sector'),
            'prioridades': distintos('tp_prioridad'),
            'incidentes': distintos('incidente'),
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Gubernamental")
def api_incidentes_l(request):
    """Listado de registros aplicando los filtros recibidos."""
    try:
        registros = _queryset_filtrado_a(request)
        data = [{
            'id': r.id,
            'municipio': r.municipio or '',
            'sector': r.sector or '',
            'prioridad': r.tp_prioridad or '',
            'incidente': r.incidente or '',
            'estado': r.estado or '',
            'fecha_hora': r.fecha_hora.isoformat() if r.fecha_hora else None,
        } for r in registros]

        return JsonResponse({'ok': True, 'total': len(data), 'registros': data})
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Gubernamental")
def api_incidente_detalle_l(request, pk):
    """Detalle completo de un incidente, con ubicación y evidencias normalizadas."""
    try:
        registro = VerReportes.objects.filter(pk=pk).first()
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'El incidente solicitado no existe.'},
                status=404,
            )

        coordenadas = _extraer_coordenadas(registro.ubicacion)

        return JsonResponse({
            'ok': True,
            'registro': {
                'id': registro.id,
                'usuario': registro.usuario or '',
                'municipio': registro.municipio or '',
                'sector': registro.sector or '',
                'incidente': registro.incidente or '',
                'prioridad': registro.tp_prioridad or '',
                'estado': registro.estado or '',
                'descripcion': registro.descripcion or '',
                'fecha_hora': registro.fecha_hora.isoformat() if registro.fecha_hora else None,
                'lat': coordenadas[0] if coordenadas else None,
                'lng': coordenadas[1] if coordenadas else None,
                'evidencias': _extraer_evidencias(registro.evidencias),
            },
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)
