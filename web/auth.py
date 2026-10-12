from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from web.api import body, error

def api_login(request):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    try:
        data = body(request)
    except (ValueError, UnicodeDecodeError):
        return error('JSON inválido.')
    if not isinstance(data.get('username'), str) or not isinstance(data.get('password'), str):
        return error('Credenciais inválidas.')
    user = authenticate(request, username=data['username'], password=data['password'])
    if user is None:
        return JsonResponse({'authenticated': False, 'detail': 'Credenciais inválidas.'}, status=401)
    login(request, user)
    return JsonResponse({'authenticated': True, 'username': user.username})
