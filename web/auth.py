from django.contrib.auth import authenticate, login
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from rest_framework.authtoken.models import Token  # <- Importa o modelo de Token oficial
import json

@csrf_exempt
def api_login(request):
    if request.method != "POST":
        return JsonResponse({'detail': 'Método não permitido.'}, status=405)

    try:
        data = json.loads(request.body.decode())
        username = data.get('username')
        password = data.get('password')
    except Exception:
        return JsonResponse({'detail': 'Requisição mal formatada.'}, status=400)

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        # cria o token se não existir, ou retorna o já criado
        token, created = Token.objects.get_or_create(user=user)

        return JsonResponse({'authenticated': True, 'username': user.username, 'authToken': token.key})
    else:
        return JsonResponse({'detail': 'Credenciais inválidas.'}, status=401)