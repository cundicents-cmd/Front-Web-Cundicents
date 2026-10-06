from django.db import models

class verUsuarioEncargado(models.Model):
    id_usuario    = models.IntegerField(primary_key=True)
    nombre        = models.CharField(max_length=150)
    apellido      = models.CharField(max_length=150)
    correo        = models.EmailField()
    cedula        = models.IntegerField()
    municipio  = models.CharField(max_length=100)
    tp_incidente  = models.CharField(max_length=100)
    class Meta:
        managed = False
        db_table = 'ver_Usuarios_Encargado'
