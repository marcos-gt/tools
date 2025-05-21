from django.shortcuts import render

# Create your views here.
def sugestao(request):
    return render(request, 'sugestao.html')
