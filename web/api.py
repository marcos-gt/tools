import json
from functools import wraps
from django.http import JsonResponse
from categoria.models import Categoria


def error(message, code='invalid_input', status=400, **extra):
    return JsonResponse({'success': False, 'error': message, 'code': code, **extra}, status=status)


def protected(view):
    @wraps(view)
    def wrapped(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return error('Autenticação obrigatória.', 'authentication_required', 401)
        return view(request, *args, **kwargs)
    return wrapped


def body(request):
    data = json.loads(request.body)
    if not isinstance(data, dict):
        raise ValueError('Objeto JSON esperado.')
    return data


def owned_category(user, value, allow_name=False):
    qs = Categoria.objects.filter(usuario=user, ativa=True)
    if str(value).isdigit():
        return qs.filter(pk=int(value)).first()
    if allow_name and isinstance(value, str):
        return qs.filter(nome=value).first()
    return None
