import hashlib
from django.conf import settings
from django.core.cache import cache


def allow_email_request(request, action, email):
    # Não usa X-Forwarded-For arbitrário nem guarda endereço de email em texto claro.
    identity = hashlib.sha256(email.strip().casefold().encode()).hexdigest()
    address = hashlib.sha256(request.META.get('REMOTE_ADDR', '').encode()).hexdigest()
    counter = f'auth-mail:{action}:ip:{address}'
    if not cache.add(counter, 1, 3600):
        try:
            count = cache.incr(counter)
        except ValueError:
            cache.set(counter, 1, 3600)
            count = 1
        if count > settings.AUTH_EMAIL_MAX_PER_IP:
            return False
    return cache.add(f'auth-mail:{action}:email:{identity}', True, settings.AUTH_EMAIL_COOLDOWN)
