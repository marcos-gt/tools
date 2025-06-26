from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from categoria.models import Categoria
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
import json
from .models import Chat



@login_required
def chat(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Usuário não autenticado'}, status=401)
    chats = Chat.objects.order_by('-timestamp').filter(categoria__ativa=True)
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
    print("Dados dos chats:", data)
    return JsonResponse({'chats': data})

@login_required
def meus_chats(request):
    chats = Chat.objects.filter(usuario=request.user).order_by('-timestamp').filter(categoria__ativa=True)
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
    print("Dados dos meus chats:", data.count)
    return JsonResponse({'chats': data})
def novo_chat(request):
    if request.method == 'POST':
        message = request.POST.get('message', '')
        category_data = request.POST.get('category')  # Pode ser ID ou nome
        visualization_type = request.POST.get('visualizationType')

        if not message or not category_data or not visualization_type:
            return JsonResponse({'error': 'Todos os campos são obrigatórios'}, status=400)

        try:
            if category_data.isdigit():
                categoria = get_object_or_404(Categoria, pk=int(category_data))
            else:
                categoria = get_object_or_404(Categoria, nome__iexact=category_data)

            chat = Chat.objects.create(
                usuario=request.user,
                message=message,
                categoria=categoria,
                visualizationType=visualization_type
            )

            return JsonResponse({
                'id': chat.id,
                'message': chat.message,
                'usuario': chat.usuario.username,
                'visualizationType': chat.visualizationType,
                'categoria': chat.categoria.nome,
                'timestamp': chat.timestamp.isoformat(),
            }, status=201)

        except Categoria.DoesNotExist:
            return JsonResponse({
                'error': f'Categoria "{category_data}" não encontrada'
            }, status=404)
        except Exception as e:
            return JsonResponse({
                'error': f'Erro interno: {str(e)}'
            }, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)


@login_required
@csrf_exempt
def inativar_chats(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category = data.get('category')
            print("Dados recebidos para inativar chats view chats:", data)
            if not category:
                return JsonResponse({'error': 'Categoria é obrigatória'}, status=400)

            from categoria.models import Categoria
            try:
                categoria_obj = Categoria.objects.get(nome__iexact=category)
            except Categoria.DoesNotExist:
                return JsonResponse({'error': 'Categoria não encontrada'}, status=404)

            chats_atualizados = Chat.objects.filter(
                usuario=request.user,
                categoria=categoria_obj,
                ativo=True
            ).update(ativo=False)

            return JsonResponse({
                'success': True,
                'count': chats_atualizados,
                'message': f'{chats_atualizados} chats foram inativados'
            })

        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)
