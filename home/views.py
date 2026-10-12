import logging
import time
from django.http import JsonResponse
from django.shortcuts import render, redirect
from categoria.models import Categoria
from chat.models import Chat
from output.models import Output
from web.api import error, owned_category
from .inference import build_payload, infer, InferenceError

logger = logging.getLogger(__name__)

def index(request):
    if not request.user.is_authenticated:
        if request.method == 'GET':
            return redirect('/login/?next=/')
        return error('Autenticação obrigatória.', 'authentication_required', 401)
    if request.method == 'POST':
        category = owned_category(request.user, request.POST.get('generatorCategory'))
        mode = request.POST.get('visualizationType')
        if not category:
            return error('Categoria inválida ou indisponível.')
        chats = Chat.objects.filter(usuario=request.user, categoria=category, ativo=True).order_by('timestamp', 'id')
        snapshots = [{'id': c.id, 'texto': c.message, 'timestamp': c.timestamp.isoformat()}
                     for c in chats if c.message.strip()]
        if not snapshots:
            return error('A categoria não contém mensagens ativas com conteúdo válido.')
        try:
            payload = build_payload(category.nome, snapshots, mode)
        except InferenceError as exc:
            return error(exc.message, exc.code, exc.status)
        record = Output.objects.create(usuario=request.user, conteudo='', modalidade=mode,
            categoria_snapshot={'id': category.id, 'nome': category.nome}, mensagens_snapshot=snapshots,
            payload=payload, modelo=payload['model'], status='pending')
        record.categoria.add(category)
        started = time.monotonic()
        try:
            original, normalized = infer(payload, mode)
            record.resposta_original = original
            record.conteudo = normalized
            record.status = 'success'
        except InferenceError as exc:
            record.status = 'failure'
            record.codigo_erro = exc.code
            record.resposta_original = exc.original
            logger.warning('Inferência falhou: registro=%s código=%s', record.pk, exc.code)
            return error(exc.message, exc.code, exc.status, output_id=record.pk)
        except Exception:
            record.status = 'failure'
            record.codigo_erro = 'internal_error'
            logger.error('Falha interna na inferência: registro=%s', record.pk)
            return error('Falha interna ao processar a geração.', 'internal_error', 500, output_id=record.pk)
        finally:
            record.duracao_ms = round((time.monotonic() - started) * 1000)
            record.save()
        return JsonResponse({'success': True, 'output': record.conteudo, 'output_id': record.pk,
            'categoria': category.nome, 'modalidade': mode, 'total_chats': len(snapshots),
            'syntax_validation': 'pending_frontend'})
    if request.method != 'GET':
        return error('Método não permitido.', 'method_not_allowed', 405)
    categories = Categoria.objects.filter(usuario=request.user, ativa=True).order_by('nome', 'id')
    chats = Chat.objects.filter(usuario=request.user, ativo=True, categoria__ativa=True,
                                categoria__usuario=request.user).order_by('-timestamp', '-id')
    return render(request, 'index.html', {'categorias': categories, 'chats': chats, 'qtd': chats.count()})
