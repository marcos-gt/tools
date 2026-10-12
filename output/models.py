from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Output(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ManyToManyField('categoria.Categoria')
    chats = models.ForeignKey('chat.Chat', on_delete=models.SET_NULL, null=True, blank=True)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    modalidade = models.CharField(max_length=20, default='')
    categoria_snapshot = models.JSONField(default=dict)
    mensagens_snapshot = models.JSONField(default=list)
    payload = models.JSONField(default=dict)
    modelo = models.CharField(max_length=255, default='')
    resposta_original = models.TextField(default='')
    status = models.CharField(max_length=20, default='legacy')
    codigo_erro = models.CharField(max_length=50, default='')
    duracao_ms = models.PositiveIntegerField(default=0)
    render_status = models.CharField(max_length=20, default='pending')

    def __str__(self):
        return f'{self.usuario_id} - {self.pk} - {self.status}'
