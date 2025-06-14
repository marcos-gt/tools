from selectors import SelectSelector
from django.shortcuts import get_object_or_404

from django.shortcuts import render
from django.http import JsonResponse
import ollama
from django.contrib.auth.decorators import login_required

from categoria.views import categoria
from chat.models import Chat
from categoria.models import Categoria
import pprint




@login_required
def index(request):
    if request.method == "POST":
        categoria_name = request.POST.get('generatorCategory')

        if not categoria_name:
            return JsonResponse({
                'error': 'Categoria é obrigatória'
            }, status=400)

        try:
            chats_exato = Chat.objects.filter(usuario=request.user, categoria__nome=categoria_name)
            chats_iexact = Chat.objects.filter(usuario=request.user, categoria__nome__iexact=categoria_name)
            chats_contains = Chat.objects.filter(usuario=request.user, categoria__nome__icontains=categoria_name)

            if chats_iexact.exists():
                chats = chats_iexact
            elif chats_contains.exists():
                chats = chats_contains
            else:
                chats = chats_exato

            if chats.exists():
                chats_texto = "\n".join([
                    f"- {chat.message}"
                    for chat in chats[:10]  # Limitar a 10 chats para não sobrecarregar
                ])

                categoria = chats.first().categoria
                categoria_nome = categoria.nome if categoria else "Categoria desconhecida"

            else:
                chats_texto = "Nenhuma conversa encontrada para esta categoria."
                categoria_nome = categoria_name


            response = ollama.chat(
                model="deepseek-r1:7b",
                messages=[
                    {"role": "user", "content": f'''
                    Crie um mapa mental usando APENAS a sintaxe Mermaid.
                    Responda SÓ com o código, sem explicações.

                    Use o formato:
                    flowchart TD
                        A["Tópico Central"] --> B["Subtópico 1"]
                        A --> C["Subtópico 2"]
                        B --> D["Detalhe 1"]
                        C --> E["Detalhe 2"]

                    Regras importantes:
                    - Use [ ] para tópicos normais
                    - Use {{ }} para decisões
                    - Use ( ) para processos
                    - Use | | para comentários nas setas
                    - Mantenha em português                
                    - Utilize quebras de linha para organizar o código
                    
                    Categoria: {categoria_nome}
                    Conversas: {chats_texto}

                    Crie um mapa mental organizado e criativo sobre este tema.
                    '''},
                ],
            )

            print(f'Response recebida: {response["message"]["content"][:200]}...')

            # MUDANÇA: Retornar 'output' em vez de 'response'
            mermaid_content = response["message"]["content"].split("</think>", 1)[-1].strip().replace("```mermaid ", "").replace("```", "").strip()

            return JsonResponse({
                'output': mermaid_content,
                'categoria': categoria_nome,
                'total_chats': chats.count()
            })

        except Exception as e:
            print(f"Erro completo: {str(e)}")
            print(f"Tipo do erro: {type(e)}")
            import traceback
            traceback.print_exc()

            return JsonResponse({
                'error': f'Erro interno: {str(e)}'
            }, status=500)

    # Quando for GET, cai aqui:
    categorias = Categoria.objects.filter(ativa=True).order_by('nome')
    chats = Chat.objects.filter(usuario=request.user).order_by('-timestamp')
    qtd_chats = chats.count()

    chats_lista = [
        {
            "id": chat.id,
            "message": chat.message,
            "timestamp": chat.timestamp.isoformat(),
            "category": chat.categoria.nome.upper() if chat.categoria else "",
            # adicione outros campos se precisar
        }
        for chat in chats
    ]

    categorias_lista = [
        {
            "id": cat.id,
            "nome": cat.nome.upper(),
            "descricao": cat.descricao,
            "data_criacao": cat.data_criacao.isoformat(),
            "ativa": cat.ativa,
        }
        for cat in categorias
    ]

    return render(request, 'index.html', {
        'chats': chats_lista,
        'categorias': categorias_lista,
        'qtd': qtd_chats
    })

