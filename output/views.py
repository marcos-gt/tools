from django.shortcuts import render

# Create your views here.
def output(request):
    return render(request, 'output.html')