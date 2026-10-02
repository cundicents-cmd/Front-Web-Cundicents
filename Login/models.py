from django.db import models

class VerUsuarios(models.Model):
    id = models.IntegerField(primary_key=True)
    nombre = models.CharField(null = False, max_length=100)
    apellidos = models.CharField(null = False, max_length=100)
    correo = models.CharField(null = False, max_length=100)
    cedula = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'ver_Usuarios'
