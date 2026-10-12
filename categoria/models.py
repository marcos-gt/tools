from django.db import models
from django.conf import settings

# Create your models here.
class Categoria(models.Model):
    id = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, editable=False)
    nome = models.CharField(max_length=255)
    descricao = models.TextField()
    data_criacao = models.DateTimeField(auto_now_add=True)
    ativa = models.BooleanField(default=True)

    def __str__(self):
        return self.nome
    class Meta:
        constraints = [models.UniqueConstraint(fields=["usuario", "nome"], name="categoria_usuario_nome_unique")]
