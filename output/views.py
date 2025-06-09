from django.shortcuts import render
from .models import Output
from django.http import JsonResponse


# Create your views here.
def output(request):
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
    outputs = Output.objects.filter(usuario=request.user).order_by('-data_criacao')
    data = [
        {
            'id': output.id,
            'conteudo': output.conteudo,
            'categorias': [cat.nome for cat in output.categoria.all()],
            'chat_id': output.chats.id,
            'data_criacao': output.data_criacao.isoformat(),
        }
        for output in outputs
    ]
    return JsonResponse({'outputs': data})