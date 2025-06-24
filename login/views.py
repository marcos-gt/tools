from django.shortcuts import render
from django.contrib.auth import logout as django_logout
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import redirect


# Create your views here.
def login(request):
    return render(request, 'registration\login.html')


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
