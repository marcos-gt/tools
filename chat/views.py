from django.shortcuts import render

# Create your views here.
def chat(request):
    print("Renderizando chat.html")
    return render(request, 'chat.html')