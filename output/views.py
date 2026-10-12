from django.http import JsonResponse, HttpResponse
from web.api import protected, error, body
from .models import Output

def serialize(o):
    return {'id': o.pk, 'data': o.data_criacao.isoformat(), 'usuario_id': o.usuario_id,
        'categoria': o.categoria_snapshot, 'modalidade': o.modalidade,
        'mensagens': o.mensagens_snapshot, 'payload': o.payload, 'modelo': o.modelo,
        'resposta_original': o.resposta_original, 'mermaid': o.conteudo, 'status': o.status,
        'codigo_erro': o.codigo_erro, 'duracao_ms': o.duracao_ms,
        'render_status': o.render_status}

@protected
def output(request):
    if request.method != 'GET':
        return error('Método não permitido.', 'method_not_allowed', 405)
    qs = Output.objects.filter(usuario=request.user).order_by('-data_criacao', '-id')
    return JsonResponse({'outputs': [serialize(o) for o in qs]})

@protected
def export(request, pk, format):
    if request.method != 'GET':
        return error('Método não permitido.', 'method_not_allowed', 405)
    o = Output.objects.filter(pk=pk, usuario=request.user).first()
    if not o:
        return error('Registro indisponível.', 'not_found', 404)
    if format == 'json':
        response = JsonResponse(serialize(o), json_dumps_params={'ensure_ascii': False, 'indent': 2})
    elif format == 'mmd':
        if not o.conteudo:
            return error('Registro sem código Mermaid.')
        response = HttpResponse(o.conteudo, content_type='text/plain; charset=utf-8')
    else:
        return error('Formato inválido.')
    response['Content-Disposition'] = f'attachment; filename="geracao-{o.pk}.{format}"'
    return response

@protected
def render_status(request, pk):
    if request.method != 'POST':
        return error('Método não permitido.', 'method_not_allowed', 405)
    o = Output.objects.filter(pk=pk, usuario=request.user, status='success').first()
    if not o:
        return error('Registro indisponível.', 'not_found', 404)
    try:
        status = body(request).get('status')
    except (ValueError, UnicodeDecodeError):
        return error('JSON inválido.')
    if status not in ('success', 'failure'):
        return error('Status inválido.')
    o.render_status = status
    o.save(update_fields=['render_status'])
    return JsonResponse({'success': True})
