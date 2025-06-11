from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from categoria.models import Categoria


from django.shortcuts import render

from chat.models import Chat
from django.http import JsonResponse
@login_required

def chat(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
    chats = Chat.objects.order_by('-timestamp')
    data = [
        {
            'id': chat.id,
            'message': chat.message,
            'visualizationType': chat.visualizationType if hasattr(chat, 'visualizationType') else None,
            'categoria': chat.categoria.nome if hasattr(chat, 'categoria') else None,
            'timestamp': chat.timestamp.isoformat(),
        }
        for chat in chats
    ]
    return JsonResponse({'chats': data})
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Chat

@login_required
def meus_chats(request):
    chats = Chat.objects.filter(usuario=request.user).order_by('-timestamp')
    data = [
        {
            'id': chat.id,
            'message': chat.message,
            'timestamp': chat.timestamp.isoformat(),
            'usuario': chat.usuario.username,
            'visualizationType': chat.visualizationType if hasattr(chat, 'visualizationType') else None,
            'categoria': chat.categoria.nome if hasattr(chat, 'categoria') else None,
        }
        for chat in chats
    ]
    return JsonResponse({'chats': data})
def novo_chat(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        category_id = request.POST.get('category')
        visualization_type = request.POST.get('visualizationType')

        if not message or not category_id or not visualization_type:
            return JsonResponse({'error': 'Todos os campos são obrigatórios'}, status=400)

        # Busca a categoria pelo ID recebido
        categoria = get_object_or_404(Categoria, pk=category_id)

        chat = Chat.objects.create(
            usuario=request.user,
            message=message,
            categoria=categoria,
            visualizationType=visualization_type  # se esse campo existir no modelo!
        )
        return JsonResponse({
            'id': chat.id,
            'message': chat.message,
            'usuario': chat.usuario.username,
            'visualizationType': chat.visualizationType,
            'timestamp': chat.timestamp.isoformat(),
        }, status=201)

    return JsonResponse({'error': 'Método não permitido'}, status=405)

