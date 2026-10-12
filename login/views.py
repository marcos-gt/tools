from django.views.decorators.csrf import ensure_csrf_cookie
from django.shortcuts import render
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect
import logging
from smtplib import SMTPException
from urllib.parse import urlparse
from django.conf import settings
from django.contrib.auth import login as session_login, get_user_model
from django.contrib.auth import views as auth_views
from django.db import transaction, IntegrityError
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode, url_has_allowed_host_and_scheme
from django.views.decorators.debug import sensitive_post_parameters
from .forms import LoginForm, SignupForm, RecoveryForm, EmailForm
from .models import AccountEmail
from .mail import ensure_email_configured, send_activation_email, send_welcome_email, EmailUnavailable
from .tokens import activation_token
from .limits import allow_email_request

logger = logging.getLogger(__name__)
MAIL_ERRORS = (EmailUnavailable, SMTPException, OSError)
EMAIL_FAILURE = 'Não foi possível enviar o email neste momento. Tente novamente mais tarde.'
RATE_FAILURE = 'Muitas solicitações. Aguarde um pouco antes de tentar novamente.'


# Create your views here.
@ensure_csrf_cookie
@sensitive_post_parameters('password')
def login(request):
    if request.user.is_authenticated:
        return redirect('/')
    form = LoginForm(request, data=request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        session_login(request, form.get_user())
        target = request.POST.get('next', '/')
        if not url_has_allowed_host_and_scheme(target, {request.get_host()}, require_https=request.is_secure()):
            target = '/'
        return redirect(target)
    return render(request, 'registration/login.html', {'form':form, 'next':request.GET.get('next', '/')})


@sensitive_post_parameters('password1', 'password2')
def signup(request):
    if request.user.is_authenticated:
        return redirect('/')
    form = SignupForm(request.POST if request.method == 'POST' else None)
    status = 200
    if request.method == 'POST' and form.is_valid():
        try:
            ensure_email_configured()
            if not allow_email_request(request, 'signup', form.cleaned_data['email']):
                form.add_error(None, RATE_FAILURE)
                return render(request, 'registration/signup.html', {'form':form}, status=429)
            with transaction.atomic():
                user = form.save(commit=False)
                user.is_active = False
                user.save()
                AccountEmail.objects.create(user=user, email=user.email)
                send_activation_email(user)
        except MAIL_ERRORS:
            logger.warning('auth_email_failed action=signup')
            form.add_error(None, EMAIL_FAILURE + ' O cadastro não foi concluído.')
            status = 503
        except IntegrityError:
            form.add_error(None, 'Já existe um cadastro com esse usuário ou email.')
        else:
            return redirect('signup_done')
    return render(request, 'registration/signup.html', {'form':form}, status=status)


def signup_done(request):
    return render(request, 'registration/signup_done.html')


def pending_user(uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        if not uid.isdigit() or int(uid) > 2147483647:
            return None
        user = get_user_model().objects.filter(pk=uid, is_active=False,
            account_email__verified_at__isnull=True, account_email__isnull=False).first()
        if user and user.account_email.email == user.email.casefold() and activation_token.check_token(user, token):
            return user
    except (ValueError, TypeError, OverflowError, UnicodeError):
        pass
    return None


def activate_account(request, uidb64, token):
    user = pending_user(uidb64, token)
    if request.method == 'POST' and user:
        with transaction.atomic():
            user = get_user_model().objects.select_for_update().get(pk=user.pk)
            identity = AccountEmail.objects.select_for_update().get(user=user)
            if user.is_active or identity.verified_at or not activation_token.check_token(user, token):
                return render(request, 'registration/activate.html', {'validlink':False})
            user.is_active = True
            user.save(update_fields=['is_active'])
            identity.verified_at = timezone.now()
            identity.save(update_fields=['verified_at'])
        try:
            send_welcome_email(user)
        except MAIL_ERRORS:
            logger.warning('auth_email_failed action=welcome user_id=%s', user.pk)
        return redirect('activation_done')
    return render(request, 'registration/activate.html', {'validlink':bool(user)})


def activation_done(request):
    return render(request, 'registration/activation_done.html')


def resend_confirmation(request):
    form = EmailForm(request.POST if request.method == 'POST' else None)
    if request.method == 'POST' and form.is_valid():
        try:
            ensure_email_configured()
        except MAIL_ERRORS:
            form.add_error(None, EMAIL_FAILURE)
            return render(request, 'registration/resend.html', {'form':form}, status=503)
        email = form.cleaned_data['email'].casefold()
        if not allow_email_request(request, 'resend', email):
            form.add_error(None, RATE_FAILURE)
            return render(request, 'registration/resend.html', {'form':form}, status=429)
        user = get_user_model().objects.filter(email__iexact=email, is_active=False,
            account_email__verified_at__isnull=True, account_email__isnull=False).first()
        if user:
            try:
                send_activation_email(user)
            except MAIL_ERRORS:
                logger.warning('auth_email_failed action=resend')
        return redirect('resend_done')
    return render(request, 'registration/resend.html', {'form':form})


def resend_done(request):
    return render(request, 'registration/resend_done.html')


class RecoveryView(auth_views.PasswordResetView):
    template_name = 'registration/password_reset_form.html'
    form_class = RecoveryForm
    email_template_name = 'registration/email/reset.txt'
    html_email_template_name = 'registration/email/reset.html'
    subject_template_name = 'registration/email/reset_subject.txt'
    success_url = reverse_lazy('password_reset_done')

    def form_valid(self, form):
        try:
            ensure_email_configured()
        except MAIL_ERRORS:
            form.add_error(None, EMAIL_FAILURE)
            return self.render_to_response(self.get_context_data(form=form), status=503)
        if not allow_email_request(self.request, 'recovery', form.cleaned_data['email']):
            form.add_error(None, RATE_FAILURE)
            return self.render_to_response(self.get_context_data(form=form), status=429)
        origin = urlparse(settings.PUBLIC_SITE_URL)
        try:
            form.save(domain_override=origin.netloc, use_https=origin.scheme == 'https',
                token_generator=self.token_generator, from_email=settings.DEFAULT_FROM_EMAIL,
                email_template_name=self.email_template_name,
                subject_template_name=self.subject_template_name,
                request=self.request, html_email_template_name=self.html_email_template_name,
                extra_email_context={'site_name':settings.SITE_NAME})
        except MAIL_ERRORS:
            # Não distingue conta existente de desconhecida quando o SMTP falha.
            logger.warning('auth_email_failed action=recovery')
        return redirect(self.success_url)

@login_required
def logout_view(request):
    if request.method == 'POST':
        # Logout seguro - invalida sessão no servidor
        django_logout(request)

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Logout realizado com sucesso'
            })

        # Redirect para requisições normais
        return redirect('login')

    return JsonResponse({'error': 'Método não permitido'}, status=405)
