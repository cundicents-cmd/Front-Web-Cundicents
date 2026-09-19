from django.db import models

class VerMunicipios(models.Model):
    id_municipio = models.IntegerField(primary_key=True)
    municipio = models.CharField(max_length=100)
    id_usuario = models.IntegerField(null=True, blank=True)
    nombre_completo = models.CharField(max_length=200, null=True, blank=True)
    class Meta:
        managed = False
        db_table = 'ver_Municipios_Administrador'


class VerUsuarios(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(null = False, max_length=100)
    apellidos = models.CharField(null = False, max_length=100)
    correo = models.CharField(null = False, max_length=100)
    cedula = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'ver_Usuarios'