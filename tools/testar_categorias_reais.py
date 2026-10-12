"""Preenche casos autorizados e testa HTTP/Django/Ollama reais sem apagar dados.

PowerShell: definir TCC_LOGIN_PASSWORD no processo e executar com .venv-tcc.
Credenciais não são salvas no relatório. Os casos são sintéticos, exceto a
transcrição literal da imagem do primeiro caso.
"""
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import sys
import time

import requests

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'web.settings')
os.environ['DJANGO_DEBUG'] = 'true'
import django
django.setup()
from django.conf import settings
from django.contrib.auth.models import User
from categoria.models import Categoria
from chat.models import Chat

REPORT = ROOT / os.getenv('TCC_REAL_REPORT', 'docs/testes-reais-2026-10-12')
REPORT.mkdir(parents=True, exist_ok=True)
BASE = 'http://127.0.0.1:55435'
password = os.environ['TCC_LOGIN_PASSWORD']
username = os.getenv('TCC_LOGIN_USER', 'tcc')
cases = json.loads((REPORT / 'categorias.json').read_text(encoding='utf-8'))


def post(session, path, *, data=None, json_data=None, timeout=30):
    return session.post(BASE + path, data=data, json=json_data,
                        headers={'X-CSRFToken': session.cookies.get('csrftoken', '')}, timeout=timeout)


def login(user, credential):
    session = requests.Session()
    session.get(BASE + '/login/', timeout=10).raise_for_status()
    response = post(session, '/api-login/', json_data={'username': user, 'password': credential})
    response.raise_for_status()
    return session


log_file = (ROOT / '.test-artifacts/django-real.log').open('w', encoding='utf-8')
server = subprocess.Popen([sys.executable, 'manage.py', 'runserver', '127.0.0.1:55435', '--noreload'],
                          stdout=log_file, stderr=log_file, creationflags=subprocess.CREATE_NO_WINDOW)
try:
    for _ in range(60):
        if server.poll() is not None:
            raise RuntimeError('Servidor de teste não iniciou; confira o log técnico local.')
        try:
            if requests.get(BASE + '/login/', timeout=1).status_code == 200:
                break
        except requests.RequestException:
            time.sleep(.25)
    session = login(username, password)
    print('LOGIN HTTP OK; preparando 15 categorias', flush=True)
    user = User.objects.get(username=username)
    for case in cases:
        result = post(session, '/categoria/receberCategorias/', json_data={'nome': case['nome']})
        result.raise_for_status()
        category = Categoria.objects.get(usuario=user, nome=case['nome'])
        case['categoria_id'] = category.pk
        existing = set(Chat.objects.filter(usuario=user, categoria=category, ativo=True).values_list('message', flat=True))
        for message in case['mensagens']:
            if message not in existing:
                result = post(session, '/chat/novo/', data={'category': category.pk, 'message': message, 'visualizationType': 'text'})
                result.raise_for_status()
                existing.add(message)
        qs = Chat.objects.filter(usuario=user, categoria=category, ativo=True).order_by('timestamp', 'id')
        case['mensagens_efetivas'] = [{'id': c.pk, 'texto': c.message} for c in qs if c.message.strip()]
        print('CATEGORIA', case['caso'], 'ID', category.pk, 'mensagens', len(case['mensagens_efetivas']), flush=True)
    cat13 = Categoria.objects.get(pk=cases[12]['categoria_id'])
    inactive, _ = Chat.objects.get_or_create(usuario=user, categoria=cat13,
        message='Mensagem INATIVA de controle: não deve entrar no payload de geração.', defaults={'ativo': False})
    if inactive.ativo:
        raise RuntimeError('Controle inativo existente foi alterado; não será sobrescrito.')
    empty, _ = Categoria.objects.get_or_create(usuario=user, nome='SIM16 - CONTROLE SEM MENSAGENS', defaults={'descricao': 'Controle negativo de validação.'})
    checks = []
    csrf_response = session.post(BASE + '/categoria/receberCategorias/', json={'nome':'NAO_CRIAR_SEM_CSRF'}, timeout=10)
    checks.append({'teste':'POST autenticado sem CSRF é rejeitado','http':csrf_response.status_code,'esperado':403,'passou':csrf_response.status_code == 403})
    for label, data, expected in [
        ('modalidade inválida', {'generatorCategory': cases[0]['categoria_id'], 'visualizationType': 'invalida'}, 400),
        ('categoria sem mensagens', {'generatorCategory': empty.pk, 'visualizationType': 'mapa-mental'}, 400),
        ('categoria inexistente', {'generatorCategory': 2147483647, 'visualizationType': 'mapa-mental'}, 400),
    ]:
        response = post(session, '/', data=data)
        checks.append({'teste': label, 'http': response.status_code, 'esperado': expected, 'passou': response.status_code == expected})
    secondary_name = 'tcc_isolamento_' + time.strftime('%Y%m%d_%H%M%S')
    secondary_password = secrets.token_urlsafe(32)
    secondary = User.objects.create_user(username=secondary_name, password=secondary_password)
    secondary_category = Categoria.objects.create(usuario=secondary, nome=cases[1]['nome'], descricao='Fixture de isolamento com mesmo nome, outro proprietário.')
    Chat.objects.create(usuario=secondary, categoria=secondary_category, message='Controle de isolamento de outro usuário: não deve aparecer na conta tcc.')
    for label, path, json_data in [
        ('categoria de outro usuário não gera', '/', None),
        ('categoria de outro usuário não inativa', '/categoria/inativar/', {'category_id': secondary_category.pk}),
        ('chats de outro usuário não inativam', '/chat/inativar/', {'category_id': secondary_category.pk}),
    ]:
        response = post(session, path, json_data=json_data, data={'generatorCategory': secondary_category.pk, 'visualizationType': 'mapa-mental'} if json_data is None else None)
        expected = 400 if path == '/' else 404
        checks.append({'teste': label, 'http': response.status_code, 'esperado': expected, 'passou': response.status_code == expected})
    visible = session.get(BASE + '/chat/', timeout=10).json()['chats']
    checks.append({'teste': 'listagem exclui outro proprietário', 'passou': all(c['category_id'] != secondary_category.pk for c in visible)})
    manifest = {'data': '2026-10-12', 'modelo': settings.OLLAMA_MODEL,
                'parametros': {'temperature': settings.OLLAMA_TEMPERATURE, 'num_ctx': settings.OLLAMA_NUM_CTX,
                               'read_timeout': settings.OLLAMA_READ_TIMEOUT, 'think': settings.OLLAMA_THINK},
                'fase': os.getenv('TCC_TEST_PHASE','baseline'), 'usuario': username, 'casos': cases, 'controles': checks,
                'controle_inativo_id': inactive.pk, 'usuario_isolamento': secondary_name,
                'referencia_visual_sha256': hashlib.sha256((ROOT / 'diagrama-1.png').read_bytes()).hexdigest(),
                'natureza': 'Testes funcionais com entradas sintéticas e saídas reais do Ollama; não são resultados conceituais validados do TCC.'}
    headers = {'Authorization': 'Bearer ' + settings.OLLAMA_TOKEN} if settings.OLLAMA_TOKEN else {}
    for endpoint in ('version', 'tags'):
        response = requests.get(settings.OLLAMA_BASE_URL + '/api/' + endpoint, headers=headers, timeout=(5,15))
        response.raise_for_status()
        data = response.json()
        manifest['ollama_' + endpoint] = data if endpoint == 'version' else [
            {'name': m.get('name'), 'digest': m.get('digest'), 'details': m.get('details')}
            for m in data.get('models', []) if m.get('name') == settings.OLLAMA_MODEL]
    (REPORT / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    env = os.environ.copy()
    env['TCC_REAL_BASE'] = BASE
    env['TCC_BROWSER_TIMEOUT'] = str(int((settings.OLLAMA_CONNECT_TIMEOUT + settings.OLLAMA_READ_TIMEOUT + 60) * 1000))
    print('CONTROLES', sum(c['passou'] for c in checks), '/', len(checks), flush=True)
    result = subprocess.run(['node', 'tools/testar_categorias_reais.cjs'], env=env)
    result.check_returncode()
    second_session = login(secondary_name, secondary_password)
    records = json.loads((REPORT / 'resultados.json').read_text(encoding='utf-8'))
    own_output = next((r.get('output_id') for r in records if r.get('output_id')), None)
    if own_output:
        response = second_session.get(BASE + f'/output/{own_output}/export/json/', timeout=10)
        checks.append({'teste': 'outro usuário não exporta output de tcc', 'http': response.status_code, 'esperado':404, 'passou':response.status_code == 404})
    manifest['controles'] = checks
    (REPORT / 'manifesto.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
finally:
    server.terminate()
    server.wait(timeout=15)
    log_file.close()
    print('Servidor Django de teste encerrado; PostgreSQL e Ollama existentes preservados.', flush=True)
