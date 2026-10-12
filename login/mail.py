from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from email.utils import parseaddr
from .tokens import activation_token


class EmailUnavailable(Exception):
    pass


def ensure_email_configured():
    try:
        validate_email(parseaddr(settings.DEFAULT_FROM_EMAIL)[1])
    except ValidationError:
        raise EmailUnavailable('sender_missing') from None
    if settings.EMAIL_BACKEND == 'django.core.mail.backends.smtp.EmailBackend' and not settings.EMAIL_HOST:
        raise EmailUnavailable('host_missing')


def send_templated_email(subject_template, text_template, html_template, context, recipient, from_email=None):
    ensure_email_configured()
    context = {**context, 'site_name':settings.SITE_NAME, 'site_url':settings.PUBLIC_SITE_URL,
               'expiry_minutes':(settings.PASSWORD_RESET_TIMEOUT + 59) // 60}
    subject = ''.join(render_to_string(subject_template, context).splitlines()).strip()
    message = EmailMultiAlternatives(subject, render_to_string(text_template, context),
                                    from_email or settings.DEFAULT_FROM_EMAIL, [recipient])
    if html_template:
        message.attach_alternative(render_to_string(html_template, context), 'text/html')
    if message.send(fail_silently=False) != 1:
        raise EmailUnavailable('delivery_failed')


def send_activation_email(user):
    path = reverse('activate_account', kwargs={'uidb64':urlsafe_base64_encode(force_bytes(user.pk)),
                                              'token':activation_token.make_token(user)})
    send_templated_email('registration/email/activation_subject.txt', 'registration/email/activation.txt',
                        'registration/email/activation.html', {'user':user, 'action_url':settings.PUBLIC_SITE_URL + path}, user.email)


def send_welcome_email(user):
    send_templated_email('registration/email/welcome_subject.txt', 'registration/email/welcome.txt',
                        'registration/email/welcome.html', {'user':user, 'action_url':settings.PUBLIC_SITE_URL + reverse('login')}, user.email)
