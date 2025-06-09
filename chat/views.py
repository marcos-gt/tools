from django.contrib.auth.decorators import login_required
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
        }
        for chat in chats
    ]
    return JsonResponse({'chats': data})
