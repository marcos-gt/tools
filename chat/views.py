from django.http import JsonResponse
from web.api import protected, error, body, owned_category
from .models import Chat

@protected
def chat(request):
    if request.method != 'GET':
        return error('Método não permitido.', 'method_not_allowed', 405)
    chats = Chat.objects.filter(usuario=request.user, ativo=True, categoria__ativa=True,
        categoria__usuario=request.user).select_related('categoria').order_by('-timestamp', '-id')
    return JsonResponse({'chats': [{'id': c.id, 'message': c.message,
        'visualizationType': c.visualizationType, 'categoria': c.categoria.nome,
        'category_id': c.categoria_id, 'timestamp': c.timestamp.isoformat()} for c in chats]})

meus_chats = chat

@protected
def novo_chat(request):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    message = request.POST.get('message', '')
    category = owned_category(request.user, request.POST.get('category'))
    if not message.strip() or not category:
        return error('Mensagem e categoria válida são obrigatórias.')
    c = Chat.objects.create(usuario=request.user, categoria=category, message=message,
        visualizationType=request.POST.get('visualizationType', 'text'))
    return JsonResponse({'id': c.id, 'message': c.message, 'categoria': category.nome,
        'category_id': category.id, 'timestamp': c.timestamp.isoformat()}, status=201)

@protected
def inativar_chats(request):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    try:
        data = body(request)
    except (ValueError, UnicodeDecodeError):
        return error('JSON inválido.')
    category = owned_category(request.user, data.get('category_id', data.get('category')))
    if not category:
        return error('Categoria indisponível.', 'not_found', 404)
    count = Chat.objects.filter(usuario=request.user, categoria=category, ativo=True).update(ativo=False)
    return JsonResponse({'success': True, 'count': count})
