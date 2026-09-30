from django.db import models

class ver_Usuario_Municipio_Responsabilidad(models.Model):
    id = models.IntegerField(primary_key=True)
    id_usuario = models.IntegerField(null=False)
    id_municipio = models.IntegerField(null=False)
    id_tp_incidente = models.IntegerField(null=True)
    class Meta:
        managed = False
        db_table = 'ver_Usuario_Municipio_Responsabilidad'

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

class verUsuariosResponsabilidades(models.Model):
    id_usuario    = models.IntegerField(primary_key=True)
    nombre        = models.CharField(max_length=150)
    apellido      = models.CharField(max_length=150)
    correo        = models.EmailField()
    cedula        = models.IntegerField()
    id_municipio  = models.IntegerField()
    id_tp_incidente = models.IntegerField()   # ← antes id_tp_municipio
    tp_incidente  = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'ver_Usuarios_Responsabilidades'