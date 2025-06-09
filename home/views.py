from selectors import SelectSelector

from django.shortcuts import render
from django.http import JsonResponse
import ollama
from django.contrib.auth.decorators import login_required
from chat.models import Chat
from categoria.models import Categoria



@login_required
def index(request):
    if request.method == "POST":
        user_input = request.POST.get('prompt', '')
        try:
            response = ollama.chat(
                model="deepseek-r1:7b",
                messages=[
                    {"role": "user", "content": '''
                    "Sempre que eu pedir um fluxograma, 
                    responda usando a sintaxe do Mermaid (como no exemplo abaixo), 
                    formatado em código markdown com 
                    ```mermaid. Inclua um título descritivo e explique os passos opcionalmente, se sempre em português. 
                    Exemplo:  ```mermaid flowchart TD     A["Start"] --> B["Step 1"]     B --> C["Step 2"]     C --> D[End]. 
                    ''' + user_input},
                ],
            )
            return JsonResponse({
                'response': response["message"]["content"].split("</think>", 1)[-1].strip()
            })
        except Exception as e:
            return JsonResponse({
                'error': str(e)
            }, status=500)
    # Quando for GET, cai aqui:
    categorias = Categoria.objects.filter(ativa=True).order_by('nome')
    chats = Chat.objects.filter(usuario=request.user).order_by('-timestamp')
    qtd_chats = chats.count()
    return render(request, 'index.html', {'chats': chats,'categorias': categorias,'qtd': qtd_chats})

