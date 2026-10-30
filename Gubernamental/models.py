from django.db import models

class VerMunicipios(models.Model):
    id_municipio = models.IntegerField(primary_key=True)
    municipio = models.CharField(max_length=100)
    id_usuario = models.IntegerField(null=True, blank=True)
    nombre_completo = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'ver_Municipios_Administrador'

class verSectores(models.Model):
    id = models.IntegerField(primary_key=True)
    id_municipio = models.IntegerField()
    sector = models.CharField(null = False, max_length=100)
    coordenadas  = models.JSONField(null=False, blank=False) 
    class Meta:
        managed = False
        db_table = 'ver_Sectores'

class VerUsuarios(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(null = False, max_length=100)
    apellidos = models.CharField(null = False, max_length=100)
    correo = models.CharField(null = False, max_length=100)
    cedula = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'ver_Usuarios'

class VerReportes(models.Model):
    id = models.BigIntegerField(primary_key=True)
    id_usuario = models.BigIntegerField()
    usuario = models.CharField(max_length=255)
    id_incidente = models.BigIntegerField()
    incidente = models.CharField(max_length=255)
    id_municipio = models.BigIntegerField()
    municipio = models.CharField(max_length=255)
    id_sector = models.BigIntegerField()
    sector = models.CharField(max_length=255)
    id_prioridad = models.BigIntegerField()
    tp_prioridad = models.CharField(max_length=255)
    id_estado = models.BigIntegerField()
    estado = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField()
    ubicacion = models.JSONField(null=True, blank=True)
    evidencias = models.JSONField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = 'ver_Reportes'
        ordering = ['-fecha_hora']
        
class VerHistoricoIncidentes(models.Model):
    id = models.BigIntegerField(primary_key=True)
    cc_usuario = models.CharField(max_length=255)
    tipo_incidente = models.CharField(max_length=255)
    incidente = models.CharField(max_length=255)
    municipio = models.CharField(max_length=255)
    sector = models.CharField(max_length=255)
    prioridad = models.CharField(max_length=255)
    estado = models.CharField(max_length=255)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField()
    ubicacion = models.JSONField(null=True, blank=True)
    evidencias = models.JSONField(null=True, blank=True)
        
    class Meta:
        managed = False
        db_table = 'ver_Historico_Incidentes'
        ordering = ['-fecha_hora']
