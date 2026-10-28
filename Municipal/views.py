import json, re, json
from io import BytesIO
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.db import connection
from django.contrib import messages
from django.contrib.auth.hashers import make_password
from django.contrib.auth import update_session_auth_hash
from .models import verUsuariosResponsabilidades, ver_Usuario_Municipio_Responsabilidad, verSectores, VerUsuarios, VerHistoricoIncidentes, VerMunicipios, VerReportes
from cundicents.decorators import group_required


def puntos_a_wkt(puntos):
    coords = [(p[1], p[0]) for p in puntos] 
    if coords[0] != coords[-1]:
        coords.append(coords[0])           
    anillo = ", ".join(f"{lng} {lat}" for lng, lat in coords)
    return f"POLYGON(({anillo}))"

@group_required("Municipal")
def inicio_municipalidad(request):
    return render(request, "inicio_m.html")


#Views de la gestion de sectores
@group_required("Municipal")
def gestion_sectores(request):
    id_user = request.user.id
    id_Municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=id_user).id_municipio
    sectores = verSectores.objects.filter(id_municipio=id_Municipio)
    return render(request, "sectores_m.html", {"sectores": sectores})

@group_required("Municipal")
def crear_sector(request):
    if request.method == 'POST':
        nombre = (request.POST.get('nombre') or '').strip()
        puntos_raw = request.POST.get('puntos') or '[]'

        if not nombre:
            messages.error(request, 'El nombre del sector es obligatorio.')
            return redirect('Crear-Sector')

        try:
            puntos = json.loads(puntos_raw)
        except json.JSONDecodeError:
            messages.error(request, 'Los puntos del sector no son válidos.')
            return redirect('Crear-Sector')

        if not isinstance(puntos, list) or len(puntos) < 4:
            messages.error(request, 'Debes dibujar al menos 4 puntos y cerrar el sector.')
            return redirect('Crear-Sector')

        # Convertir a WKT para MySQL
        try:
            wkt = puntos_a_wkt(puntos)
        except ValueError as e:
            return redirect('Crear-Sector')

        # Obtener municipio del usuario
        
        id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=request.user.id).id_municipio
        
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL agregar_Sector(%s, %s, %s, @p_mensaje)",
                    [id_municipio, nombre, wkt]
                )
                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''
        except Exception as e:
            messages.error(request, f'Error al guardar el sector: {e}')
            return redirect('Crear-Sector')
        if mensaje_sp != "Sector registrado correctamente.": 
            messages.success(request, f'Error: "{mensaje_sp}".')
            return redirect('Sectores')
        else:
            messages.success(request, f'Sector "{nombre}" guardado correctamente.')
            return redirect('Sectores')

    return render(request, "crear_sector.html")

@group_required("Municipal")
def ver_sector(request, sector_id):
    sector = get_object_or_404(verSectores, id=sector_id)
    return render(request, 'ver_sector_m.html', {'sector': sector})

@group_required("Municipal")
def eliminar_sector(request, sector_id):
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "CALL eliminar_Sector(%s, @p_mensaje)",
                [sector_id]
            )
            cursor.execute("SELECT @p_mensaje")
            fila = cursor.fetchone()
            mensaje_sp = fila[0] if fila else ''
    except Exception as e:
        messages.error(request, f'Error al eliminar el sector: {e}')
        return redirect('Sectores')
    if mensaje_sp != "Sector eliminado correctamente.": 
        messages.success(request, f'Error: "{mensaje_sp}".')
        return redirect('Sectores')
    else:
        messages.success(request, f'{mensaje_sp}')
        return redirect('Sectores')


#Views de la gestion de encargados
@group_required("Municipal")
def gestion_encargados(request):
    id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(id_usuario=request.user.id).id_municipio
    encargados_SyC = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=1)    
    encargados_Ac = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=2)
    encargados_GdR = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=3)
    encargados_I = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=4)
    encargados_SePu = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=5)
    encargados_Am = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=6)
    encargados_SaPu = verUsuariosResponsabilidades.objects.filter(id_municipio=id_municipio, id_tp_incidente=7)
    context = {
        'id_municipio':   id_municipio,
        'encargados_SyC':  encargados_SyC,
        'encargados_Ac':   encargados_Ac,
        'encargados_GdR':  encargados_GdR,
        'encargados_I':    encargados_I,
        'encargados_SePu': encargados_SePu,
        'encargados_Am':   encargados_Am,
        'encargados_SaPu': encargados_SaPu,
    }
    return render(request, 'encargados_m.html', context)

@group_required("Municipal")
def agregar_encargado(request):
    if request.method == 'POST':
        # Obtener municipio del usuario logueado
        try:
            id_municipio = ver_Usuario_Municipio_Responsabilidad.objects.get(
                id_usuario=request.user.id
            ).id_municipio
        except ver_Usuario_Municipio_Responsabilidad.DoesNotExist:
            messages.error(request, 'No se encontró un municipio asignado para tu usuario.')
            return render(request, "agregar_encargado_m.html")

        nombre        = request.POST.get('nombre', '').strip()
        apellidos     = request.POST.get('apellidos', '').strip()
        cedula        = request.POST.get('cedula', '').strip()
        correo        = request.POST.get('correo', '').strip()
        password      = request.POST.get('password', '').strip()
        tipoIncidente = request.POST.get('tipoIncidente', '').strip()

        # Validación mínima del lado servidor
        if not all([nombre, apellidos, cedula, correo, password, tipoIncidente]):
            messages.error(request, 'Todos los campos son obligatorios.')
            return render(request, "agregar_encargado_m.html")

        passhash = make_password(password)

        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "CALL registrar_Encargado(%s, %s, %s, %s, %s, %s, %s, @p_mensaje)",
                    [nombre, apellidos, correo, passhash, cedula,
                     int(id_municipio), tipoIncidente]
                )

                cursor.execute("SELECT @p_mensaje")
                fila = cursor.fetchone()
                mensaje_sp = fila[0] if fila else ''

                if mensaje_sp != "Usuario registrado correctamente":
                    messages.error(request, mensaje_sp or "No se recibió respuesta del servidor.")
                    return render(request, "agregar_encargado_m.html")

                messages.success(request, 'Encargado agregado exitosamente.')
                return redirect('Encargados')

        except Exception as e:
            messages.error(request, f'Error al registrar al encargado: {e}')
            # ✅ CORREGIDO: redirect() sin request
            return redirect('Encargados')

    return render(request, "agregar_encargado_m.html")

@group_required("Municipal")
def eliminar_encargado(request, id_usuario):
    try:
        with connection.cursor() as cursor:
            cursor.callproc('eliminar_Encargado', [id_usuario])
            resultado = cursor.fetchone()

            if resultado and resultado[0] == 1:
                return JsonResponse({'success': True})
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'No se pudo eliminar el encargado'
                })

    except Exception as e:
        return JsonResponse(
            {'success': False, 'error': str(e)},
            status=500
        )

@group_required("Municipal")
def actualizar_encargado(request, id_usuario):
    try:
        encargado = verUsuariosResponsabilidades.objects.get(id_usuario=id_usuario)
    except verUsuariosResponsabilidades.DoesNotExist:
        messages.error(request, 'El encargado no existe.')
        return redirect('Encargados')

    if request.method != 'POST':
        return render(request, 'actualizar_encargado_m.html', {
            'encargado': encargado
        })

    nombre    = request.POST.get('nombre', '').strip()
    apellidos = request.POST.get('apellidos', '').strip()
    cedula    = request.POST.get('cedula', '').strip()
    correo    = request.POST.get('correo', '').strip()
    password  = request.POST.get('password', '').strip()
    tipoInicidente = request.POST.get('tipoIncidente', '').strip()

    if VerUsuarios.objects.filter(cedula=cedula).exclude(id=id_usuario).exists():
        messages.error(request, 'La cédula ya está registrada por otro usuario.')
        return render(request, 'actualizar_encargado_m.html', {
            'encargado': encargado
        })

    if VerUsuarios.objects.filter(correo=correo).exclude(id=id_usuario).exists():
        messages.error(request, 'El correo ya está registrado por otro usuario.')
        return render(request, 'actualizar_encargado_m.html', {
            'encargado': encargado
        })

    try:
        if password == "": passw = None
        else: passw = make_password(password)
        
        with connection.cursor() as cursor:
            cursor.callproc('actualizar_Encargado', [id_usuario , nombre, apellidos, cedula, correo, passw, tipoInicidente])
        messages.success(request, 'Encargado actualizado correctamente.')
        return redirect('Encargados')

    except Exception as e:
        # ❌ Error → se queda en HTML2 con el mensaje
        messages.error(request, f'Ocurrió un error al actualizar el administrador: {e}')
        return render(request, 'actualizar_administrador_g.html', {
            'encargado': encargado
        })

# Views para la seccion de historial de incidentes
def _limpiar(valor):
    """Devuelve None cuando el filtro equivale a 'todos'."""
    if valor is None:
        return None
    valor = str(valor).strip()
    if valor == '' or valor.lower() == 'todos':
        return None
    return valor

def _a_decimal(valor):
    try:
        numero = float(valor)
    except (TypeError, ValueError):
        return None
    return numero

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

def _formatear_fecha(dt):
    if not dt:
        return ''
    try:
        if timezone.is_aware(dt):
            dt = timezone.localtime(dt)
    except Exception:
        pass
    return dt.strftime('%d/%m/%Y %H:%M')

def _municipio_del_usuario(request):
    try:
        relacion = (
            ver_Usuario_Municipio_Responsabilidad.objects
            .filter(id_usuario=request.user.id)
            .first()
        )
        if not relacion:
            return None

        return VerMunicipios.objects.filter(id_municipio=relacion.id_municipio).first()
    except Exception:
        return None

def _queryset_filtrado_m(request):
    """Igual que _queryset_filtrado pero forzando el municipio del usuario."""
    municipio_obj = _municipio_del_usuario(request)
    if municipio_obj is None:
        # Sin municipio asignado → no verá nada
        return VerHistoricoIncidentes.objects.none()

    qs = VerHistoricoIncidentes.objects.filter(municipio=municipio_obj.municipio)

    sector = _limpiar(request.GET.get('sector'))
    tipo = _limpiar(request.GET.get('tipo_incidente'))
    incidente = _limpiar(request.GET.get('incidente'))

    if sector:    qs = qs.filter(sector=sector)
    if tipo:      qs = qs.filter(tipo_incidente=tipo)
    if incidente: qs = qs.filter(incidente=incidente)

    return qs.order_by('-fecha_hora')

@group_required("Municipal")
def reportes(request):
    """Página de reportes filtrada por el municipio del usuario."""
    return render(request, 'historial_reportes_m.html')

@group_required("Municipal")
def api_filtros(request):
    """Filtros limitados al municipio del usuario."""
    try:
        municipio_obj = _municipio_del_usuario(request)
        if municipio_obj is None:
            return JsonResponse({
                'ok': True, 'municipio': '',
                'sectores': [], 'tipos': [], 'incidentes': [],
            })

        base = VerHistoricoIncidentes.objects.filter(municipio=municipio_obj.municipio)

        def distintos(campo):
            valores = (
                base.exclude(**{campo + '__isnull': True})
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
            'municipio': municipio_obj.municipio,
            'sectores': distintos('sector'),
            'tipos': distintos('tipo_incidente'),
            'incidentes': distintos('incidente'),
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Municipal")
def api_incidentes(request):
    """Listado de incidentes solo del municipio del usuario."""
    try:
        registros = _queryset_filtrado_m(request)
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

@group_required("Municipal")
def api_incidente_detalle(request, pk):
    """Detalle solo si el incidente pertenece al municipio del usuario."""
    try:
        municipio_obj = _municipio_del_usuario(request)
        if municipio_obj is None:
            return JsonResponse(
                {'ok': False, 'error': 'El usuario no tiene un municipio asignado.'},
                status=403,
            )

        registro = (
            VerHistoricoIncidentes.objects
            .filter(pk=pk, municipio=municipio_obj.municipio)
            .first()
        )
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'El incidente no existe o no pertenece a su municipio.'},
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

@group_required("Municipal")
def api_reporte_pdf(request):
    """PDF filtrado por el municipio del usuario."""
    from reportlab.lib import colors as rl_colors
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import cm
    from reportlab.platypus import (Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle)

    try:
        registros = list(_queryset_filtrado_m(request))
    except Exception as exc:  # noqa: BLE001
        return HttpResponse(
            f'No se pudo consultar la base de datos: {exc}',
            status=500, content_type='text/plain; charset=utf-8',
        )

    municipio_obj = _municipio_del_usuario(request)
    municipio_nombre = municipio_obj.municipio if municipio_obj else '(sin municipio asignado)'

    etiquetas = (
        ('Sector', _limpiar(request.GET.get('sector'))),
        ('Tipo de incidente', _limpiar(request.GET.get('tipo_incidente'))),
        ('Incidente', _limpiar(request.GET.get('incidente'))),
    )
    partes = [f'{etq}: {val}' for etq, val in etiquetas if val]
    texto_filtros = ' · '.join(partes) if partes else 'Sin filtros adicionales'

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
        Paragraph(f'Reporte de incidentes registrados {municipio_nombre}', e_titulo),
        Paragraph(f'Generado el {timezone.localtime().strftime("%d/%m/%Y %H:%M")}', e_sub),
        Paragraph(f'Filtros aplicados: {texto_filtros}', e_sub),
        Paragraph(f'Total de registros: {len(registros)}', e_sub),
        Spacer(1, 0.45 * cm),
               
    ]

    if registros:
        cabecera = ['ID', 'Fecha y hora', 'Sector',
                    'Tipo', 'Incidente', 'Prioridad', 'Estado']
        datos = [[Paragraph(c, e_cab) for c in cabecera]]
        for r in registros:
            datos.append([
                Paragraph(str(r.id), e_celda),
                Paragraph(_formatear_fecha(r.fecha_hora), e_celda),
                Paragraph(r.sector or '—', e_celda),
                Paragraph(r.tipo_incidente or '—', e_celda),
                Paragraph(r.incidente or '—', e_celda),
                Paragraph(r.prioridad or '—', e_celda),
                Paragraph(r.estado or '—', e_celda),
            ])
        anchos = [1.8*cm, 3.2*cm, 3.0*cm, 2.6*cm, 3.4*cm, 6.8*cm, 2.6*cm, 2.8*cm]
        tabla = Table(datos, colWidths=anchos, repeatRows=1)
        tabla.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), rl_colors.HexColor('#d71920')),
            ('TEXTCOLOR', (0, 0), (-1, 0), rl_colors.white),
            ('GRID', (0, 0), (-1, -1), 0.4, rl_colors.HexColor('#e3d6b6')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [rl_colors.white, rl_colors.HexColor('#faf3e0')]),
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        story.append(tabla)
    else:
        story.append(Paragraph('No se encontraron registros con los filtros seleccionados.', e_sub))

    def _pie(canvas, documento):
        canvas.saveState()
        canvas.setFont('Helvetica', 7)
        canvas.setFillColor(rl_colors.HexColor('#7a6a4a'))
        canvas.drawString(1.2 * cm, 0.7 * cm, 'Sistema de Incidentes · Reporte generado automáticamente')
        canvas.drawRightString(pagina[0] - 1.2 * cm, 0.7 * cm, f'Página {documento.page}')
        canvas.restoreState()

    doc.build(story, onFirstPage=_pie, onLaterPages=_pie)
    pdf = buffer.getvalue()
    buffer.close()

    nombre = f"reporte_incidentes_{timezone.localtime().strftime('%Y%m%d_%H%M')}.pdf"
    respuesta = HttpResponse(pdf, content_type='application/pdf')
    respuesta['Content-Disposition'] = f'attachment; filename="{nombre}"'
    return respuesta


#Views de incidentes activos
def _queryset_filtrado_a(request):
    """Igual que _queryset_filtrado pero forzando el municipio del usuario."""
    municipio_obj = _municipio_del_usuario(request)
    if municipio_obj is None:
        # Sin municipio asignado → no verá nada
        return VerReportes.objects.none()

    qs = VerReportes.objects.filter(id_municipio=municipio_obj.id_municipio)

    sector = _limpiar(request.GET.get('sector'))
    prioridad = _limpiar(request.GET.get('prioridad'))
    incidente = _limpiar(request.GET.get('incidente'))

    if sector:    qs = qs.filter(sector=sector)
    if prioridad: qs = qs.filter(tp_prioridad=prioridad)
    if incidente: qs = qs.filter(incidente=incidente)

    return qs.order_by('-fecha_hora')

def _municipio_del_usuario(request):
    try:
        relacion = (
            ver_Usuario_Municipio_Responsabilidad.objects
            .filter(id_usuario=request.user.id)
            .first()
        )
        if not relacion:
            return None

        return VerMunicipios.objects.filter(id_municipio=relacion.id_municipio).first()
    except Exception:
        return None

@group_required("Municipal")
def reportes_a(request):
    """Página de reportes filtrada por el municipio del usuario."""
    return render(request, 'lista_reportes_m.html')

@group_required("Municipal")
def api_filtros_a(request):
    """Filtros limitados al municipio del usuario."""
    try:
        municipio_obj = _municipio_del_usuario(request)
        if municipio_obj is None:
            return JsonResponse({
                'ok': True, 'municipio': '',
                'sectores': [], 'prioridades': [], 'incidentes': [],
            })

        base = VerReportes.objects.filter(id_municipio=municipio_obj.id_municipio)

        def distintos(campo):
            valores = (
                base.exclude(**{campo + '__isnull': True})
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
            'municipio': municipio_obj.municipio,
            'sectores': distintos('sector'),
            'prioridades': distintos('tp_prioridad'),
            'incidentes': distintos('incidente'),
        })
    except Exception as exc:  # noqa: BLE001
        return JsonResponse({'ok': False, 'error': str(exc)}, status=500)

@group_required("Municipal")
def api_incidentes_a(request):
    """Listado de incidentes solo del municipio del usuario."""
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

@group_required("Municipal")
def api_incidente_detalle_a(request, pk):
    """Detalle solo si el incidente pertenece al municipio del usuario."""
    try:
        municipio_obj = _municipio_del_usuario(request)
        if municipio_obj is None:
            return JsonResponse(
                {'ok': False, 'error': 'El usuario no tiene un municipio asignado.'},
                status=403,
            )

        registro = (
            VerReportes.objects
            .filter(pk=pk, id_municipio=municipio_obj.id_municipio)
            .first()
        )
        if registro is None:
            return JsonResponse(
                {'ok': False, 'error': 'El incidente no existe o no pertenece a su municipio.'},
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
                'prioridad': registro.tp_prioridad or '',
                'incidente': registro.incidente or '',
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

#View de configuracion
@group_required("Municipal")
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
            return redirect('Actualizar-Usuario-M')

        except Exception as e:
            messages.error(request, f'Ocurrió un error al actualizar los datos: {e}')
            usuario = VerUsuarios.objects.get(id=id)
            return render(request, 'configuracion_m.html', {'usuario': usuario})

    usuario = VerUsuarios.objects.get(id=id)
    context = {'usuario': usuario, }
    return render(request, 'configuracion_m.html', context)