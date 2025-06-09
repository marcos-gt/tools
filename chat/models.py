from django.db import models
from django.contrib.auth.models import User

class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    categoria = models.ForeignKey('categoria.Categoria', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    visualizationType = models.CharField(max_length=50, default='text')

    def __str__(self):
        return f"{self.usuario}: {self.message[:20]}..."