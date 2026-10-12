from django.db import models
from django.conf import settings

class AccountEmail(models.Model):
    """Reserva única de email dos novos cadastros; contas existentes são preservadas."""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='account_email')
    email = models.EmailField(unique=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f'Confirmação da conta {self.user_id}'
