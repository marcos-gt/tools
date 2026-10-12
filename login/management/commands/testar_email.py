from smtplib import SMTPException
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.core.validators import validate_email
from login.mail import ensure_email_configured, EmailUnavailable


class Command(BaseCommand):
    help = 'Envia uma mensagem de teste para o destinatário indicado, sem exibir credenciais.'

    def add_arguments(self, parser):
        parser.add_argument('destinatario')

    def handle(self, *args, **options):
        try:
            validate_email(options['destinatario'])
        except ValidationError:
            raise CommandError('Informe um email de destino válido.') from None
        try:
            ensure_email_configured()
            count = send_mail(f'Teste de email — {settings.SITE_NAME}',
                f'A configuração de envio de emails de {settings.SITE_NAME} está respondendo.\n'
                f'Endereço configurado para os links: {settings.PUBLIC_SITE_URL}\n'
                'Esta mensagem não contém senha ou link de recuperação.',
                settings.DEFAULT_FROM_EMAIL, [options['destinatario']], fail_silently=False)
            if count != 1:
                raise EmailUnavailable('delivery_failed')
        except (SMTPException, OSError, EmailUnavailable) as exc:
            code = getattr(exc, 'smtp_code', None)
            detail = f' Código SMTP: {code}.' if isinstance(code, int) else ''
            raise CommandError('Não foi possível enviar. Confira a configuração e a autenticação do provedor.' + detail) from None
        self.stdout.write(self.style.SUCCESS('Mensagem de teste aceita pelo serviço de email. Confira a caixa de entrada e o spam.'))
