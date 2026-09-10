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

class Item(models.Model):
    STATUS_CHOICES = [
        ('perdido', 'Perdido (Alguém está procurando)'),
        ('achado', 'Achado (Alguém encontrou e guardou)'),
        ('devolvido', 'Devolvido (Entregue ao dono)'),
    ]

    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    local = models.CharField(max_length=255, help_text="Onde foi encontrado ou onde acha que perdeu")
    data_registro = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='achado')
    
    imagem = models.ImageField(upload_to='itens_imagens/', blank=True, null=True) 
    
    registrado_por = models.ForeignKey(User, on_delete=models.CASCADE, related_name='itens_registrados')

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
  
