from django.http import JsonResponse
from django.shortcuts import render
from django.db import transaction
from web.api import protected, error, body, owned_category
from .models import Categoria

@protected
def categoria(request):
    if request.method != 'GET':
        return error('Método não permitido.', 'method_not_allowed', 405)
    qs = Categoria.objects.filter(usuario=request.user, ativa=True).order_by('nome', 'id')
    return JsonResponse({'categorias': [{'id': c.id, 'nome': c.nome, 'descricao': c.descricao,
        'ativa': c.ativa, 'data_criacao': c.data_criacao.isoformat()} for c in qs]})

list_all = categoria

@protected
def renderizar(request):
    return render(request, 'categoria.html')

@protected
def receberCategorias(request):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    try:
        data = body(request)
    except (ValueError, UnicodeDecodeError):
        return error('JSON inválido.')
    names = data.get('categorias', [data.get('nome')])
    if not isinstance(names, list) or not names or any(not isinstance(n, str) or not n.strip() or len(n.strip()) > 255 for n in names):
        return error('Informe nomes válidos com até 255 caracteres.')
    created = []
    with transaction.atomic():
        for name in names:
            c, new = Categoria.objects.get_or_create(usuario=request.user, nome=name.strip(), defaults={'descricao': ''})
            if not c.ativa:
                c.ativa = True
                c.save(update_fields=['ativa'])
            if new:
                created.append(c.nome)
    return JsonResponse({'success': True, 'criadas': created})

@protected
def inativar_categoria(request):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    try:
        data = body(request)
    except (ValueError, UnicodeDecodeError):
        return error('JSON inválido.')
    c = owned_category(request.user, data.get('category_id', data.get('category')), allow_name=True)
    if not c:
        return error('Categoria indisponível.', 'not_found', 404)
    c.ativa = False
    c.save(update_fields=['ativa'])
    return JsonResponse({'success': True})
