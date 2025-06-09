from django.contrib import admin
from chat.models import Chat
from output.models import Output
from categoria.models import Categoria
from sugestao.models import Sugestao

admin.site.register(Chat)
admin.site.register(Output)
admin.site.register(Categoria)
admin.site.register(Sugestao)
admin.site.site_header = "Administração do Web"
admin.site.site_title = "Painel de Administração do Web"
admin.site.index_title = "Bem-vindo ao Painel de Administração do Web"
