from django.shortcuts import render, redirect
from .forms import ConfigPanelForm
from .models import Configuration


def configpanel(request):
    configuration = Configuration.objects.all()[0]
    if request.method == 'POST':
        form = ConfigPanelForm(request.POST)
        if form.is_valid():
            competition_status = form.cleaned_data['competition_status']
            ranking_visibility = form.cleaned_data['ranking_visibility'] 
            print(competition_status)
            print(ranking_visibility)
            configuration = Configuration.objects.all()[0]
            configuration.competition_status = competition_status
            configuration.ranking_visibility = ranking_visibility
            configuration.save()
            return redirect('config-panel')
    else:
        form = ConfigPanelForm()

    return render(request, 'competition/configpanel.html', {"configuration": configuration})
