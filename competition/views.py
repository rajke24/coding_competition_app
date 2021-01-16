from django.shortcuts import render

# Create your views here.
def configpanel(request):
    return render(request, 'competition/configpanel.html')