from django.shortcuts import render
import json
from django.http import JsonResponse
from categoria.models import Categoria

def categoria(request):
    # if not request.user.is_authenticated:
    #     return JsonResponse({'error': 'Usuário não autenticado'}, status=401)

    categorias = Categoria.objects.filter(ativa=True).order_by('nome')
    data = [
       {
           'id': categoria.id,
           'nome': categoria.nome,
           'descricao': categoria.descricao,
           'data_criacao': categoria.data_criacao.isoformat(),
           'ativa': categoria.ativa,
       }
       for categoria in categorias
    ]
    return JsonResponse({'categorias': data})

def renderizar(request):
    return render(request, 'categoria.html')
def list_all(request):
    """
    List all categories.
    """
    categorias = Categoria.objects.all().order_by('nome')
    data = [
        {
            'nome': categoria.nome,
         }
        for categoria in categorias
    ]
    return JsonResponse({'categorias': data})

def receberCategorias(request):
    # printa no terminal
    print("Dados recebidos:", request.body)
    if request.method == 'POST':
        # Detecta JSON
        try:
            data = json.loads(request.body)
        except Exception:
            return JsonResponse({'error': 'JSON inválido'}, status=400)


        nomes = []
        if 'categorias' in data:
            nomes = data['categorias']
        elif 'nome' in data:
            nomes = [data['nome']]
        else:
            return JsonResponse({'error': 'Nenhum nome ou categorias enviados'}, status=400)

        criadas = []
        for nome in nomes:
            cat, created = Categoria.objects.get_or_create(nome=nome)
            if created:
                criadas.append(nome)

        return JsonResponse({'message': 'Categorias salvas com sucesso!', 'criadas': criadas, 'todas': nomes})

    return JsonResponse({'error': 'Invalid request method'}, status=405)

