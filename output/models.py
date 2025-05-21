from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class Output(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    categoria = models.ManyToManyField('categoria.Categoria')
    chats = models.ForeignKey('chat.Chat', on_delete=models.CASCADE)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.usuario.nome} - {self.categoria.nome} - {self.data_criacao}"