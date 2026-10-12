from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm, PasswordResetForm
from .models import AccountEmail
from .mail import send_templated_email


def style_fields(form):
    for field in form.fields.values():
        field.widget.attrs['class'] = 'form-input'


class LoginForm(AuthenticationForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['username'].widget.attrs.update(id='username', placeholder='Seu nome de usuário', autocomplete='username')
        self.fields['password'].widget.attrs.update(id='password', placeholder='Sua senha', autocomplete='current-password')


class SignupForm(UserCreationForm):
    email = forms.EmailField(label='Email', max_length=254)
    first_name = forms.CharField(label='Nome', max_length=150)

    class Meta(UserCreationForm.Meta):
        model = get_user_model()
        fields = ('first_name', 'username', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['first_name'].widget.attrs.update(autocomplete='given-name', placeholder='Como podemos chamar você?')
        self.fields['username'].widget.attrs.update(autocomplete='username', placeholder='Escolha um nome de usuário')
        self.fields['email'].widget.attrs.update(autocomplete='email', placeholder='voce@exemplo.com')
        for name in ('password1', 'password2'):
            self.fields[name].widget.attrs['autocomplete'] = 'new-password'
        self.fields['username'].help_text = 'Até 150 caracteres. Letras, números e @/./+/-/_.'
        self.fields['password1'].help_text = 'Use pelo menos 8 caracteres e evite senhas comuns ou semelhantes ao seu nome.'
        self.fields['password2'].help_text = ''

    def clean_email(self):
        email = self.cleaned_data['email'].strip().casefold()
        if get_user_model().objects.filter(email__iexact=email).exists() or AccountEmail.objects.filter(email=email).exists():
            raise forms.ValidationError('Este email já possui um cadastro. Entre ou reenvie a confirmação.')
        return email


class EmailForm(forms.Form):
    email = forms.EmailField(label='Email', max_length=254, widget=forms.EmailInput(attrs={
        'class':'form-input', 'autocomplete':'email', 'placeholder':'Email usado no cadastro'}))


class RecoveryForm(PasswordResetForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        style_fields(self)
        self.fields['email'].widget.attrs.update(autocomplete='email', placeholder='Email usado no cadastro')

    def send_mail(self, subject_template_name, email_template_name, context, from_email, to_email, html_email_template_name=None):
        send_templated_email(subject_template_name, email_template_name, html_email_template_name,
                             context, to_email, from_email=from_email)
