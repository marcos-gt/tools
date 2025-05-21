from django.contrib import admin
from chat.models import Chat
from output.models import Output
from categoria.models import Categoria
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import User
from django import forms

admin.site.register(Chat)
admin.site.register(Output)
admin.site.register(Categoria)