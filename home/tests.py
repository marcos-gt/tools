import json
from unittest.mock import patch, Mock
import requests
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.utils import timezone
from categoria.models import Categoria
from chat.models import Chat
from output.models import Output
from .inference import build_payload, normalize, InferenceError


class GenerationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user('pesquisador', password='test-password')
        self.other = User.objects.create_user('outro', password='test-password')
        self.cat = Categoria.objects.create(usuario=self.user, nome='BD01')
        self.foreign = Categoria.objects.create(usuario=self.other, nome='BD01')
        self.client.force_login(self.user)

    def generate(self, mode='mapa-mental', category=None):
        return self.client.post('/', {'generatorCategory': category or self.cat.pk, 'visualizationType': mode})

    def response(self, content='mindmap\n  root((Chaves))\n    Integridade'):
        response = Mock()
        response.json.return_value = {'done': True, 'message': {'content': content}}
        return response

    @patch('home.inference.requests.post')
    def test_full_order_quantity_and_isolation(self, post):
        post.return_value = self.response()
        messages = [Chat.objects.create(usuario=self.user, categoria=self.cat,
                    message=f'Mensagem {i}: texto integral com mais de vinte caracteres') for i in range(12)]
        Chat.objects.filter(pk__in=[m.pk for m in messages]).update(timestamp=timezone.now())
        Chat.objects.create(usuario=self.user, categoria=self.cat, message='inativa', ativo=False)
        Chat.objects.create(usuario=self.other, categoria=self.cat, message='outro usuário')
        Chat.objects.create(usuario=self.other, categoria=self.foreign, message='outra categoria')
        result = self.generate()
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.json()['total_chats'], 12)
        payload = post.call_args.kwargs['json']
        material = json.loads(payload['messages'][1]['content'])['mensagens']
        self.assertEqual([s['id'] for s in material], [m.pk for m in messages])
        self.assertEqual([s['texto'] for s in material], [m.message for m in messages])
        self.assertEqual(Output.objects.get().mensagens_snapshot, material)

    @patch('home.inference.requests.post')
    def test_invalid_input_does_not_call_service(self, post):
        self.assertEqual(self.generate().status_code, 400)
        Chat.objects.create(usuario=self.user, categoria=self.cat, message=' ')
        self.assertEqual(self.generate().status_code, 400)
        Chat.objects.create(usuario=self.user, categoria=self.cat, message='Conteúdo')
        self.assertEqual(self.generate('invalida').status_code, 400)
        self.assertEqual(self.generate(category=self.foreign.pk).status_code, 400)
        post.assert_not_called()

    def test_prompts_distinct_and_limit(self):
        snapshots = [{'id': 1, 'texto': 'Chaves primárias'}]
        mind = build_payload('BD', snapshots, 'mapa-mental')
        flow = build_payload('BD', snapshots, 'fluxograma')
        self.assertIn('mindmap', mind['messages'][0]['content'])
        self.assertIn('flowchart TD', flow['messages'][0]['content'])
        self.assertNotEqual(mind, flow)
        with override_settings(OLLAMA_MAX_INPUT_CHARS=5):
            with self.assertRaises(InferenceError):
                build_payload('BD', snapshots, 'mapa-mental')

    def test_normalization(self):
        code = 'mindmap\n  root((Chaves))\n    Integridade'
        self.assertEqual(normalize('<think>conteúdo privado</think>\n```mermaid\n' + code + '\n```', 'mapa-mental'), code)
        self.assertEqual(normalize(code, 'mapa-mental'), code)
        for text in ('', '<think>incompleto', '```mermaid\n'+code, code+'\n```',
                     'explicação\n'+code, 'flowchart TD\n A-->B', 'mindmap', 'mindmap\n <script>alert(1)</script>'):
            with self.subTest(text=text), self.assertRaises(InferenceError):
                normalize(text, 'mapa-mental')

    @patch('home.inference.requests.post')
    def test_failures_are_not_success(self, post):
        Chat.objects.create(usuario=self.user, categoria=self.cat, message='Chaves')
        for exc, status, code in [(requests.ConnectionError(), 502, 'connection_unavailable'),
                                  (requests.Timeout(), 504, 'timeout'),
                                  (requests.HTTPError(), 502, 'upstream_http')]:
            with self.subTest(code=code):
                post.side_effect = exc
                response = self.generate()
                self.assertEqual(response.status_code, status)
                self.assertEqual(response.json()['code'], code)
        post.side_effect = None
        for content, code in [('', 'empty_content'), ('sem código', 'incompatible_structure'),
                              ('<think>incompleto', 'incomplete_content')]:
            post.return_value = self.response(content)
            result = self.generate()
            self.assertEqual(result.status_code, 502)
            self.assertEqual(result.json()['code'], code)
            self.assertEqual(Output.objects.get(pk=result.json()['output_id']).resposta_original, content)
        response = self.response()
        response.json.side_effect = ValueError()
        post.return_value = response
        self.assertEqual(self.generate().json()['code'], 'invalid_json')
        response.json.side_effect = None
        response.json.return_value = []
        self.assertEqual(self.generate().json()['code'], 'unexpected_response')
        response.json.return_value = {'done': False, 'message': {'content': 'mindmap\n root'}}
        self.assertEqual(self.generate().json()['code'], 'incomplete_response')
        self.assertFalse(Output.objects.exclude(status='failure').exists())

    @override_settings(OLLAMA_TOKEN='private-token', OLLAMA_BASE_URL='https://private-server.example')
    @patch('home.inference.requests.post')
    def test_snapshots_exports_no_secrets_and_no_overwrite(self, post):
        post.return_value = self.response('<think>raciocínio</think>\n```mermaid\nmindmap\n  root((Chaves))\n```')
        chat = Chat.objects.create(usuario=self.user, categoria=self.cat, message='Mensagem original completa')
        first = self.generate().json()['output_id']
        chat.message = 'Editada'
        chat.save()
        self.generate()
        self.assertEqual(Output.objects.count(), 2)
        response = self.client.get(f'/output/{first}/export/json/')
        self.assertEqual(response.status_code, 200)
        evidence = response.json()
        self.assertEqual(evidence['mensagens'][0]['texto'], 'Mensagem original completa')
        self.assertIn('raciocínio', evidence['resposta_original'])
        self.assertNotIn('raciocínio', evidence['mermaid'])
        self.assertNotIn('private-token', response.content.decode())
        self.assertNotIn('private-server.example', response.content.decode())
        self.assertEqual(post.call_args.kwargs['headers']['Authorization'], 'Bearer private-token')
        self.assertEqual(self.client.get(f'/output/{first}/export/mmd/').content.decode(), evidence['mermaid'])

    def test_access_and_mutation_isolation(self):
        chat = Chat.objects.create(usuario=self.other, categoria=self.foreign, message='Segredo')
        output = Output.objects.create(usuario=self.other, conteudo='Segredo')
        self.assertEqual(self.client.get('/chat/').json()['chats'], [])
        self.assertEqual(self.client.get('/chat/meus/').json()['chats'], [])
        self.assertEqual([c['id'] for c in self.client.get('/categoria/').json()['categorias']], [self.cat.id])
        self.assertEqual(self.client.get('/output/').json()['outputs'], [])
        for format in ('json', 'mmd'):
            self.assertEqual(self.client.get(f'/output/{output.pk}/export/{format}/').status_code, 404)
        self.assertEqual(self.client.post('/chat/novo/', {'category': self.foreign.pk, 'message': 'Ataque'}).status_code, 400)
        for url in ('/categoria/inativar/', '/chat/inativar/'):
            self.assertEqual(self.client.post(url, {'category_id': self.foreign.pk}, content_type='application/json').status_code, 404)
        chat.refresh_from_db()
        self.foreign.refresh_from_db()
        self.assertTrue(chat.ativo)
        self.assertTrue(self.foreign.ativa)
        self.client.logout()
        for url in ('/chat/', '/categoria/', '/output/', '/chat/novo/'):
            self.assertEqual(self.client.get(url).status_code, 401)
        self.assertEqual(self.client.post('/', {}).status_code, 302)

    def test_csrf_login_and_protected_posts(self):
        secure = Client(enforce_csrf_checks=True)
        secure.force_login(self.user)
        for url in ('/', '/chat/novo/', '/chat/inativar/', '/categoria/inativar/', '/categoria/receberCategorias/', '/api-login/'):
            self.assertEqual(secure.post(url, {}).status_code, 403)
        secure.logout()
        self.assertEqual(secure.get('/login/').status_code, 200)
        self.assertIn('csrftoken', secure.cookies)
        response = secure.post('/api-login/', {'username': 'pesquisador', 'password': 'test-password'},
            content_type='application/json', HTTP_X_CSRFTOKEN=secure.cookies['csrftoken'].value)
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('authToken', response.json())

    def test_creation_same_name_and_inactivation(self):
        result = self.client.post('/categoria/receberCategorias/', {'nome': 'BD02'}, content_type='application/json')
        self.assertEqual(result.status_code, 200)
        self.assertEqual(Categoria.objects.get(nome='BD02').usuario, self.user)
        chat = self.client.post('/chat/novo/', {'message': 'Texto inteiro', 'category': self.cat.pk})
        self.assertEqual(chat.status_code, 201)
        self.assertEqual(self.client.post('/chat/inativar/', {'category': self.cat.pk}, content_type='application/json').status_code, 200)
        self.assertEqual(self.client.get('/chat/').json()['chats'], [])

    def test_home_template_contains_generation_mode(self):
        response = self.client.get('/')
        self.assertContains(response, 'id="generatorMode"')
        self.assertContains(response, 'mermaid@11.12.0')
