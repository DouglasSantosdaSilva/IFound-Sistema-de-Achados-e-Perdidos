from django.db import models
from django.contrib.auth.models import User

class Perfil(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    nome_completo = models.CharField(max_length=255, blank=True, null=True)
    vinculo = models.CharField(max_length=50, default='Aluno(a)')
    curso = models.CharField(max_length=255, blank=True, null=True)
    turma = models.CharField(max_length=100, blank=True, null=True)
    foto_url = models.URLField(max_length=500, blank=True, null=True)

    def __str__(self):
        return f"Perfil de {self.user.username}"
