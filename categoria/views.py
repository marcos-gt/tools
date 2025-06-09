from django.shortcuts import render
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
    """
    Render the categoria page.
    """
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
    if request.method == 'POST':
        categorias = request.POST.getlist('categorias[]')
        if not categorias:
            return JsonResponse({'error': 'No categories provided'}, status=400)

        criadas = []
        for nome in categorias:
            cat, created = Categoria.objects.get_or_create(nome=nome)
            if created:
                criadas.append(nome)

        return JsonResponse({
            'message': 'Categorias salvas com sucesso!',
            'criadas': criadas,
            'todas': categorias
        })

    return JsonResponse({'error': 'Invalid request method'}, status=405)
