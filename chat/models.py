from django.db import models

class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey('usuario.Usuario', on_delete=models.CASCADE)
    categoria = models.ForeignKey('categoria.Categoria', on_delete=models.CASCADE)
    message = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user}: {self.message[:20]}..."