from django.db import models

# Create your models here.
class Sugestao(models.Model):
    chat = models.ForeignKey('chat.Chat', on_delete=models.CASCADE)
    conteudo = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)