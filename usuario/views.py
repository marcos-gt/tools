from django.shortcuts import render,redirect

from usuario.models import Usuario


# Create your views here.
def home(request):
    users = Usuario.objects.all()
    return render(request, 'usuario/user.html', {'users': users})

def user_create(request):
    if request.method == 'POST':
        nome = request.POST.get('nome')
        email = request.POST.get('email')
        telefone = request.POST.get('telefone')  # supondo que exista
        senha = request.POST.get('senha')

        Usuario.objects.create(nome=nome, email=email, telefone=telefone, senha=senha)
        return redirect('home')  # redireciona para a listagem após salvar

    return render(request, 'usuario/user_form.html')