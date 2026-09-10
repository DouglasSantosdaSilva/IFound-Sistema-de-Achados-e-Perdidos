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

from django.db import models
from django.contrib.auth.models import User

class Item(models.Model):
    STATUS_CHOICES = [
        ('achei', 'Achei'),
        ('perdi', 'Perdi'),
    ]

    nome = models.CharField(max_length=100)
    descricao = models.TextField()
    local = models.CharField(max_length=100)
    data_registro = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='achei')
    imagem = models.ImageField(upload_to='itens/', null=True, blank=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itens')
    criado_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"

class Solicitacao(models.Model):
    STATUS_CHOICES = [
        ('pendente', 'Pendente'),
        ('aprovado', 'Aprovado'),
        ('recusado', 'Recusado'),
    ]

    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='solicitacoes')
    solicitante = models.ForeignKey(User, on_delete=models.CASCADE, related_name='minhas_solicitacoes')
    foto_comprovante = models.ImageField(upload_to='comprovantes/')
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pendente')

    def __str__(self):
        return f"Solicitação de {self.solicitante.username} para {self.item.nome}"

    def __str__(self):
        return f"{self.nome} ({self.get_status_display()})"
  
