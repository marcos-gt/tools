import re
from datetime import datetime, timedelta
from smtplib import SMTPException
from unittest.mock import patch
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.core.cache import cache
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from .models import AccountEmail
from .tokens import activation_token


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    DEFAULT_FROM_EMAIL='Sistema <notificacoes@example.test>', PUBLIC_SITE_URL='https://app.example.test',
    CACHES={'default':{'BACKEND':'django.core.cache.backends.locmem.LocMemCache','LOCATION':'auth-test-cache'}})
class AccountTests(TestCase):
    def setUp(self):
        cache.clear()
        self.data = {'first_name':'Ana', 'username':'ana_teste', 'email':'Ana@Example.test',
                     'password1':'Senha-Forte!4086', 'password2':'Senha-Forte!4086'}

    def signup(self):
        return self.client.post(reverse('signup'), self.data)

    def pending(self):
        user = User.objects.create_user('pendente', email='pendente@example.test', password='Senha-Forte!4086', is_active=False)
        AccountEmail.objects.create(user=user, email=user.email)
        return user

    def activation_url(self, user, token=None):
        return reverse('activate_account', kwargs={'uidb64':urlsafe_base64_encode(force_bytes(user.pk)),
                                                  'token':token or activation_token.make_token(user)})

    def test_signup_password_hash_inactive_and_multipart_email(self):
        response = self.signup()
        self.assertRedirects(response, reverse('signup_done'))
        user = User.objects.get(username='ana_teste')
        self.assertFalse(user.is_active)
        self.assertEqual(user.email, 'ana@example.test')
        self.assertTrue(user.check_password(self.data['password1']))
        self.assertNotEqual(user.password, self.data['password1'])
        self.assertEqual(AccountEmail.objects.get(user=user).email, user.email)
        self.assertEqual(len(mail.outbox),1)
        self.assertEqual(mail.outbox[0].to, [user.email])
        self.assertTrue(mail.outbox[0].alternatives)
        self.assertIn('https://app.example.test/login/confirmar-email/',mail.outbox[0].body)
        self.assertNotIn(self.data['password1'],mail.outbox[0].body)
        self.assertEqual(self.client.post('/api-login/', {'username':user.username,'password':self.data['password1']},content_type='application/json').status_code,401)

    def test_activation_requires_post_is_one_use_and_sends_welcome(self):
        user = self.pending()
        url = self.activation_url(user)
        self.assertContains(self.client.get(url), 'Confirmar meu email')
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertRedirects(self.client.post(url),reverse('activation_done'))
        user.refresh_from_db()
        self.assertTrue(user.is_active)
        self.assertIsNotNone(user.account_email.verified_at)
        self.assertEqual(len(mail.outbox),1)
        self.assertIn('Sua conta está pronta',mail.outbox[0].subject)
        self.assertNotContains(self.client.get(url),'Confirmar meu email')
        self.assertEqual(self.client.post('/api-login/',{'username':user.username,'password':'Senha-Forte!4086'},content_type='application/json').status_code,200)

    def test_activation_invalid_expired_and_wrong_purpose_tokens(self):
        user = self.pending()
        now = datetime(2026,10,12,12,0)
        with patch.object(activation_token, '_now', return_value=now):
            token = activation_token.make_token(user)
        with patch.object(activation_token, '_now', return_value=now+timedelta(hours=2)):
            self.assertNotContains(self.client.get(self.activation_url(user,token)),'Confirmar meu email')
        wrong = default_token_generator.make_token(user)
        self.assertNotContains(self.client.get(self.activation_url(user,wrong)),'Confirmar meu email')
        self.assertEqual(self.client.get('/login/confirmar-email/invalido/invalido/').status_code,200)
        user.refresh_from_db()
        self.assertFalse(user.is_active)

    def test_activation_does_not_reactivate_disabled_confirmed_account(self):
        user=self.pending()
        self.client.post(self.activation_url(user))
        user.refresh_from_db()
        user.is_active=False
        user.save()
        self.assertNotContains(self.client.get(self.activation_url(user)),'Confirmar meu email')

    def test_duplicates_case_insensitive_and_weak_password(self):
        User.objects.create_user('existente', email='ANA@example.test')
        self.assertContains(self.signup(),'Este email já possui')
        self.assertFalse(User.objects.filter(username='ana_teste').exists())
        self.data.update(email='outra@example.test',password1='12345678',password2='12345678')
        self.signup()
        self.assertFalse(User.objects.filter(username='ana_teste').exists())
        self.data.update(username='existente',password1='Senha-Forte!4086',password2='Senha-Forte!4086')
        self.assertContains(self.signup(),'já existe')

    @patch('login.views.send_activation_email', side_effect=SMTPException('private-smtp-information'))
    def test_smtp_signup_failure_rolls_back_and_hides_details(self, send):
        response=self.signup()
        self.assertEqual(response.status_code,503)
        self.assertContains(response,'cadastro não foi concluído',status_code=503)
        self.assertNotContains(response,'private-smtp-information',status_code=503)
        self.assertFalse(User.objects.filter(username='ana_teste').exists())
        self.assertEqual(AccountEmail.objects.count(),0)

    @override_settings(EMAIL_BACKEND='django.core.mail.backends.smtp.EmailBackend',EMAIL_HOST='',DEFAULT_FROM_EMAIL='')
    def test_unconfigured_mail_shows_useful_error_without_creating_user(self):
        self.assertEqual(self.signup().status_code,503)
        self.assertFalse(User.objects.filter(username='ana_teste').exists())
        self.assertEqual(self.client.post(reverse('password_reset'),{'email':'unknown@example.test'}).status_code,503)

    def test_resend_and_recovery_do_not_disclose_accounts(self):
        self.pending()
        known=self.client.post(reverse('resend_confirmation'),{'email':'pendente@example.test'},follow=True)
        unknown=self.client.post(reverse('resend_confirmation'),{'email':'unknown@example.test'},follow=True)
        self.assertEqual(known.content,unknown.content)
        self.assertEqual(len(mail.outbox),1)
        for email in ('pendente@example.test','missing@example.test'):
            self.assertRedirects(self.client.post(reverse('password_reset'),{'email':email}),reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox),1)  # conta inativa não recebe reset

    def test_password_reset_round_trip_expiry_and_reuse(self):
        user=User.objects.create_user('ativo',email='ativo@example.test',password='Senha-Antiga!5863')
        response=self.client.post(reverse('password_reset'),{'email':user.email})
        self.assertRedirects(response,reverse('password_reset_done'))
        self.assertEqual(len(mail.outbox),1)
        self.assertIn('https://app.example.test',mail.outbox[0].body)
        self.assertNotIn('Senha-Antiga!5863',mail.outbox[0].body)
        path=re.search(r'https://app.example.test([^\s]+)',mail.outbox[0].body).group(1)
        confirm=self.client.get(path)
        self.assertEqual(confirm.status_code,302)
        form_url=confirm.url
        response=self.client.post(form_url,{'new_password1':'Senha-Nova!6932','new_password2':'Senha-Nova!6932'})
        self.assertRedirects(response,reverse('password_reset_complete'))
        user.refresh_from_db()
        self.assertTrue(user.check_password('Senha-Nova!6932'))
        self.assertFalse(user.check_password('Senha-Antiga!5863'))
        self.assertContains(self.client.get(path),'Este link é inválido')
        now=datetime(2026,10,12,12,0)
        with patch.object(default_token_generator,'_now',return_value=now):
            token=default_token_generator.make_token(user)
        expired=reverse('password_reset_confirm',kwargs={'uidb64':urlsafe_base64_encode(force_bytes(user.pk)),'token':token})
        with patch.object(default_token_generator,'_now',return_value=now+timedelta(hours=2)):
            self.assertContains(self.client.get(expired),'Este link é inválido')

    @patch('login.forms.send_templated_email',side_effect=SMTPException('private-server'))
    def test_reset_runtime_mail_error_has_same_public_response(self, send):
        User.objects.create_user('ativo',email='ativo@example.test',password='Senha-Antiga!5863')
        known=self.client.post(reverse('password_reset'),{'email':'ativo@example.test'},follow=True)
        missing=self.client.post(reverse('password_reset'),{'email':'missing@example.test'},follow=True)
        self.assertEqual(known.content,missing.content)
        self.assertNotContains(known,'private-server')

    @override_settings(ALLOWED_HOSTS=['testserver','attacker.example'])
    def test_email_links_ignore_request_host_and_login_redirect_is_safe(self):
        user=User.objects.create_user('ativo',email='ativo@example.test',password='Senha-Antiga!5863')
        self.client.post(reverse('password_reset'),{'email':user.email},HTTP_HOST='attacker.example')
        self.assertIn('https://app.example.test',mail.outbox[0].body)
        self.assertNotIn('attacker.example',mail.outbox[0].body)
        response=self.client.post(reverse('login'),{'username':user.username,'password':'Senha-Antiga!5863','next':'https://attacker.example/'})
        self.assertRedirects(response,'/')

    def test_rate_limit_and_csrf(self):
        data={'email':'missing@example.test'}
        self.assertEqual(self.client.post(reverse('password_reset'),data).status_code,302)
        self.assertEqual(self.client.post(reverse('password_reset'),data).status_code,429)
        secure=Client(enforce_csrf_checks=True)
        for path in (reverse('signup'),reverse('login'),reverse('password_reset'),reverse('resend_confirmation')):
            self.assertEqual(secure.post(path,{}).status_code,403)
        user=self.pending()
        self.assertEqual(secure.post(self.activation_url(user),{}).status_code,403)

    def test_existing_active_accounts_remain_usable(self):
        user=User.objects.create_user('legado',password='senha-de-teste')
        response=self.client.post(reverse('login'),{'username':user.username,'password':'senha-de-teste'})
        self.assertRedirects(response,'/')
        self.assertFalse(AccountEmail.objects.filter(user=user).exists())
