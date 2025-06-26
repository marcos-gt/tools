from django.shortcuts import render
import json
from django.http import JsonResponse
from categoria.models import Categoria
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from chat.models import Chat


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
    categorias = Categoria.objects.all().order_by('nome').filter(ativa=True)
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

@login_required
@csrf_exempt
def inativar_categoria(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            category_name = data.get('category')
            category_id = data.get('category_id')
            
            print("Dados recebidos para inativar categoria:", data)
            
            if not category_name and not category_id:
                return JsonResponse({'error': 'Nome ou ID da categoria é obrigatório'}, status=400)

            # Buscar a categoria por ID ou nome
            try:
                if category_id and category_id.isdigit():
                    categoria = Categoria.objects.get(id=int(category_id), ativa=True)
                elif category_name:
                    categoria = Categoria.objects.get(nome__iexact=category_name, ativa=True)
                else:
                    # Se category_id não for numérico, tratar como nome
                    categoria = Categoria.objects.get(nome__iexact=category_id, ativa=True)
                    
            except Categoria.DoesNotExist:
                return JsonResponse({'error': 'Categoria não encontrada ou já está inativa'}, status=404)

            # Contar quantos chats serão afetados
            from chat.models import Chat
            chats_count = Chat.objects.filter(categoria=categoria, ativo=True).count()

            # Inativar a categoria
            categoria.ativa = False
            categoria.save()
            
            print(f"{chats_count} chats afetados para a categoria: {categoria.nome}")
            
            return JsonResponse({
                'success': True,
                'message': f'Categoria "{categoria.nome}" foi inativada com sucesso',
                'chats_count': chats_count
            })

        except Exception as e:
            print(f"Erro ao inativar categoria: {str(e)}")
            return JsonResponse({'error': str(e)}, status=500)

    return JsonResponse({'error': 'Método não permitido'}, status=405)